from .log import logger as log

async def main(self, data: dict, session):
    if data.get("post_type") == "message":
        if data.get("message_type") == "group":
            sender: dict = data.get("sender", {})
            log.info(f"收到群 ({data.get('group_id')}) 内 {get_uername(sender)}({sender.get('user_id')}) 的消息: {data.get('raw_message')} [{data.get('message_id')}]")
        elif data.get("message_type") == "private":
            pass
        


def get_uername(sender: dict) -> str:
    if sender.get("card"):
        return sender.get("card", "")
    else:
        return sender.get("nickname", "")