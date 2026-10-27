from enum import IntEnum


class OpType(IntEnum):
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    Resume = 6
    RECONNECT = 7
    Invalid_Session = 9
    HELLO = 10
    Heartbeat_ACK = 11
    # HTTP_Callback_ACK = 12
