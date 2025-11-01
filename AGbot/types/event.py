from enum import Enum


class onEvent(Enum):
    message = "message"
    notice = "notice"
    request = "request"
    meta_event = "meta_event"