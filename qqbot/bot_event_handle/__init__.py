from dataclasses import dataclass

from ..types.qq_events import EventType


@dataclass
class BotEvent:
    event_type: EventType
