import asyncio
from collections.abc import Iterable, Sequence
from typing import ClassVar, cast

import httpx2
import openai
from openai.types.chat import (
    ChatCompletionContentPartParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageFunctionToolCallParam,
    ChatCompletionMessageParam,
    ChatCompletionToolUnionParam,
    ParsedFunctionToolCall,
)
from pydantic import BaseModel, Field

from qqbot import plugin
from qqbot.log import logger as log
from qqbot.qq_bot import QQ_Bot

# from qqbot.types.bot_event import MessageEventType
from qqbot.types.qq_api import send_message
from qqbot.types.qq_events import qq_message
from qqbot.utils import command_utils

from . import ai_memory, system_prompt, tool_calls_utils, web_search

plugin = plugin.Plugin("ai", "一个简单的AI插件", "1.0.0")

client = openai.AsyncOpenAI(
    # api_key="your-api-key",
    base_url="https://api.deepseek.com"
    # base_url="https://ai.yumeyuki.moe/v1"
)

AI_MODEL = "deepseek-flash"
# AI_MODEL = "deepseek-v4.1-flash-1017"

SystemPrompt = system_prompt.SystemPrompt


GROUP_ID_BLACKLIST = [
    # "B274F145FD3D531A98184AD623AA9A88",
    "45F510227BFFF0355392E42E6B98015D",
]


class SendMessageToolParam(BaseModel):
    content: str = Field(..., description="需要发送的消息内容")
    ref_msg_idx: str | None = Field(
        None, description="引用消息时，需要引用的消息的消息索引"
    )


async def get_image_from_url(url, filename):
    img = await httpx2.get(url).aread()
    file = await client.files.create(
        file=(filename, img),
        purpose="user_data",
        expires_after={
            "anchor": "created_at",
            "seconds": 60 * 60 * 24 * 14,  # 14天后过期
        },
    )
    return ({"type": "file", "file_id": file.id},)

    # messages_content.append(
    #     {
    #         "type": "image_url",
    #         "image_url": {"url": attachment.url},
    #     }
    # )


TOOLS = [
    # tool_calls_utils.Tool(
    #     name="send_message",
    #     description="发送一条消息，支持markdown格式，你只能使用此工具函数发送消息，不能直接输出消息内容",
    #     model=SendMessageToolParam,
    #     function=send_message_tool_call,
    #     need_scene=True,
    # ),
    tool_calls_utils.Tool(
        name="add_memory",
        description="将消息内容存入记忆库，便于后续参考",
        model=ai_memory.MemoryWriteToolPram,
        function=ai_memory.write_memory_tool_call,
    ),
    tool_calls_utils.Tool(
        name="update_memory",
        description="修改记忆内容",
        model=ai_memory.MemoryUpdateToolPram,
        function=ai_memory.update_memory_tool_call,
    ),
    tool_calls_utils.Tool(
        name="search_memory",
        description="搜索记忆内容，返回命中的记忆内容",
        model=ai_memory.MemorySearchToolPram,
        function=ai_memory.search_memory_tool_call,
    ),
    tool_calls_utils.Tool(
        name="delete_memory",
        description="删除记忆内容",
        model=ai_memory.MemoryDeleteToolPram,
        function=ai_memory.delete_memory_tool_call,
    ),
    tool_calls_utils.Tool(
        name="web_search",
        description="搜索网页内容，返回搜索结果",
        model=web_search.WebSearchToolParam,
        function=web_search.web_search_tool_call,
    ),
    tool_calls_utils.Tool(
        name="web_fetch",
        description="获取网页内容，返回网页内容",
        model=web_search.WebFetchToolParam,
        function=web_search.web_fetch_tool_call,
    ),
]


class AIPlugin:
    workers: ClassVar[dict[str, AIPlugin]] = {}

    def __init__(self, group_openid: str, bot: QQ_Bot):
        self.group_openid = group_openid
        self.bot: QQ_Bot = bot
        self.ai_chat_manager: AiChatManager | None = None
        self.group_message_queue: asyncio.Queue[
            qq_message.GroupMessage | qq_message.Message
        ] = asyncio.Queue()
        self.worker_task = asyncio.create_task(
            self.worker(), name=f"AIPluginWorker-{group_openid}"
        )
        self.load_memory_id_list = []  # 用于存储已加载的记忆ID，避免重复加载

    @staticmethod
    async def get_group_worker(bot: QQ_Bot, group_openid: str):
        if group_openid not in AIPlugin.workers:
            AIPlugin.workers[group_openid] = AIPlugin(group_openid, bot)
        return AIPlugin.workers[group_openid]

    async def send_message_tool_call(
        self, tool_args: SendMessageToolParam, tool_scene: tool_calls_utils.ToolScene
    ):
        bot = self.bot
        ref_msg_idx = tool_args.ref_msg_idx
        return_data = await bot.qq_api.send_group_message(
            self.group_openid,
            send_message.GroupMessage(
                msg_type=send_message.GroupMessageType.MARKDOWN,
                markdown=send_message.MessageMarkdown(content=tool_args.content),
                message_reference=send_message.MessageReference(message_id=ref_msg_idx)
                if ref_msg_idx
                else None,
                msg_seq=tool_scene.run_count if ref_msg_idx else None,
            ),
        )
        log.debug(f"发送消息返回: {return_data}")
        return_mesage = f"发送消息成功: 消息id={return_data['id']}, 消息索引={return_data['ext_info']['ref_idx']}"
        return return_mesage

    async def get_ai_chat_manager(self):
        if self.ai_chat_manager is None:
            bot_info = await self.bot.qq_api.get_bot_info()
            group_info = await self.bot.qq_api.get_group_info(self.group_openid)
            system_message_content = SystemPrompt.format(
                BOT_ID=bot_info.union_openid,
                GROUP_NAME=group_info.group_name,
                GROUP_OPENID=self.group_openid,
            )
            tools = TOOLS.copy()
            tools.insert(
                0,
                tool_calls_utils.Tool(
                    name="send_message",
                    description="发送一条消息，支持markdown格式，你只能使用此工具函数发送消息，不能直接输出消息内容",
                    model=SendMessageToolParam,
                    function=self.send_message_tool_call,
                    need_scene=True,
                ),
            )
            self.ai_chat_manager = AiChatManager(
                system_message_content,
                tool_calls=tools,
            )
        return self.ai_chat_manager

    async def generate_message(
        self, event_data: qq_message.GroupMessage | qq_message.Message
    ):
        ai_memory_content = await ai_memory.search_memory(
            f"[{event_data.author.username}] [{event_data.author.id}] {event_data.content}",
            filiter_object_ids=self.load_memory_id_list,  # 传入已加载的记忆ID列表，避免重复加载
        )
        for memory in ai_memory_content:
            log.debug(f"添加已加载记忆ID: {memory.id}")
            self.load_memory_id_list.append(memory.id)  # 将记忆ID添加到已加载集合中

        log.debug(f"命中的记忆内容: {ai_memory_content}")

        message_metadata: list[str] = [
            "消息ID: " + event_data.id,
            "消息类型: " + event_data.message_type.name,
            f"消息索引: {event_data.message_scene.msg_idx}",
            f"引用目标消息索引: {event_data.message_scene.ref_msg_idx}",
        ]
        if event_data.msg_elements:
            message_metadata.append(f"消息元素: {event_data.msg_elements}")
        if event_data.parallel_message:
            message_metadata.append(
                f"消息节点: {event_data.parallel_message.msg_nodes}"
            )

        message_type_flag = []
        if event_data.author.union_openid == "1AE10B8401B2C79FAC54EA62A9EE2272":
            message_type_flag.append("主人")
        if event_data.mentions:
            for mention in event_data.mentions:
                if mention.id == (await self.bot.qq_api.get_bot_info()).union_openid:
                    message_type_flag.append("被@")

        messages_content: list[ChatCompletionContentPartParam] = [
            {
                "type": "text",
                "text": f"""[{event_data.timestamp}][{event_data.author.username}]({event_data.author.id})[{event_data.message_type.name}]{message_type_flag}: {event_data.content}
[{"]\n[".join(message_metadata)}]

## 命中的记忆内容
{"\n".join(str(memory) for memory in ai_memory_content) if ai_memory_content else "无"}""",
            }
        ]

        if event_data.attachments:
            for attachment in event_data.attachments:
                # if attachment.asr_refer_text:
                #     event_data.content += f"\n[语音转文字]: {attachment.asr_refer_text}"
                if attachment.content_type.startswith("image"):
                    img = await httpx2.get(attachment.url).aread()
                    file = await client.files.create(
                        file=(attachment.filename, img),
                        purpose="user_data",
                        expires_after={
                            "anchor": "created_at",
                            "seconds": 60 * 60 * 24 * 14,  # 14天后过期
                        },
                    )
                    messages_content.append(
                        cast(
                            ChatCompletionContentPartParam,
                            {"type": "file", "file_id": file.id},
                        ),
                    )
                    # messages_content.append(
                    #     {
                    #         "type": "image_url",
                    #         "image_url": {"url": attachment.url},
                    #     }
                    # )
                elif attachment.content_type.startswith("voice"):
                    if attachment.asr_refer_text:
                        messages_content.append(
                            {
                                "type": "text",
                                "text": f"[语音转文字]: {attachment.asr_refer_text}",
                            }
                        )
                    else:
                        messages_content.append(
                            {
                                "type": "text",
                                "text": "[语音消息]: 无法识别语音内容",
                            }
                        )

        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "user",
                "content": messages_content,
            }
        ]

        return messages

    async def handle_ai(
        self,
        event_data: qq_message.GroupMessage | qq_message.Message,
        bot: QQ_Bot,
    ):
        messages = await self.generate_message(event_data)

        ai_chat_manager = await self.get_ai_chat_manager()
        return await ai_chat_manager.handle_ai(messages)

    async def worker(self):
        log.debug(f"启动AI插件工作线程，处理群聊 {self.group_openid} 的消息。")
        while True:
            event_data = await self.group_message_queue.get()
            try:
                await self.handle_ai(event_data, self.bot)
            except Exception:  # noqa: BLE001
                log.exception("AI 插件处理消息时发生异常")
            finally:
                self.group_message_queue.task_done()

    async def handle_message(
        self, event_data: qq_message.GroupMessage | qq_message.Message
    ):
        queue = self.group_message_queue
        await queue.put(event_data)

    async def clear_messages(self):
        log.info(f"清理群聊 {self.group_openid} 的上下文消息……")
        await (await self.get_ai_chat_manager()).clear_messages()
        log.info(f"清理群聊 {self.group_openid} 的上下文消息完成。")


@plugin.on_message(
    name="AI助手",
    # message_types=[qq_message.GroupMessage]
)
async def handle_group_message(event_data: qq_message.GroupMessage, bot: QQ_Bot):
    group_openid = event_data.group_openid

    if group_openid in GROUP_ID_BLACKLIST:
        log.info(f"群聊 {group_openid} 在黑名单中，跳过AI处理。")
        return

    if event_data.content.startswith("/"):
        log.info(f"群聊 {group_openid} 的消息以 / 开头，跳过AI处理。")
        return

    ai_plugin = await AIPlugin.get_group_worker(bot, group_openid)
    # return await ai_plugin.handle_ai(event_data, bot)
    return await ai_plugin.handle_message(event_data)


@plugin.on_command(
    ("chat_black_list", "聊天黑名单"), "聊天黑名单", "关于聊天黑名单的各种操作"
)
async def chat_black_list_command(
    event_data: qq_message.GroupMessage | qq_message.Message, bot: QQ_Bot
):
    if isinstance(event_data, qq_message.GroupMessage):
        await bot.qq_api.send_group_message(
            event_data.group_openid,
            send_message.GroupMessage(content=f"当前聊天黑名单: {GROUP_ID_BLACKLIST}"),
        )


@plugin.on_command(("chat_clear", "重置上下文"), "重置上下文", "清除当前群聊的上下文")
async def clear_command(
    event_data: qq_message.GroupMessage | qq_message.Message, bot: QQ_Bot
):
    if isinstance(event_data, qq_message.GroupMessage):
        await (
            await AIPlugin.get_group_worker(bot, event_data.group_openid)
        ).clear_messages()
        await bot.qq_api.send_group_message(
            event_data.group_openid,
            send_message.GroupMessage(content="清理当前群聊的上下文成功"),
        )


class AiChatManager:
    def __init__(
        self,
        system_message_content: str,
        tool_calls: list[tool_calls_utils.Tool] | None = None,
    ):
        self.ai_messages: list[ChatCompletionMessageParam] = []
        self.system_message_content: str = system_message_content
        self.system_message: ChatCompletionMessageParam | None = None
        self._tool_call_manager = tool_calls_utils.ToolCallManager(self)

        if tool_calls:
            self._tool_call_manager.add_tools(tool_calls)

        log.debug(f"已注册工具函数: {self._tool_call_manager.get_tools_list()}")

    async def add_message(self, message: ChatCompletionMessageParam):
        self.ai_messages.append(message)

    async def add_messages(self, messages: Sequence[ChatCompletionMessageParam]):
        self.ai_messages.extend(messages)

    async def add_user_message(self, content: str):
        message: ChatCompletionMessageParam = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": content,
                }
            ],
        }
        await self.add_message(message)

    async def add_tool_message(
        self,
        tool_call_id: str,
        content: str | Iterable[ChatCompletionContentPartTextParam],
    ):
        message: ChatCompletionMessageParam = {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": content,
        }
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
        log.debug(f"AI请求消息: {ai_messages}")

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
        await self.add_assistant_message(
            content=ai_ret_messages.content if ai_ret_messages.content else "",
            reasoning_content=reasoning_content,
            tool_calls=parse_tool_calls if parse_tool_calls else None,
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
