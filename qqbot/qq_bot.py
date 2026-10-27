import asyncio
from typing import ClassVar

import yarl

from . import handle, http_client, plugin
from .log import logger as log
from .qq_api import QQ_Api
from .types import qq_event, ws_data

API_HOST = yarl.URL("https://api.bot.qq.com")


class QQ_Bot:
    bot_list: ClassVar[list] = []

    def __init__(self):
        self.access_token = None
        self.access_token_expires_in: int = 0
        self.qq_api = QQ_Api(self)
        self._getway: str | None = None
        self._http_headers = {}
        self._ws: http_client.AsyncWebSocketSession | None = None
        self._heartbeat_task: asyncio.Task | None = None
        self._latest_s: int | None = None

        self.plugin_manager = plugin.PluginManager()

        self.bot_list.append(self)

    async def post_qqbot_api(self, api_path: str, json: dict):
        resp = await http_client.post(
            API_HOST / api_path, json=json, headers=self._http_headers
        )
        resp.raise_for_status()
        res = resp.json()
        log.debug(f"API 返回: {res}")
        return res

    async def get_qqbot_api(self, api_path: str):
        resp = await http_client.get(API_HOST / api_path, headers=self._http_headers)
        res = resp.json()
        log.debug(f"API 返回: {res}")
        return res

    async def get_access_token(self, app_id, client_secret):
        log.info("获取 access_token")
        data = {
            "appId": app_id,
            "clientSecret": client_secret,
        }
        res = await self.post_qqbot_api("app/getAppAccessToken", data)
        self.access_token = res["access_token"]
        self.access_token_expires_in = res["expires_in"]

        self._http_headers = {"Authorization": f"QQBot {self.access_token}"}

    async def get_getway(self):
        res = await self.get_qqbot_api("gateway")
        self._getway = res.get("url")

    async def ws_send_json(self, data: ws_data.WsData):
        if self._ws:
            await self._ws.send_json(data.model_dump())

    async def _connect_ws(self):
        if not self._getway:
            return
        log.info(f"连接 WebSocket: {self._getway}")
        async with http_client.client.websocket(self._getway) as ws:
            self._ws = ws

            data = ws_data.WsData(
                op=ws_data.OpType.IDENTIFY,
                d={
                    "token": f"QQBot {self.access_token}",
                    "intents": 0 | 1 << 0 | 1 << 1 | 1 << 12 | 1 << 9 | 1 << 25,
                    "shard": [0, 1],
                    "properties": {},
                },
            )
            await self.ws_send_json(data)
            while True:
                data = await ws.receive_json()
                log.debug(f"收到 WebSocket 消息: {data}")
                websocket_data = ws_data.WsData.model_validate(data)
                log.debug(f"解析后的 WebSocket 数据: {websocket_data}")
                latest_s = websocket_data.s
                if latest_s:
                    self._latest_s = latest_s
                match websocket_data.op:
                    case ws_data.OpType.HELLO:
                        data = websocket_data.d
                        if data and "heartbeat_interval" in data:
                            log.debug(
                                f"收到心跳间隔: {data['heartbeat_interval']}ms, 开始发送心跳"
                            )
                            if self._heartbeat_task:
                                log.debug("取消之前的心跳任务")
                                self._heartbeat_task.cancel()
                            self._heartbeat_task = asyncio.create_task(
                                self.keep_heartbeat(data["heartbeat_interval"])
                            )
                    case ws_data.OpType.RECONNECT:
                        log.debug("收到重连请求，重新连接 WebSocket")
                        raise QQ_BOT_WEBSOCKET_RECONNECT(
                            "收到重连请求，重新连接 WebSocket"
                        )
                    case ws_data.OpType.DISPATCH:
                        log.debug(
                            f"收到事件: {websocket_data.t}, 数据: {websocket_data.d}"
                        )
                        if websocket_data.t in qq_event.QQEventType:
                            # 触发事件
                            event_type = qq_event.QQEventType(websocket_data.t)
                            await handle.handle_event(
                                event_type, websocket_data.d, self
                            )

    async def connect_ws(self):
        while True:
            try:
                await self._connect_ws()
            except* QQ_BOT_WEBSOCKET_RECONNECT:
                log.debug("WebSocket 连接需要重新连接")
                # continue  # 重新连接 WebSocket
            # except Exception as e:
            #     log.error(f"WebSocket 连接异常: {e}, 正在尝试重新连接...")
            #     await asyncio.sleep(5)  # 等待一段时间后重连

    async def keep_heartbeat(self, heartbeat_interval):
        log.debug(f"开始发送心跳，间隔: {heartbeat_interval}ms")
        while True:
            if self._ws:
                heartbeat_data = ws_data.WsData(
                    op=ws_data.OpType.HEARTBEAT, d=self._latest_s
                )
                # await self._ws.send_json(heartbeat_data)
                await self.ws_send_json(heartbeat_data)
                log.debug(f"已发送心跳: {heartbeat_data}")
            await asyncio.sleep(heartbeat_interval / 1000)

    async def run(self, app_id, client_secret):
        log.info("启动 QQ_Bot")
        await self.get_access_token(app_id, client_secret)
        await self.get_getway()
        await self.connect_ws()


class QQ_BOT_WEBSOCKET_RECONNECT(Exception):
    """WebSocket 连接需要重新连接的异常。"""


if __name__ == "__main__":
    import asyncio

    from plugin import echo

    from .config import config

    async def main():
        qq = QQ_Bot()
        qq.plugin_manager.add_plugin(echo.plugin, qq)
        await qq.run(config.appId, config.clientSecret)

    asyncio.run(main())
