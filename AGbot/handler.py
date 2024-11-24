from .log import logger as log
from . import api
from . import plugin
from . import config


async def main(data: dict):
    if data.get("post_type") == "message" or data.get("post_type") == "message_sent":
        if data.get("message_type") == "group":
            if data.get("sub_type") == "normal":
                await 群聊消息处理(data)
        elif data.get("message_type") == "private":
            if data.get("sub_type") == "friend":
                sender: dict = data.get("sender", {})
                log.info(
                    f"收到私聊消息: {sender.get('nickname')}({sender.get('user_id')}) 的消息: {data.get('raw_message')} [{data.get('message_id')}]")
    elif data.get("post_type") == "notice":
        log.info(f"收到通知: {data.get('notice_type')}")
    elif data.get("post_type") == "meta_event":
        if data.get("meta_event_type") == "lifecycle":
            log.info(f"收到生命周期事件: {data.get('sub_type')}")
        elif data.get("meta_event_type") == "heartbeat":
            log.info(f"收到心跳包: {data.get('status')} [{data.get('interval')}]")
    elif not "post_type" in data:
        await api.handler(data)
    else:
        log.warning(f"收到不支持的内容: {data}")


def get_uername(sender: dict) -> str:
    if sender.get("card"):
        return sender.get("card", "")
    else:
        return sender.get("nickname", "")


async def 群聊消息处理(data: dict):
    sender = data.get("sender", {})
    log.info(f"收到群 {await api.获取群名称(data.get('group_id'))}({data.get('group_id')}) 内 {get_uername(sender)}({sender.get('user_id')}) 的消息: {data.get('raw_message')} [{data.get('message_id')}]")
    if data.get("group_id") in config.群聊白名单:
        await plugin.bot.匹配命令(data)
