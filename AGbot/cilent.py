import asyncio
import aiohttp
from .log import logger as log
from . import utils
from . import handler
from . import config


@utils.重试(重试次数=99999, 错误处理函数=None)
async def run() -> None:
    async with aiohttp.ClientSession() as session:
        ws_url = config.ws_url
        log.info(f"正在连接: {ws_url}")
        async with session.ws_connect(ws_url) as ws:
            log.info("连接成功")
            utils.set_ws(ws)
            async for msg in ws:
                data = msg.json()
                log.debug(f"收到json消息: {data}")
                await handler.main(data, ws)
