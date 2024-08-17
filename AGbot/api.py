from networkx import group_in_degree_centrality
from .log import logger as log
import time

群信息缓存 = {}


async def 获取群信息(ws, group_id):
    """
    获取群信息
    """
    群信息 = 群信息缓存.get(group_id, {})
    if not 群信息:
        await 刷新群信息缓存(ws, group_id)
    return 群信息


async def 刷新群信息缓存(ws, group_id):
    data = {"action": "get_group_info", "params": {"group_id": group_id},
            "echo": {"type": "get_group_info", "group_id": group_id}}
    await ws.send_json(data)

async def 删除群信息缓存(ws):
    群信息缓存.clear()


async def 获取群名称(ws, group_id):
    return (await 获取群信息(ws, group_id)).get("group_name", "群名称加载中")


async def 发送群消息(ws, group_id, message):
    data = {"action": "send_group_msg", "params": {"group_id": group_id,
                                                   "message": message}, "echo": {"type": "send_group_msg", "group_id": group_id}}
    await ws.send_json(data)


async def handler(ws, data):
    echo = data.get("echo")
    if echo.get("type") == "get_group_info":
        群信息缓存.update({echo.get("group_id"): data.get("data")})



