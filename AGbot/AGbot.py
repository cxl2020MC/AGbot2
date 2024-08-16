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
        self.插件 = plugin.bot
    
    @utils.重试(重试次数=9999, 错误处理函数=None)
    async def run(self) -> None:
        async with aiohttp.ClientSession() as session:
            log.info(f"正在连接: {self.ws_url}")
            async with session.ws_connect(self.ws_url) as ws:
                log.info("连接成功")
                utils.set_ws(ws)
                async for msg in ws:
                    data = msg.json()
                    log.debug(f"收到json消息: {data}")
                    await handler.main(self, data, ws)