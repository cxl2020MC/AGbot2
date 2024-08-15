from .log import logger as log
from . import api

async def main(self, data: dict, ws):
    if data.get("post_type") == "message" or data.get("post_type") == "message_sent":
        if data.get("message_type") == "group":
            await 群聊消息处理(self, data, ws)
        elif data.get("message_type") == "private":
            sender: dict = data.get("sender", {})
            log.info(f"收到私聊消息: {sender.get('nickname')}({sender.get('user_id')}) 的消息: {data.get('raw_message')} [{data.get('message_id')}]")
    elif data.get("post_type") == "notice":
        log.info(f"收到通知: {data.get('notice_type')}")
    elif data.get("post_type") == "meta_event":
        if data.get("meta_event_type") == "lifecycle":
            log.info(f"收到生命周期事件: {data.get('sub_type')}")
        elif data.get("meta_event_type") == "heartbeat":
            log.info(f"收到心跳包: {data.get('status')} [{data.get('interval')}]")
    elif "retcode" in data:
        await api.handler(ws, data)
    else:
        log.warning(f"收到不支持的内容: {data}")


def get_uername(sender: dict) -> str:
    if sender.get("card"):
        return sender.get("card", "")
    else:
        return sender.get("nickname", "")
    
async def 群聊消息处理(self, data: dict, ws):
    sender: dict = data.get("sender", {})
    log.info(f"收到群 {await api.获取群名称(ws, data.get('group_id'))}({data.get('group_id')}) 内 {get_uername(sender)}({sender.get('user_id')}) 的消息: {data.get('raw_message')} [{data.get('message_id')}]")
    for 插件 in self.插件列表:
        for 命令列表 in 插件.命令列表:
            for 命令 in 命令列表:
                for 命令 in 命令:
                    log.debug(f"当前检测命令： {命令}")
                    if data.get("raw_message", "").startswith(命令):
                        await 命令.get("函数")(self, data, ws)