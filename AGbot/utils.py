import aiofiles
import aiofiles.os
import asyncio
import traceback
import functools
from pathlib import Path
from datetime import datetime
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


async def get_data_path() -> Path:
    path = Path(config.data_dir)
    # path.mkdir(exist_ok=True, parents=True)
    await create_folder(path)
    
    return path

async def create_folder(path):
    await aiofiles.os.makedirs(path, exist_ok=True)
    return path
async def save_error_log(data, traceback):
    time = str(datetime.today())
    w_data = json.dumps({
        "data": data,
        "traceback": traceback,
        "time": time
    }, ensure_ascii=False, indent=4)
    path = await get_data_path()
    path = path / "错误追踪"
    # path.mkdir(exist_ok=True, parents=True)
    await create_folder(path)
    path = path / f"{time}.json"
    # path.touch()
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(w_data)
    log.info(f"错误追踪已储存至 {path}")
    return time


async def log_error(event: Event, error_type, error_object, * , send_message=True):
    exc = traceback.format_exc()
    log.error(f"发生错误 {error_type} 执行出错: {exc}")
    try:
        error_id = await save_error_log(event.data, exc)
    except Exception as e2:
        error_id = "错误追踪储存失败"
        exc = traceback.format_exc()
        log.error(f"储存错误追踪失败: {repr(e2)}\n{exc}")
    message = f"""发生错误:
    {error_type} 执行出错: {repr(error_object)}
error_id: {error_id}"""
    if send_message:
        await api.send_message(event, message)

