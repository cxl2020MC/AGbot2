from .log import logger as log
from . import api

async def main(self, data: dict, ws):
    if data.get("post_type") == "message":
        if data.get("message_type") == "group":
            sender: dict = data.get("sender", {})
            log.info(f"收到群 {await api.获取群名称(ws, data.get('group_id'))}({data.get('group_id')}) 内 {get_uername(sender)}({sender.get('user_id')}) 的消息: {data.get('raw_message')} [{data.get('message_id')}]")
        elif data.get("message_type") == "private":
            sender: dict = data.get("sender", {})
            log.info(f"收到私聊消息: {sender.get('nickname')}({sender.get('user_id')}) 的消息: {data.get('raw_message')} [{data.get('message_id')}]")
    elif "echo" in data:
        await api.handler(ws, data)


def get_uername(sender: dict) -> str:
    if sender.get("card"):
        return sender.get("card", "")
    else:
        return sender.get("nickname", "")