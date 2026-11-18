from typing import TYPE_CHECKING
lazy import base64
lazy import hashlib

from . import http_client
from .log import logger as log
from .types.qq_api import file_update, group_bot_info, group_info, user_info

if TYPE_CHECKING:
    import anyio
    from pydantic import BaseModel

    from .qq_bot import QQ_Bot
    from .types.qq_api import send_message


def _from_model_to_json(model: BaseModel) -> dict:
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

    async def get_file_uploader(self):
        return FileUploader(self)


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
        file_data: anyio.AsyncFile[bytes] | bytes,
        *,
        srv_send_msg: bool = False,
    ):
        # 读出二进制内容
        if isinstance(file_data, bytes):
            raw = file_data
        else:
            raw: bytes = await file_data.read()

        # 校验大小（5M 限制）
        if len(raw) > 5 * 1024 * 1024:
            raise ValueError(
                f"文件 {file_name} 大小 {len(raw)} 字节超过 5M,"
                "请改用 URL 上传或分片上传路径"
            )

        # base64 编码
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
        file_name: str,
        file_data: anyio.AsyncFile[bytes] | bytes,
        file_type: file_update.FileType,
        *,
        srv_send_msg: bool = False,
    ):
        # 读出二进制内容
        if isinstance(file_data, bytes):
            raw = file_data
        else:
            raw: bytes = await file_data.read()

        md5 = hashlib.md5(raw).hexdigest()
        sha1 = hashlib.sha1(raw).hexdigest()
        # 前 10002432 字节（约 10MB） 的 MD5 值
        md5_10m = hashlib.md5(raw[:10002432]).hexdigest()
        file_size = len(raw)

        log.info(
            f"准备上传大文件 {file_name}，大小 {file_size} 字节，MD5 {md5}，SHA1 {sha1}，前 10MB MD5 {md5_10m}"
        )

        file_update_prepare_request = file_update.FileUpdatePrepareRequest(
            file_type=file_type,
            file_size=file_size,
            file_name=file_name,
            md5=md5,
            sha1=sha1,
            md5_10m=md5_10m,
        )

        prepare_result = await self._upload_prepare_large_file(
            type, open_id, file_update_prepare_request
        )

        log.info(
            f"上传大文件 {file_name} 准备完成，upload_id {prepare_result.upload_id}，分块大小 {prepare_result.block_size} 字节，共 {len(prepare_result.parts)} 个分片"
        )

        for part in prepare_result.parts:
            start = part.index * prepare_result.block_size
            end = min(start + prepare_result.block_size, len(raw))
            log.debug(f"上传大文件 {file_name} 的第 {part.index} 个分片，范围 [{start}:{end}]")
            part_data = raw[start:end]
            print(part_data)
            md5_part = hashlib.md5(part_data).hexdigest()
            log.debug(
                f"上传大文件 {file_name} 的第 {part.index} 个分片到 {part.presigned_url}，大小 {len(part_data)} 字节，范围 [{start}:{end}]，MD5 {md5_part}"
            )

            await self._upload_large_file_part(
                url=part.presigned_url,
                part_data=part_data,
            )

            await self._upload_large_file_finish(
                type,
                open_id,
                prepare_result.upload_id,
                part.index,
                len(part_data),
                md5_part,
            )

        return await self._merge_large_file(
            type,
            open_id,
            prepare_result.upload_id,
            file_name,
            file_type,
            srv_send_msg=srv_send_msg,
        )

    async def _upload_prepare_large_file(
        self,
        type: file_update.ApiType,
        open_id: str,
        file_update_prepare_request: file_update.FileUpdatePrepareRequest,
    ):
        data = _from_model_to_json(file_update_prepare_request)
        result = await self.QQ_BOT.post_qqbot_api(
            f"v2/{type}/{open_id}/upload_prepare", json=data
        )
        return file_update.FileUpdatePrepareResponse.model_validate(result)

    async def _upload_large_file_part(
        self,
        url: str,
        part_data: bytes,
    ):
        client = http_client.client
        return await client.put(url, content=part_data, timeout=60)

    async def _upload_large_file_finish(
        self,
        type: file_update.ApiType,
        open_id: str,
        upload_id: str,
        part_index: int,
        block_size: int,
        md5: str,
    ):
        file_upload_part_finish = file_update.FileUploadPartFinish(
            upload_id=upload_id, part_index=part_index, block_size=block_size, md5=md5
        )
        data = _from_model_to_json(file_upload_part_finish)
        return await self.QQ_BOT.post_qqbot_api(
            f"v2/{type}/{open_id}/upload_part_finish", json=data
        )

    async def _merge_large_file(
        self,
        type: file_update.ApiType,
        open_id: str,
        upload_id: str,
        file_name: str,
        file_type: file_update.FileType,
        srv_send_msg: bool = False,
    ):
        file_update_request = file_update.FileUpdateRequest(
            file_type=file_type,
            file_name=file_name,
            upload_id=upload_id,
            srv_send_msg=srv_send_msg,
        )
        return file_update.FileUpdateResult.model_validate(
            await self._update_file(type, open_id, file_update_request)
        )
