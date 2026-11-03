"""QQ 官方机器人客户端。"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any, ClassVar

import yarl

from . import handle, http_client, plugin
from .config import config
from .log import logger as log
from .qq_api import QQ_Api
from .types import ws_data
from .types.qq_events import qq_event

API_HOST = yarl.URL("https://api.bot.qq.com")

# 默认订阅的 intents 位掩码
DEFAULT_INTENTS = (
    (1 << 0)  # GUILDS
    | (1 << 1)  # GUILD_MEMBERS
    | (1 << 9)  # GUILD_MESSAGES
    | (1 << 12)  # DIRECT_MESSAGE
    | (1 << 25)  # GROUP_AND_C2C_EVENT
)

RECONNECT_DELAY_SECONDS = 5


class QQBotReconnect(Exception):
    """服务端要求重新建立 WebSocket 连接。"""


class QQ_Bot:
    """QQ 官方机器人客户端，负责鉴权、WebSocket 连接与事件分发。"""

    bot_list: ClassVar[list[QQ_Bot]] = []

    def __init__(self):
        self.access_token: str | None = None
        self.access_token_expires_in: int = 0

        self.qq_api = QQ_Api(self)
        self.plugin_manager = plugin.PluginManager(self)

        self._gateway: str | None = None
        self._session_id: str | None = None
        self._http_headers: dict[str, str] = {}
        self._ws: http_client.AsyncWebSocketSession | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._latest_s: int | None = None

        type(self).bot_list.append(self)

    # HTTP API

    async def _api_request(
        self, method: str, api_path: str, **kwargs: Any
    ) -> dict[str, Any]:
        requester = http_client.post if method == "POST" else http_client.get
        resp = await requester(
            API_HOST / api_path, headers=self._http_headers, **kwargs
        )
        resp.raise_for_status()
        res = resp.json()
        log.debug(f"API {api_path} 返回: {res}")
        return res

    async def post_qqbot_api(
        self, api_path: str, json: dict[str, Any]
    ) -> dict[str, Any]:
        return await self._api_request("POST", api_path, json=json)

    async def get_qqbot_api(self, api_path: str) -> dict[str, Any]:
        return await self._api_request("GET", api_path)

    # 鉴权与 Gateway

    async def fetch_access_token(
        self, app_id: str, client_secret: str
    ) -> dict[str, Any]:
        log.info("获取 access_token")
        res = await self.post_qqbot_api(
            "app/getAppAccessToken",
            {"appId": app_id, "clientSecret": client_secret},
        )
        self.access_token = res["access_token"]
        self.access_token_expires_in = res["expires_in"]
        self._http_headers = {"Authorization": f"QQBot {self.access_token}"}
        return res

    async def fetch_gateway(self) -> None:
        res = await self.get_qqbot_api("gateway")
        url = res.get("url")
        if not url:
            raise RuntimeError(f"获取 gateway 失败: {res}")
        self._gateway = url

    # WebSocket

    async def ws_send_json(self, data: ws_data.WsData) -> None:
        if self._ws is None:
            raise RuntimeError("WebSocket 未连接，无法发送数据")
        await self._ws.send_json(data.model_dump())

    async def _connect_ws(self) -> None:
        if not self._gateway:
            raise RuntimeError("尚未获取 gateway URL，请先调用 fetch_gateway()")

        log.info(f"连接 WebSocket: {self._gateway}")
        async with http_client.client.websocket(self._gateway) as ws:
            self._ws = ws
            while True:
                raw = await ws.receive_json()
                log.debug(f"收到 WebSocket 消息: {raw}")
                try:
                    message = ws_data.WsData.model_validate(raw)
                except Exception:  # noqa: BLE001
                    log.exception("解析 WebSocket 消息失败")
                    continue
                await self._handle_ws_message(message)

    async def connect_ws(self) -> None:
        """保持 WebSocket 连接，断线后自动重连。"""
        while True:
            try:
                await self._connect_ws()
            except QQBotReconnect:
                log.info("服务端要求重连，重新建立 WebSocket")
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                log.exception(f"WebSocket 连接异常，{RECONNECT_DELAY_SECONDS} 秒后重试")
            finally:
                await self._stop_heartbeat()
                self._ws = None
            await asyncio.sleep(RECONNECT_DELAY_SECONDS)

    async def _handle_ws_message(self, message: ws_data.WsData) -> None:
        if message.s is not None:
            self._latest_s = message.s
        try:
            await self.ws_message_handler(message)
        except QQBotReconnect:
            raise
        except Exception:  # noqa: BLE001
            log.exception("处理 WebSocket 消息时发生异常")

    async def ws_message_handler(self, message: ws_data.WsData) -> None:
        match message.op:
            case ws_data.OpType.HELLO:
                await self._on_hello(message.d)
            case ws_data.OpType.RECONNECT:
                raise QQBotReconnect("服务端要求重连")
            case ws_data.OpType.DISPATCH:
                await self._on_dispatch(message)
            case ws_data.OpType.Heartbeat_ACK:
                log.debug(f"收到心跳 ACK，seq={self._latest_s}")
            case _:
                log.debug(f"忽略未处理的 op: {message.op}")

    # 事件处理

    async def _on_hello(self, data: dict[str, Any] | None) -> None:
        if not data or "heartbeat_interval" not in data:
            log.warning("HELLO 消息缺少 heartbeat_interval")
            return

        interval_ms = int(data["heartbeat_interval"])
        log.debug(f"心跳间隔: {interval_ms}ms")

        await self._stop_heartbeat()
        await self._identify_or_resume()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(interval_ms))

    async def _identify_or_resume(self) -> None:
        token = f"QQBot {self.access_token}"
        if self._session_id and self._latest_s is not None:
            log.info(f"恢复会话 session_id={self._session_id} seq={self._latest_s}")
            payload = ws_data.WsData(
                op=ws_data.OpType.Resume,
                d={
                    "token": token,
                    "session_id": self._session_id,
                    "seq": self._latest_s,
                },
            )
        else:
            log.info("发送 IDENTIFY 建立新会话")
            payload = ws_data.WsData(
                op=ws_data.OpType.IDENTIFY,
                d={
                    "token": token,
                    "intents": DEFAULT_INTENTS,
                    "shard": [0, 1],
                    "properties": {},
                },
            )
        await self.ws_send_json(payload)

    async def _on_dispatch(self, message: ws_data.WsData) -> None:
        log.debug(f"收到事件: {message.t}, 数据: {message.d}")
        match message.t:
            case "READY":
                if isinstance(message.d, dict):
                    self._session_id = message.d.get("session_id")
                    log.info(f"会话就绪 session_id={self._session_id}")
            case "RESUMED":
                log.info("会话恢复成功")
            case "INVALID_SESSION":
                log.warning("会话无效，清除本地会话状态")
                self._session_id = None
                self._latest_s = None

        if not message.t:
            return
        try:
            event_type = qq_event.QQEventType(message.t)
        except ValueError:
            log.debug(f"忽略未知事件: {message.t}")
            return
        await handle.handle_event(event_type, message.d, self)

    # 心跳

    async def _heartbeat_loop(self, interval_ms: int) -> None:
        interval = interval_ms / 1000
        log.debug(f"开始发送心跳，间隔 {interval}s")
        try:
            while True:
                if self._ws is not None:
                    try:
                        await self.ws_send_json(
                            ws_data.WsData(
                                op=ws_data.OpType.HEARTBEAT, d=self._latest_s
                            )
                        )
                        log.debug(f"已发送心跳 seq={self._latest_s}")
                    except Exception:  # noqa: BLE001
                        log.exception("发送心跳失败，心跳任务退出")
                        return
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            log.debug("心跳任务已取消")
            raise

    async def _stop_heartbeat(self) -> None:
        task = self._heartbeat_task
        self._heartbeat_task = None
        if task is None or task.done():
            return
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    # 入口

    async def run(
        self,
        app_id: str = config.appId,
        client_secret: str = config.clientSecret,
    ) -> None:
        log.info("启动 QQ_Bot")
        await self.fetch_access_token(app_id, client_secret)
        await self.fetch_gateway()
        await self.connect_ws()


if __name__ == "__main__":
    from plugin import echo

    async def main() -> None:
        qq = QQ_Bot()
        qq.plugin_manager.add_plugin(echo.plugin)
        await qq.run()

    asyncio.run(main())
