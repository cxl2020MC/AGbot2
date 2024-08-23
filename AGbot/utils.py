import aiohttp
import asyncio
import traceback
import functools
from pathlib import Path
import time
from .log import logger as log
from . import config


def set_ws(websocket: aiohttp.ClientWebSocketResponse):
    global ws
    ws = websocket

def get_ws() -> aiohttp.ClientWebSocketResponse:
    return ws

def 重试(重试次数: int, 重试间隔: int = 1, 异常类型 = Exception, 错误处理函数 = None):
    def directer(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for i in range(重试次数):
                try:
                    return await func(*args, **kwargs)
                except 异常类型 as e:
                    log.error(f"发生错误, : {traceback.format_exc()}")
                    log.info(f"将在 {重试间隔} 秒后重试第 {i+1} 次")
                    if 错误处理函数:
                        错误处理函数(e)
                    await asyncio.sleep(重试间隔)
        return wrapper
    return directer


def 储存错误追踪():
    path = Path(config.数据文件夹)
    path = path / "错误追踪" / f"{time.time()}.json"
    path.touch()
    with open(path, "w", encodeing="utf-8") as f:
        pass