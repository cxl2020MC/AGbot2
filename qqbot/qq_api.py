from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .qq_bot import QQ_Bot


class QQ_Api:
    def __init__(self, QQ_BOT: QQ_Bot):
        self.QQ_BOT = QQ_BOT

    async def send_group_message(self, group_openid: str, message: dict):
        data = {}

        return await self.QQ_BOT.post_qqbot_api(
            f"v2/groups/{group_openid}/messages", json=message
        )
