from dataclasses import dataclass

from ..types.bot_event import EventType
from . import BotEvent


@dataclass
class GroupMessageEvent(BotEvent):
    event_type: EventType = EventType.GROUP_MESSAGE


@dataclass
class GroupAtMessageEvent(BotEvent):
    event_type: EventType = EventType.GROUP_AT_MESSAGE
