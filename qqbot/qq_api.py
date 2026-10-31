from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel

    from .qq_bot import QQ_Bot
    from .types.qq_api import send_message


def _from_model_to_json(model: BaseModel):
    return model.model_dump(exclude_none=True)


class QQ_Api:
    def __init__(self, QQ_BOT: QQ_Bot):
        self.QQ_BOT = QQ_BOT

    async def send_group_message(
        self, group_openid: str, message: send_message.GroupMessage
    ):
        data = _from_model_to_json(message)

        return await self.QQ_BOT.post_qqbot_api(
            f"v2/groups/{group_openid}/messages", json=data
        )
