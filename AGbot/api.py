from .log import logger as log
import time

群信息缓存 = {}

async def 获取群信息(ws, group_id):
    """
    获取群信息
    """
    await 刷新群信息缓存(ws, group_id)
    return 群信息缓存.get(group_id, {})

async def 刷新群信息缓存(ws, group_id):
    data = {"action": "get_group_info", "params": {"group_id": group_id}, "echo": {"type"}}
    await ws.send_json(data)

async def 获取群名称(ws, group_id):
    return (await 获取群信息(ws, group_id)).get("group_name", "群名称加载中")