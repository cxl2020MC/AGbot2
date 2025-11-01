import asyncio
from .log import logger as log
from . import plugin
from . import config
from .types.message_event import GroupMessageEvent, PrivateMessageEvent


async def main(data: dict):
    match data:
        case {"post_type": "message" | "message_sent", "message_type": "group", "sub_type": "normal"}:
            await group_message_handler(data)
        case {"post_type": "message" | "message_sent", "message_type": "private", "sub_type": "friend"}:
            await private_message_handler(data)
        case {"post_type": "notice"}:
            log.info(f"收到通知: {data.get('notice_type')}")
        case {"post_type": "notice", "notice_type": "group_recall"}:
            log.info("群消息撤回")
            ...
        case {"post_type": "meta_event", "meta_event_type": "lifecycle"}:
            log.info(f"收到生命周期事件: {data.get('sub_type')}")
        case {"post_type": "meta_event", "meta_event_type": "heartbeat"}:
            log.info(f"收到心跳包: {data.get('status')} [{data.get('interval')}]")

        case _:
            log.warning(f"收到不支持的内容: {data}")


def get_username(sender: dict) -> str:
    return sender.get("card", "") or sender.get("nickname", "")


async def group_message_handler(data: dict):
    event = GroupMessageEvent(data)
    log.info(f"收到群 {await event.group_name}({event.group_id}) 内 {event.get_username()}({event.user_id}) 的消息: {event.raw_message} [{event.message_id}]")
    if event.group_id not in config.group_black_list:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(plugin.match_command(event))
            tg.create_task(plugin.match_event(event))


async def private_message_handler(data: dict):
    event = PrivateMessageEvent(data)
    log.info(
        f"收到私聊消息: {event.sender_nickname}({event.user_id}) 的消息: {event.raw_message} [{event.message_id}]")
    async with asyncio.TaskGroup() as tg:
        tg.create_task(plugin.match_command(event))
        tg.create_task(plugin.match_event(event))

