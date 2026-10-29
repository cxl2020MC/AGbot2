from pydantic import BaseModel
from typing import Any
from .qq_events.qq_op import OpType


class WsData(BaseModel):
    # opcode
    op: OpType
    # 事件id
    id: str | None = None
    # 下行消息序列号
    s: int | None = None
    # 事件类型
    t: str | None = None
    # 事件内容
    d: Any | dict | None = None


# class WsDataFactory:
