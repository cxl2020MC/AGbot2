from enum import Enum, Flag


# class Event(Enum):
#     message = "message"
#     notice = "notice"
#     request = "request"
#     meta_event = "meta_event"

# class MessageEvent(Enum):
#     private = "private"
#     group = "group"
#     # unknown = "unknown"


class Event(Flag):
    GroupMessage = 1
    PrivateMessage = 2
    Message = GroupMessage | PrivateMessage
    Notice = 4
    