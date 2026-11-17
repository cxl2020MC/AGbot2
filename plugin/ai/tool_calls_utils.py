import traceback
from collections.abc import Awaitable, Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

import openai
from openai.types.chat import (
    # ChatCompletionContentPartParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionFunctionToolParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallUnionParam,
    ChatCompletionToolMessageParam,
    ParsedFunctionToolCall,
)
from pydantic import BaseModel

from qqbot.log import logger as log
from qqbot.types.qq_events import qq_message

# from pydantic import BaseModel, Field
if TYPE_CHECKING:
    from qqbot.qq_bot import QQ_Bot

    from . import ai


def make_tool_call_result(
    *,
    tool_call_id: str,
    content: str | Iterable[ChatCompletionContentPartTextParam],
) -> ChatCompletionToolMessageParam:
    return {"role": "tool", "tool_call_id": tool_call_id, "content": content}


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
            if message["role"] == "tool" and message["tool_call_id"] == tool_call["id"]:
                message_tool_calls.remove(tool_call)
    if len(message_tool_calls) > 0:
        log.warning(f"以下工具调用在回复中找不到对应的ID: {message_tool_calls}")


# @dataclass
class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        model: type[BaseModel],
        function: Callable[..., Awaitable],
        *,
        need_scene: bool = False,
    ):
        self.name = name
        self.description = description
        self.function = function
        self.model = model
        self.tool_call: ChatCompletionFunctionToolParam = openai.pydantic_function_tool(
            model=model, name=name, description=description
        )
        self.need_scene = need_scene

    def __str__(self):
        # return f"Tool(name={self.name}, description={self.description}, model={self.model})"
        return str(self.tool_call)


@dataclass
class ToolScene:
    run_count: int


class ToolCallManager:
    def __init__(self, ai_obj: ai.AiChatManager) -> None:
        # self.tools: list[ChatCompletionToolUnionParam] = []
        self.tools: list[Tool] = []
        self.ai_obj = ai_obj

    # def add_tool(self, tool_call: ChatCompletionToolUnionParam):
    #     self.tools.append(tool_call)

    def add_tool(self, tool: Tool):
        for existing_tool in self.tools:
            if existing_tool.name == tool.name:
                log.warning(f"工具 {tool.name} 已存在，将被覆盖。")
                self.tools.remove(existing_tool)
                break
        self.tools.append(tool)

    def add_tools(self, tools: Sequence[Tool]):
        self.tools.extend(tools)

    def get_tools(self):
        return self.tools

    def change_tool(self, tool_name: str, new_tool: Tool):
        for i, tool in enumerate(self.get_tools()):
            if tool.name == tool_name:
                self.tools[i] = new_tool
                break

    def get_tools_list(self):
        tools: list[ChatCompletionFunctionToolParam] = []
        for tool in self.get_tools():
            tools.append(tool.tool_call)
        return tools

    async def run_tool_calls(
        self,
        tool_calls: list[ParsedFunctionToolCall],
        tool_scene: ToolScene,
    ) -> list[ChatCompletionToolMessageParam]:
        results = []
        for tool_call in tool_calls or []:
            tool_call_id = tool_call.id
            tool_name = tool_call.function.name
            tool_args = tool_call.function.parsed_arguments
            log.info(f"执行工具调用: {tool_name}({tool_args})[{tool_call_id}]")
            # 执行工具调用的逻辑
            for tool in self.get_tools():
                if tool.name == tool_name:
                    log.debug(f"匹配到工具: {tool}")
                    try:
                        if tool.need_scene:
                            result_content = await tool.function(tool_args, tool_scene)
                        else:
                            result_content = await tool.function(tool_args)
                    except Exception:  # noqa: BLE001
                        error_str = traceback.format_exc()
                        log.exception(
                            f"工具 {tool_name} 参数 {tool_args} [{tool_call_id}] 调用失败"
                        )
                        result_content = f"发生错误: {error_str}"
                    results.append(
                        make_tool_call_result(
                            tool_call_id=tool_call_id, content=result_content
                        )
                    )
        return results

    async def stop_all_tool_calls(
        self, tool_calls: list[ParsedFunctionToolCall], stop_message: str
    ):
        results = []
        for tool_call in tool_calls or []:
            tool_call_id = tool_call.id
            tool_name = tool_call.function.name
            tool_args = tool_call.function.parsed_arguments
            log.info(f"阻止工具调用: {tool_name}({tool_args})[{tool_call_id}]")
            results.append(
                make_tool_call_result(tool_call_id=tool_call_id, content=stop_message)
            )
        return results
