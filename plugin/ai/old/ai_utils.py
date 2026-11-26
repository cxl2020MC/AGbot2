from collections.abc import Iterable, Sequence
from typing import cast

import openai
from openai.types.responses import (
    ParsedResponseFunctionToolCall,
    ResponseFunctionCallOutputItem,
    ResponseFunctionCallOutputItemList,
    ResponseFunctionCallOutputItemListParam,
    ResponseFunctionCallOutputItemParam,
    ResponseFunctionToolCall,
    ResponseFunctionToolCallOutputItem,
    ResponseFunctionToolCallParam,
    ResponseInputFile,
    ResponseInputImage,
    # ResponseCustomToolCallParam,
    # ResponseCustomToolCallOutput,
    ResponseInputImageParam,
    ResponseInputItemParam,
    ResponseInputMessageContentListParam,
    ResponseInputParam,
    # ResponseInputText,
    ResponseInputTextParam,
)

from qqbot.log import logger as log
from qqbot.utils import data_utils

from . import tool_calls_utils

client = openai.AsyncOpenAI()

AI_MODEL = "deepseek-flash"
# AI_MODEL = "deepseek-v4.1-flash-1017"


def make_user_message(content: str | ResponseInputMessageContentListParam):
    message: ResponseInputItemParam = {
        "type": "message",
        "role": "user",
        "content": content,
    }
    return message


def make_text_content(text: str):
    message = ResponseInputTextParam(
        type="input_text",
        text=text,
    )
    return message


def make_image_content(image_url: str | None = None, file_id: str | None = None):
    message = ResponseInputImageParam(
        detail="auto",
        type="input_image",
        image_url=image_url,
        file_id=file_id,
    )
    return message


type FunctionCallOutput = str | ResponseFunctionCallOutputItemListParam


def make_function_call_output_message(
    function_call: ResponseFunctionToolCall,
    output: FunctionCallOutput,
) -> ResponseInputItemParam:
    # output: str | list[ResponseInputText| ResponseInputImage| ResponseInputFile] = output
    message: ResponseInputItemParam = {
        "type": "function_call_output",
        "id": function_call.id,
        "call_id": function_call.call_id,
        # status=function_call.status if function_call.status else "completed",
        "output": output,
    }
    return message


class AiChatManager:
    def __init__(
        self,
        system_message: str,
        tool_calls: list[tool_calls_utils.Tool] | None = None,
        name: str | None = None,
        tool_call_limit: int = 15,
    ):
        self.ai_messages: ResponseInputParam = []
        self.system_message: str = system_message
        self._tool_call_manager = tool_calls_utils.ToolCallManager()
        self.name: str | None = name
        self.tool_call_limit: int = tool_call_limit
        if tool_calls:
            self._tool_call_manager.add_tools(tool_calls)

        log.debug(f"已注册工具函数: {self._tool_call_manager.get_tools_list()}")

    async def add_message(self, message: ResponseInputItemParam):
        self.ai_messages.append(message)

    async def add_messages(self, messages: ResponseInputParam):
        self.ai_messages.extend(messages)

    async def add_user_message(self, content: str):
        message: ResponseInputItemParam = make_user_message(content)
        await self.add_message(message)

    async def get_messages(self):
        return self.ai_messages

    async def clear_messages(self):
        log.info("清理AI上下文消息……")
        self.ai_messages.clear()
        log.info("清理AI上下文消息完成。")

    async def use_ai(self, messages: ResponseInputParam):
        if self.name:
            message_json_path = data_utils.get_file_path(
                f"ai_messages/{self.name}.json"
            )
            log.debug(f"向 {message_json_path} 写入AI请求消息")
            await data_utils.write_json_file(
                message_json_path,
                list(messages),
            )
            log.debug("写入AI请求消息完成")
        else:
            log.debug(f"AI请求消息: {messages}")
        completion = await client.responses.parse(
            model=AI_MODEL,
            instructions=self.system_message,
            input=messages,
            tools=self._tool_call_manager.get_tools_list(),
        )
        log.debug(f"AI响应: {completion}")
        return completion

    async def handle_ai(
        self,
        messages: ResponseInputParam,
        *,
        run_count: int = 0,
    ):
        await self.add_messages(messages)
        log.debug(f"处理AI请求: {messages}")
        ai_messages = await self.get_messages()

        completion = await self.use_ai(ai_messages)

        tool_calls: list[ParsedResponseFunctionToolCall] = []
        for output in completion.output:
            match output.type:
                case "reasoning":
                    log.info(f"AI推理内容: {output.content}")
                case "message":
                    log.info(f"AI输出正文: {output.content}")
                case "function_call":
                    log.info(f"AI工具调用: {output}")
                    tool_calls.append(output)
                case _:
                    log.warning(f"未知的输出类型: {output.type}")

        total_tokens = completion.usage.total_tokens if completion.usage else 0
        log.info(f"本次上下文长度为 {total_tokens} token。")
        log.debug(f"详细使用情况: {completion.usage}")

        await self.add_messages(
            cast(
                ResponseInputParam,
                [output.to_dict(mode="json") for output in completion.output],
            )
        )
        if tool_calls:
            tool_call_scene = tool_calls_utils.ToolScene(
                run_count=run_count,
            )
            tool_result = await self._tool_call_manager.run_tool_calls(
                tool_calls, tool_call_scene
            )
            completion = await self.handle_ai(tool_result, run_count=run_count + 1)

        if run_count == 0 and total_tokens > 100 * 1000:
            log.info("对话内容过长，进行总结以保留核心信息。")
            await self.context_completion()

        return completion

    async def context_completion(self):
        message_content = "对话内容过长，请总结之前的对话内容(不包括系统提示词)，保留核心信息，删除冗余内容，以便继续对话。只需要总结最近10～20条的对话内容，然后直接输出总结后的对话内容，并确保保留必要的上下文信息。"
        message = make_user_message(message_content)
        ai_return = await self.handle_ai(messages=[message], run_count=1)
        for output in ai_return.output:
            if output.type == "message":
                completion_message = output.content
                break
        else:
            log.warning("未能获取总结内容，使用默认提示。")
            completion_message = (
                ai_return.output[0] if ai_return.output else "未能获取总结内容。"
            )
        log.info(f"总结后的对话内容: {completion_message}")
        self.ai_messages = [
            {
                "role": "user",
                "content": f"由于前文上下文过长，已进行总结: {completion_message}",
            }
        ]
