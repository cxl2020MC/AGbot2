import aiofiles
import asyncio
import traceback
import functools
from pathlib import Path
import time
import json

from AGbot.event import MessageEvent

from .log import logger as log
from . import config


def 重试(重试次数: int, 重试间隔: int = 1, 异常类型=Exception, 错误处理函数=None):
    def directer(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for i in range(重试次数):
                try:
                    return await func(*args, **kwargs)
                except 异常类型 as e:
                    exc = traceback.format_exc()
                    log.error(f"发生错误, : {exc}")
                    log.info(f"将在 {重试间隔} 秒后重试第 {i+1} 次")
                    if 错误处理函数:
                        错误处理函数(e)
                    await asyncio.sleep(重试间隔)
        return wrapper
    return directer


async def 储存错误追踪(data, traceback):
    timestamp = time.time()
    w_data = json.dumps({
        "data": data,
        "traceback": traceback,
    })
    path = Path(config.数据文件夹)
    path = path / "错误追踪"
    path.mkdir(exist_ok=True, parents=True)
    path = path / f"{timestamp}.json"
    # path.touch()
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(w_data)
    log.info(f"错误追踪已储存至 {path}")
    return timestamp


async def 错误处理(event: MessageEvent, error_type, error_object, tb):
    
    exc = traceback.format_exc()
    log.error(f"命令 {名称} 执行出错: {exc}")
    try:
        error_id = await 储存错误追踪(event.data, exc)
    except Exception as e2:
        error_id = None
        log.error(f"储存错误追踪失败: {e2}")
        await api.send_message(event, f"命令 {名称} 执行出错: {e.__class__.__name__}: {e}\nerror_id: {error_id}")