from .log import logger as log
from . import websocket
import time

群信息缓存 = {}


async def 获取群信息(group_id):
    """
    获取群信息
    """
    群信息 = 群信息缓存.get(group_id, {})
    if not 群信息:
        await 刷新群信息缓存(group_id)
    return 群信息


async def 刷新群信息缓存(group_id):
    ws = await websocket.get_ws()
    data = {"action": "get_group_info", "params": {"group_id": group_id},
            "echo": {"type": "get_group_info", "group_id": group_id}}
    await ws.send_json(data)


async def 删除群信息缓存():
    群信息缓存.clear()


async def 获取群名称(group_id):
    return (await 获取群信息(group_id)).get("group_name", "群名称加载中")


async def send_group_message(group_id, message):
    ws = await websocket.get_ws()
    data = {"action": "send_group_msg", "params": {"group_id": group_id,
                                                   "message": message}, "echo": {"type": "send_group_msg", "group_id": group_id, "message": message}}
    await ws.send_json(data)

async def send_message(data, message):
    if data.get("group_id"):
        await send_group_message(data.get("group_id"), message)

async def handler(data):
    echo = data.get("echo")
    if echo.get("type") == "get_group_info":
        群信息缓存.update({echo.get("group_id"): data.get("data")})
    elif echo.get("type") == "send_group_msg":
        log.info(f"发送群消息成功，群号：{echo.get('group_id')}，消息：{echo.get('message')}")
