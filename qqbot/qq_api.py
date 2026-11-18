from typing import TYPE_CHECKING
lazy import base64

from .types.qq_api import file_update, group_bot_info, group_info, user_info

if TYPE_CHECKING:
    import anyio
    from pydantic import BaseModel

    from .qq_bot import QQ_Bot
    from .types.qq_api import send_message


def _from_model_to_json(model: BaseModel):
    return model.model_dump(exclude_none=True)


class QQ_Api:
    def __init__(self, QQ_BOT: QQ_Bot):
        self.QQ_BOT = QQ_BOT
        self._group_info_cache: dict[str, group_info.GroupInfo] = {}
        self._bot_info_cache: group_bot_info.GroupBotInfo | None = None

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

    async def get_bot_info(self):
        if self._bot_info_cache is not None:
            return self._bot_info_cache

        data = await self.QQ_BOT.get_qqbot_api("users/@me")
        bot_info = group_bot_info.GroupBotInfo.model_validate(data)
        self._bot_info_cache = bot_info
        return bot_info

    async def get_user_info(self, user_openid: str):
        data = await self.QQ_BOT.get_qqbot_api(f"v2/users/{user_openid}/info")

        return user_info.UserInfoResponse.model_validate(data)


class FileUploader:
    def __init__(self, qq_api: QQ_Api) -> None:
        self.qq_api = qq_api
        self.QQ_BOT = qq_api.QQ_BOT

    async def _update_file(
        self,
        type: file_update.ApiType,
        open_id: str,
        file_update_request: file_update.FileUpdateRequest,
    ):
        data = _from_model_to_json(file_update_request)
        return await self.QQ_BOT.post_qqbot_api(f"v2/{type}/{open_id}/files", json=data)

    async def update_small_file(
        self,
        type: file_update.ApiType,
        open_id: str,
        file_type: file_update.FileType,
        file_name: str,
        file_data: anyio.AsyncFile[bytes],
        *,
        srv_send_msg: bool = False,
    ):
        # 1. 读出二进制内容
        raw: bytes = await file_data.read()

        # 2. 校验大小（5M 限制）
        if len(raw) > 5 * 1024 * 1024:
            raise ValueError(
                f"文件 {file_name} 大小 {len(raw)} 字节超过 5M,"
                "请改用 URL 上传或分片上传路径"
            )

        # 3. 按接口要求转成字符串（这里假设是 base64，请按文档确认）
        file_data_str = base64.b64encode(raw).decode("ascii")

        file_update_request = file_update.FileUpdateRequest(
            file_type=file_type,
            file_name=file_name,
            file_data=file_data_str,
            srv_send_msg=srv_send_msg,
        )

        return await self._update_file(type, open_id, file_update_request)

    async def update_large_file(
        self,
        type: file_update.ApiType,
        open_id: str,
        file_update_request: file_update.FileUpdateRequest,
    ):
        pass
