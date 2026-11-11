from pydantic import BaseModel, Field

from typing import Literal

from . import ai

class ToolCall(BaseModel):
    type: Literal["function"] = Field(..., description="函数名称")
    tool_name: str = Field(..., description="函数名称")

    tool_args: dict = Field(..., description="A dictionary of arguments to be passed to the tool.")
