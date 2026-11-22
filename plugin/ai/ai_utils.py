from collections.abc import Iterable, Sequence
from typing import cast

import openai
from openai.types.chat import (
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageFunctionToolCallParam,
    ChatCompletionMessageParam,
    ChatCompletionToolUnionParam,
    ParsedFunctionToolCall,
    ChatCompletionUserMessageParam,
    ChatCompletionToolMessageParam,
)

from qqbot.log import logger as log
from qqbot.utils import data_utils

from . import tool_calls_utils

client = openai.AsyncOpenAI(
    # api_key="your-api-key",
    # base_url="https://api.deepseek.com"
    # base_url="https://ai.yumeyuki.moe/v1"
)

AI_MODEL = "deepseek-flash"
# AI_MODEL = "deepseek-v4.1-flash-1017"


class AiChatManager:
    def __init__(
        self,
        system_message_content: str,
        tool_calls: list[tool_calls_utils.Tool] | None = None,
        name: str | None = None,
    ):
        self.ai_messages: list[ChatCompletionMessageParam] = []
        self.system_message_content: str = system_message_content
        self.system_message: ChatCompletionMessageParam | None = None
        self._tool_call_manager = tool_calls_utils.ToolCallManager()
        self.name: str | None = name
        if tool_calls:
            self._tool_call_manager.add_tools(tool_calls)

        log.debug(f"已注册工具函数: {self._tool_call_manager.get_tools_list()}")

    async def add_message(self, message: ChatCompletionMessageParam):
        self.ai_messages.append(message)

    async def add_messages(self, messages: Sequence[ChatCompletionMessageParam]):
        self.ai_messages.extend(messages)

    async def add_user_message(self, content: str):
        message = ChatCompletionUserMessageParam(
            role="user",
            content=[
                {
                    "type": "text",
                    "text": content,
                }
            ],
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

    async def add_assistant_message(
        self,
        content: str | Iterable[ChatCompletionContentPartTextParam],
        reasoning_content: str | None = None,
        tool_calls: Sequence[ChatCompletionToolUnionParam] | None = None,
    ):
        message: ChatCompletionMessageParam = cast(
            ChatCompletionMessageParam,
            {
                "role": "assistant",
                "content": content,
                "reasoning_content": reasoning_content,
                "tool_calls": tool_calls,
            },
        )
        await self.add_message(message)

    async def set_system_message(self, content: str):
        message: ChatCompletionMessageParam = {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": content,
                }
            ],
        }
        self.system_message = message

    async def get_messages(self) -> list[ChatCompletionMessageParam]:
        if self.system_message is None:
            await self.set_system_message(self.system_message_content)
        # 理论上永远不会被运行的 if 这一块
        if self.system_message is None:
            raise ValueError(
                "系统消息未设置，请先调用 set_system_message 方法设置系统消息。"
            )
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
        messages: Sequence[ChatCompletionMessageParam],
        system_message: str | None = None,
        *,
        run_count: int = 0,
    ):
        if system_message is not None:
            await self.set_system_message(system_message)

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

        parse_tool_calls = []
        if tool_calls:
            for tool_call in tool_calls:
                parse_tool_calls.append(
                    ChatCompletionMessageFunctionToolCallParam(
                        id=tool_call.id,
                        type="function",
                        function={
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,  # 已经是 JSON 字符串
                        },
                    ),
                )
        # await self.add_assistant_message(
        #     content=ai_ret_messages.content if ai_ret_messages.content else "",
        #     reasoning_content=reasoning_content,
        #     tool_calls=parse_tool_calls if parse_tool_calls else None,
        # )
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
        message: ChatCompletionMessageParam = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": message_content,
                }
            ],
        }
        ai_return = await self.handle_ai(messages=[message], run_count=1)
        completion_message = ai_return.choices[0].message.content
        log.info(f"总结后的对话内容: {completion_message}")
        self.ai_messages = [
            {
                "role": "user",
                "content": f"由于前文上下文过长，已进行总结: {completion_message}",
            }
        ]
