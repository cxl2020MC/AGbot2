import aiofiles
import asyncio
import traceback
import functools
from pathlib import Path
import time
import json

from .event import Event
from .log import logger as log
from . import config
from . import api


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
    }, ensure_ascii=False)
    path = Path(config.数据文件夹)
    path = path / "错误追踪"
    path.mkdir(exist_ok=True, parents=True)
    path = path / f"{timestamp}.json"
    # path.touch()
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(w_data)
    log.info(f"错误追踪已储存至 {path}")
    return timestamp


async def 错误处理(event: Event, error_type, error_object):
    exc = traceback.format_exc()
    log.error(f"发生错误 {error_type} 执行出错: {exc}")
    try:
        error_id = await 储存错误追踪(event.data, exc)
    except Exception as e2:
        error_id = None
        log.error(f"储存错误追踪失败: {repr(e2)}")
    message = f"""发生错误:
    {error_type} 执行出错: {repr(error_object)}
    error_id: {error_id}"""
    await api.send_message(event, message)