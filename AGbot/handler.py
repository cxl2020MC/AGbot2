from .log import logger as log
from . import api
from . import plugin
from . import config


async def main(data: dict):
    match data:
        case {"post_type": "message" | "message_sent", "message_type": "group", "sub_type": "normal"}:
            await 群聊消息处理(data)
        case {"post_type": "message" | "message_sent", "message_type": "private", "sub_type": "friend"}:
            await 私聊消息处理(data)
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


async def 群聊消息处理(data: dict):
    sender = data.get("sender", {})
    log.info(f"收到群 {await api.获取群名称(data.get('group_id'))}({data.get('group_id')}) 内 {get_username(sender)}({sender.get('user_id')}) 的消息: {data.get('raw_message')} [{data.get('message_id')}]")
    if data.get("group_id") in config.群聊白名单:
        await plugin.匹配命令(data)


async def 私聊消息处理(data: dict):
    sender = data.get("sender", {})
    log.info(
        f"收到私聊消息: {sender.get('nickname')}({sender.get('user_id')}) 的消息: {data.get('raw_message')} [{data.get('message_id')}]")
    await plugin.匹配命令(data)
