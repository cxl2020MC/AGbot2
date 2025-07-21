from .log import logger as log
from . import config
import aiohttp

群信息缓存 = {}


async def post_api(action, post_data) -> dict:
    async with aiohttp.ClientSession() as session:
        async with await session.post(f"{config.api_url}/{action}", json=post_data) as res:
            data = await res.json()
            log.debug(f"API {action} 返回: {data}")
            if data.get("status") == "ok":
                return data
            else:
                log.error(f"API {action} 返回错误 {data}")
                raise Exception(f"API {action} 返回错误 {data}")


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


async def send_group_message(group_id, message) -> dict:
    post_data = {
        "group_id": group_id,
        "message": message
    }
    log.info(f"向群聊 {group_id} 发送消息: {message}")
    return await post_api("send_group_msg", post_data)


async def send_private_message(user_id, message) -> dict:
    post_data = {
        "user_id": user_id,
        "message": message
    }
    log.info(f"向私聊 {user_id} 发送消息: {message}")
    return await post_api("send_private_msg", post_data)


async def send_message(event, message):
    if event.data.get("group_id"):
        return await send_group_message(event.data.get("group_id"), message)
    elif event.data.get("user_id"):
        return await send_private_message(event.data.get("user_id"), message)
