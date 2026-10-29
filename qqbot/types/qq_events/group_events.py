from dataclasses import dataclass

from ..bot_event import EventType
from . import BotEvent


@dataclass
class GroupMessageEvent(BotEvent):
    group_id: str
    message_id: str
    user_id: str
    user_nickname: str
    user_role: str
    message_content: str

    event_type: EventType = EventType.GROUP_MESSAGE


@dataclass
class GroupAtMessageEvent(BotEvent):
    event_type: EventType = EventType.GROUP_AT_MESSAGE
