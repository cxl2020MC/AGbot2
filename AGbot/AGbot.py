import aiohttp
import asyncio
import traceback
from . import handler
from .log import logger as log
from . import utils
from . import plugin


class App:
    def __init__(self, ws_url: str = "ws://localhost:3001/") -> None:
        self.ws_url = ws_url
        self.插件列表 = []

    async def run(self) -> None:
        async def main(session: aiohttp.ClientSession):
            log.info(f"正在连接: {self.ws_url}")
            async with session.ws_connect(self.ws_url) as ws:
                log.info("连接成功")
                utils.set_ws(ws)
                async for msg in ws:
                    data = msg.json()
                    log.debug(f"收到json消息: {data}")
                    await handler.main(self, data, ws)

        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    await main(session)
                except:
                    log.error(traceback.format_exc())
                    log.error("连接断开, 将在3s后重连")
                    await asyncio.sleep(3)

            
    def 加载插件(self, 蓝图: plugin.plugin) -> None: 
        self.插件列表.append(蓝图)

