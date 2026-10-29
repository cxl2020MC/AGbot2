from dataclasses import dataclass

from ..bot_event import EventType


@dataclass
class BotEvent:
    event_type: EventType