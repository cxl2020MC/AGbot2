import aiofiles
import aiofiles.os
import asyncio
import traceback
import functools
# from pathlib import Path
from anyio import Path
from datetime import datetime
import json


from .types.message_event import Event
from .log import logger as log
from . import config
from . import api


def retry(max_retries: int, retry_interval: int = 1, exception_type=Exception, error_handler=None):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exception_type as e:
                    exc = traceback.format_exc()
                    log.error(f"发生错误, : {exc}")
                    log.info(f"将在 {retry_interval} 秒后重试第 {i+1} 次")
                    if error_handler:
                        error_handler(e)
                    await asyncio.sleep(retry_interval)
        return wrapper
    return decorator


async def get_data_path() -> Path:
    path = Path(config.DATA_DIR)
    # path.mkdir(exist_ok=True, parents=True)
    await create_folder(path)

    return path


async def create_folder(path: Path):
    # await aiofiles.os.makedirs(path, exist_ok=True)
    await path.mkdir(exist_ok=True, parents=True)
    return path


async def save_error_log(data: dict | None, traceback_str: str):
    time_str = str(datetime.today())
    w_data = json.dumps({
        "data": data,
        "traceback": traceback_str,
        "time": time_str
    }, ensure_ascii=False, indent=4)
    path = await get_data_path()
    path = path / "错误追踪"
    # path.mkdir(exist_ok=True, parents=True)
    await create_folder(path)
    path = path / f"{time_str}.json"
    # path.touch()
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(w_data)
    log.info(f"错误追踪已储存至 {path}")
    return time_str


def get_error_log_str(error_type):
    exc = traceback.format_exc()
    log.error(f"发生错误 {error_type} 执行出错: {exc}")
    return exc


async def log_error(event: Event, error_type, error_object, *, send_message=True):
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


async def log_error_v2(error_type, error_object, event: Event | None = None, *, send_message=True):
    exc = get_error_log_str(error_type)
    try:
        if event:
            event_data = event.data
        else:
            event_data = None
        error_id = await save_error_log(event_data, exc)
    except Exception as e2:
        error_id = "错误追踪储存失败"
        exc = traceback.format_exc()
        log.error(f"储存错误追踪失败: {repr(e2)}\n{exc}")
    message = f"""发生错误:
    {error_type} 执行出错: {repr(error_object)}
error_id: {error_id}"""
    if send_message and event:
        await api.send_message(event, message)
        await api.send_private_message(config.ADMIN_QQ, message)