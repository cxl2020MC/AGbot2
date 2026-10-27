from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class UserRole(StrEnum):
    群主 = "owner"
    管理员 = "admin"
    成员 = "member"

class User(BaseModel):
    id: str
    username: str
    bot: bool
    union_openid: str | None = None
    union_user_account: str | None = None
    user_openid: str | None = None
    member_openid: str | None = None
    member_role: UserRole | None = None


class MessageScene(BaseModel):
    source: str
    ext: list[str]


class MessageAttachment(BaseModel):
    url: str
    filename: str
    size: int
    width: int | None = None
    height: int | None = None
    voice_wav_url: str | None = None
    asr_refer_text: str | None = None


class MsgElement(BaseModel):
    msg_idx: str
    author: User | None = None
    message_type: int
    content: str
    attachments: list[MessageAttachment] | None = None
    ark_data: Any | None = None
    msg_elements: list[MsgElement] | None = None

class Message(BaseModel):
    id: str
    author: User
    content: str
    timestamp: datetime
    message_type: int
    message_scene: MessageScene
    attachments: list[MessageAttachment] | None = None
    ark_data: Any | None = None
    msg_elements: list[MsgElement] | None = None

class GroupMessage(Message):
    group_openid: str
