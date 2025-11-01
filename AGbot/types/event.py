from enum import Enum


class Event(Enum):
    message = "message"
    notice = "notice"
    request = "request"
    meta_event = "meta_event"

class MessageEvent(Enum):
    private = "private"
    group = "group"
    # unknown = "unknown"
