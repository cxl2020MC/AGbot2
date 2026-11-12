from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class UserRole(StrEnum):
    群主 = "owner"
    管理员 = "admin"
    成员 = "member"

    # 自定义类型
    未知 = "unknown"

    @classmethod
    def _missing_(cls, value):
        return cls.未知


class MessageType(IntEnum):
    # 0=普通文本, 3=结构化卡片, 101=并行消息, 102=聊天记录, 103=引用消息
    普通文本 = 0
    结构化卡片 = 3
    并行消息 = 101
    聊天记录 = 102
    引用消息 = 103

    # 自定义类型
    其他类型 = -1

    @classmethod
    def _missing_(cls, value):
        return cls.其他类型


class User(BaseModel):
    id: str
    username: str
    bot: bool
    union_openid: str | None = None
    union_user_account: str | None = None
    user_openid: str | None = None
    member_openid: str | None = None
    member_role: UserRole | None = None


def parse_ext(ext: list[str]) -> dict[str, str]:
    result = {}
    for item in ext:
        if "=" in item:
            k, v = item.split("=", 1)
            result[k] = v
    return result


class MessageScene(BaseModel):
    source: str
    ext: list[str]

    msg_idx: str | None = None
    ref_msg_idx: str | None = None
    auth_token: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _lift_ext(cls, data):
        if isinstance(data, dict) and "ext" in data:
            data = dict(data)  # 不改原对象
            parsed = parse_ext(data.get("ext") or [])
            for key in ("msg_idx", "ref_msg_idx", "auth_token"):
                if key in parsed and data.get(key) is None:
                    data[key] = parsed[key]
        return data


class MessageAttachment(BaseModel):
    url: str
    filename: str
    size: int
    content_type: str
    width: int | None = None
    height: int | None = None
    voice_wav_url: str | None = None
    asr_refer_text: str | None = None


class MsgElement(BaseModel):
    msg_idx: str | None = None
    author: User | None = None
    message_type: MessageType | None = None
    content: str
    attachments: list[MessageAttachment] | None = None
    ark_data: Any | None = None
    msg_elements: list[MsgElement] | None = None


class ParallelMessage(BaseModel):
    # 看起来是仅在消息引用时才会出现, 文档里面不存在
    msg_nodes: list[MessageNode]


class MessageNode(BaseModel):
    # 看起来是仅在消息引用时才会出现, 文档里面不存在
    content: str
    message_type: MessageType


class Message(BaseModel):
    id: str
    author: User
    content: str
    timestamp: datetime
    message_type: MessageType
    message_scene: MessageScene
    attachments: list[MessageAttachment] | None = None
    mentions: list[User] | None = None
    ark_data: Any | None = None
    msg_elements: list[MsgElement] | None = None
    # 文档没有这个
    parallel_message: ParallelMessage | None = None


class GroupMessage(Message):
    group_openid: str
