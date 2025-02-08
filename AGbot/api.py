from .log import logger as log
from . import config
import httpx

群信息缓存 = {}

client = httpx.AsyncClient()


async def post_api(action, post_data) -> dict:
    req = await client.post(f"{config.api_url}/{action}", json=post_data)
    data = req.json()
    log.debug(f"API {action} 返回: {data}")
    if data["status"] == "ok":
        return data
    else:
        raise Exception(data)


async def 获取群信息(group_id):
    """
    获取群信息
    """
    群信息 = 群信息缓存.get(group_id)
    if not 群信息:
        return await 刷新群信息缓存(group_id)
    return 群信息


async def 刷新群信息缓存(group_id: int):
    post_data = {
        "group_id": group_id,
    }
    data = await post_api("get_group_info", post_data)
    群信息缓存.update({group_id: data["data"]})
    return data["data"]


async def 删除群信息缓存():
    群信息缓存.clear()


async def 获取群名称(group_id):
    return (await 获取群信息(group_id)).get("group_name")


async def send_group_message(group_id, message):
    post_data = {
        "group_id": group_id,
        "message": message
    }
    await post_api("send_group_msg", post_data)


async def send_message(data, message):
    if data.get("group_id"):
        await send_group_message(data.get("group_id"), message)
