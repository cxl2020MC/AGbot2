from collections.abc import Iterable, Sequence
from typing import cast

import openai
from openai.types.chat import (
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageFunctionToolCallParam,
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolUnionParam,
    ChatCompletionUserMessageParam,
    ParsedFunctionToolCall,
)

from qqbot.log import logger as log
from qqbot.utils import data_utils

from . import tool_calls_utils

client = openai.AsyncOpenAI(
    default_headers={
        "User-Agent": "AGbot2/5.0.0",
        "x-opencode-session": "cxl2020mc-AGbot2",
    }
)

# AI_MODEL = "deepseek-flash"
AI_MODEL = "deepseek-v4.1-flash"
# AI_MODEL = "deepseek-v4.1-flash-1017"


def make_user_message(content: str | Iterable[ChatCompletionContentPartParam]):
    message = ChatCompletionUserMessageParam(role="user", content=content)
    return message


def make_text_content(text: str):
    message = ChatCompletionContentPartTextParam(
        type="text",
        text=text,
    )
    return message


def make_image_content(image_url: str | None = None, file_id: str | None = None):
    if image_url:
        message = ChatCompletionContentPartImageParam(
            type="image_url", image_url={"url": image_url}
        )
    else:
        message = cast(
            ChatCompletionContentPartImageParam, {"type": "file", "file_id": file_id}
        )
    return message


def make_tool_call_message(
    tool_call_id: str,
    content: str | Iterable[ChatCompletionContentPartTextParam],
):
    message = ChatCompletionToolMessageParam(
        role="tool",
        tool_call_id=tool_call_id,
        content=content,
    )
    return message


class AiChatManager:
    def __init__(
        self,
        system_message_content: str,
        tool_calls: list[tool_calls_utils.Tool] | None = None,
        name: str | None = None,
    ):
        self.ai_messages: list[ChatCompletionMessageParam] = []
        self.system_message_content: str = system_message_content
        self.system_message = ChatCompletionSystemMessageParam(
            role="system", content=system_message_content
        )
        self._tool_call_manager = tool_calls_utils.ToolCallManager()
        self.name: str | None = name
        if tool_calls:
            self._tool_call_manager.add_tools(tool_calls)

        log.debug(f"已注册工具函数: {self._tool_call_manager.get_tools_list()}")

    async def add_message(self, message: ChatCompletionMessageParam):
        self.ai_messages.append(message)

    async def add_messages(self, messages: Iterable[ChatCompletionMessageParam]):
        self.ai_messages.extend(messages)

    async def add_user_message(
        self, content: str | Iterable[ChatCompletionContentPartParam]
    ):
        message = make_user_message(
            content,
        )
        await self.add_message(message)

    async def add_tool_message(
        self,
        tool_call_id: str,
        content: str | Iterable[ChatCompletionContentPartTextParam],
    ):
        message = ChatCompletionToolMessageParam(
            role="tool",
            tool_call_id=tool_call_id,
            content=content,
        )
        await self.add_message(message)

    async def get_messages(self):
        ai_messages: list[ChatCompletionMessageParam] = [self.system_message]
        ai_messages.extend(self.ai_messages)
        return ai_messages

    async def clear_messages(self):
        log.info("清理AI上下文消息……")
        self.ai_messages.clear()
        log.info("清理AI上下文消息完成。")

    async def use_ai(self, messages: Sequence[ChatCompletionMessageParam]):
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
        completion = await client.chat.completions.parse(
            model=AI_MODEL,
            messages=messages,
            tools=self._tool_call_manager.get_tools_list(),
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}},
        )
        log.debug(f"AI响应: {completion}")
        return completion

    async def handle_ai(
        self,
        messages: Iterable[ChatCompletionMessageParam] | None = None,
        *,
        run_count: int = 0,
    ):
        if messages:
            await self.add_messages(messages)
        log.debug(f"处理AI请求: {messages}")
        ai_messages = await self.get_messages()

        completion = await self.use_ai(ai_messages)
        ai_ret_messages = completion.choices[0].message
        log.debug(f"AI返回内容: {ai_ret_messages}")
        reasoning_content = getattr(ai_ret_messages, "reasoning_content", None)
        log.info(f"AI推理内容: {reasoning_content}")
        log.info(f"AI工具调用: {ai_ret_messages.tool_calls}")
        log.info(f"AI返回内容: {ai_ret_messages.content}")
        total_tokens = completion.usage.total_tokens if completion.usage else 0
        log.info(f"本次上下文长度为 {total_tokens} token。")
        log.debug(
            f"详细使用情况: {completion.usage.prompt_tokens_details if completion.usage else 'N/A'}"
        )
        tool_calls = ai_ret_messages.tool_calls

        await self.add_message(
            cast(ChatCompletionMessageParam, ai_ret_messages.to_dict(mode="json"))
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
        message = make_user_message(
            content=[
                make_text_content(message_content),
            ]
        )
        ai_return = await self.handle_ai(messages=[message], run_count=1)
        completion_message = ai_return.choices[0].message.content
        log.info(f"总结后的对话内容: {completion_message}")
        self.ai_messages = [
            make_user_message(
                content=[
                    make_text_content(
                        f"由于前文上下文过长，已进行总结: {completion_message}"
                    ),
                ]
            )
        ]
