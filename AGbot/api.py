from .log import logger as log
from . import config
import aiohttp

group_info_cache = {}


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


async def get_group_info(group_id):
    """
    获取群信息
    """
    group_info = group_info_cache.get(group_id)
    if not group_info:
        return await refresh_group_info_cache(group_id)
    return group_info


async def refresh_group_info_cache(group_id: int) -> dict:
    post_data = {
        "group_id": group_id,
    }
    data = await post_api("get_group_info", post_data)
    group_info_cache.update({group_id: data["data"]})
    return data["data"]


async def clear_group_info_cache():
    group_info_cache.clear()


async def get_group_name(group_id):
    return (await get_group_info(group_id)).get("group_name")


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
