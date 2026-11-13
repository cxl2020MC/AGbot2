from collections.abc import Iterable

from openai.types.chat import (
    # ChatCompletionContentPartParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallUnionParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolUnionParam,
)

from qqbot.log import logger as log

# from pydantic import BaseModel, Field


def make_tool_call_result(
    self,
    /,
    tool_call_id: str,
    content: str | Iterable[ChatCompletionContentPartTextParam],
) -> ChatCompletionToolMessageParam:
    return {"role": "tool", "tool_call_id": tool_call_id, "content": content}


class ToolCallManager:
    def __init__(self, ai_obj) -> None:
        self.tool_calls: list[ChatCompletionToolUnionParam] = []
        self.ai_obj = ai_obj

    def add_tool_call(self, tool_call: ChatCompletionToolUnionParam):
        self.tool_calls.append(tool_call)

    def scan_tool_calls(self, messages: list[ChatCompletionMessageParam]):
        message_tool_calls: list[ChatCompletionMessageToolCallUnionParam] = []
        for message in messages:
            tool_calls = message.get("tool_calls")
            if message["role"] == "assistant" and tool_calls is not None:
                # for tool_call in tool_calls:
                # message_tool_calls.append(tool_call)
                message_tool_calls.extend(tool_calls)
        for tool_call in message_tool_calls:
            for message in messages:
                if (
                    message["role"] == "tool"
                    and message["tool_call_id"] == tool_call["id"]
                ):
                    message_tool_calls.remove(tool_call)
        if len(message_tool_calls) > 0:
            log.warning(f"以下工具调用在回复中找不到对应的ID: {message_tool_calls}")

    def make_tool_call_result(
        self,
        /,
        tool_call_id: str,
        content: str | Iterable[ChatCompletionContentPartTextParam],
    ):
        return {"role": "tool", "tool_call_id": tool_call_id, "content": content}
