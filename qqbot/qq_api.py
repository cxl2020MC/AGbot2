from typing import TYPE_CHECKING
from .types.qq_api import group_info

if TYPE_CHECKING:
    from pydantic import BaseModel

    from .qq_bot import QQ_Bot
    from .types.qq_api import send_message


def _from_model_to_json(model: BaseModel):
    return model.model_dump(exclude_none=True)


class QQ_Api:
    def __init__(self, QQ_BOT: QQ_Bot):
        self.QQ_BOT = QQ_BOT
        self._group_info_cache: dict[str, group_info.GroupInfo] = {}

    async def send_group_message(
        self, group_openid: str, message: send_message.GroupMessage
    ):
        data = _from_model_to_json(message)

        return await self.QQ_BOT.post_qqbot_api(
            f"v2/groups/{group_openid}/messages", json=data
        )

    async def _get_group_info(self, group_openid: str):
        data = await self.QQ_BOT.get_qqbot_api(f"v2/groups/{group_openid}/info")
        return group_info.GroupInfo.model_validate(data)

    async def get_group_info(self, group_openid: str):
        if group_openid in self._group_info_cache:
            return self._group_info_cache[group_openid]


        group_info_data = await self._get_group_info(group_openid)
        self._group_info_cache[group_openid] = group_info_data
        return group_info_data
