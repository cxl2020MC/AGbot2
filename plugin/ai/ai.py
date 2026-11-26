import asyncio
from collections.abc import Iterable
from typing import ClassVar

import httpx2
import yarl
from openai.types.chat import (
    ChatCompletionContentPartParam,
    ChatCompletionMessageParam,
)
from pydantic import BaseModel, Field

from plugin.ai.ai_utils import AiRawMessages
from qqbot import plugin
from qqbot.log import logger as log
from qqbot.qq_bot import QQ_Bot

# from qqbot.types.bot_event import MessageEventType
from qqbot.types.qq_api import api_type, send_message
from qqbot.types.qq_events import qq_message
from qqbot.utils import command_utils, data_url_utils, message_sticker

# from .ai_utils import AiChatManager, client
from . import (
    ai_memory,
    ai_utils,
    nbnhhsh,
    subagent_utils,
    system_prompt,
    tool_calls_utils,
    web_search,
)

plugin = plugin.Plugin("ai", "一个简单的AI插件", "1.0.0")


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


class DeleteMessageToolParam(BaseModel):
    message_id: str = Field(..., description="需要删除的消息的消息id")


async def get_image_from_url(url, filename):
    log.info(f"从URL获取图片: {url}, filename: {filename}")
    img = await httpx2.get(url).aread()

    # file = await ai_utils.client.files.create(
    #     file=(filename, img),
    #     purpose="user_data",
    #     expires_after={
    #         "anchor": "created_at",
    #         "seconds": 60 * 60 * 24 * 14,  # 14天后过期
    #     },
    # )
    # return ai_utils.make_image_content(file_id=file.id)
    data_url = await data_url_utils.get_data_url_by_bytes(
        img, await data_url_utils.get_bytes_minetype(img)
    )
    return ai_utils.make_image_content(image_url=data_url)


async def get_image_from_url_tool(
    tool_args: web_search.WebFetchToolParam,
) -> list[ChatCompletionContentPartParam]:
    yarl_url = yarl.URL(tool_args.url)
    filename = yarl_url.name
    return [await get_image_from_url(tool_args.url, filename)]


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
    tool_calls_utils.Tool(
        name="get_image_from_url",
        description="从图片URL获取图片，返回图片",
        model=web_search.WebFetchToolParam,
        function=get_image_from_url_tool,
    ),
    tool_calls_utils.Tool(
        name="nbnhhsh",
        description="获取拼音首字母缩写的全称（能不能好好说话？）",
        model=nbnhhsh.NbnhhshToolParam,
        function=nbnhhsh.get_nbnhhsh_tool_call,
    ),
]


class AIPlugin:
    workers: ClassVar[dict[str, AIPlugin]] = {}

    def __init__(self, group_openid: str, bot: QQ_Bot):
        self.group_openid = group_openid
        self.bot: QQ_Bot = bot
        self.ai_chat_manager: ai_utils.AiChatManager | None = None
        # self.subagent_manager: subagent_utils.SubAgent | None = None
        self.group_message_queue: asyncio.Queue[qq_message.Message | AiRawMessages] = (
            asyncio.Queue()
        )
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
        msg_type = send_message.GroupMessageType.TXT
        for mark in ["#", "`", "![", "<qqbot-at-"]:
            if mark in tool_args.content:
                msg_type = send_message.GroupMessageType.MARKDOWN
                break

        return_data = await bot.qq_api.send_group_message(
            self.group_openid,
            send_message.GroupMessage(
                msg_type=msg_type,
                markdown=send_message.MessageMarkdown(content=tool_args.content)
                if msg_type == send_message.GroupMessageType.MARKDOWN
                else None,
                content=tool_args.content
                if msg_type == send_message.GroupMessageType.TXT
                else None,
                message_reference=send_message.MessageReference(message_id=ref_msg_idx)
                if ref_msg_idx
                else None,
                msg_seq=tool_scene.run_count if ref_msg_idx else None,
            ),
        )
        log.debug(f"发送消息返回: {return_data}")
        return_mesage = f"发送消息成功: 消息id={return_data.id}, 消息索引={return_data.ext_info.ref_idx}"
        return return_mesage

    async def delete_message_tool_call(self, tool_args: DeleteMessageToolParam):
        bot = self.bot
        await bot.qq_api.delete_message(
            api_type.ApiType.GROUP,
            open_id=self.group_openid,
            message_id=tool_args.message_id,
        )
        return "删除消息成功"

    async def ask_ai_tool_call(self, tool_args: subagent_utils.AskAIToolParam):
        subagent = subagent_utils.SubAgent(
            ai_plugin=self, agent_name=tool_args.agent_name
        )
        return await subagent.ask_ai_tools(tool_args)

    async def get_ai_chat_manager(self):
        if self.ai_chat_manager is None:
            bot_info = await self.bot.qq_api.get_bot_info()
            group_info = await self.bot.qq_api.get_group_info(self.group_openid)
            system_message_content = SystemPrompt.format(
                BOT_NICKNAME=bot_info.username,
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
            tools.extend(
                [
                    tool_calls_utils.Tool(
                        name="delete_message",
                        description="撤回一条自己已经发送的消息",
                        model=DeleteMessageToolParam,
                        function=self.delete_message_tool_call,
                    ),
                    tool_calls_utils.Tool(
                        name="ask_ai",
                        description="向AI提问，用于处理短时间无法直接回答的问题，可以用于深度研究等多的用途，作为异步函数调用，返回AI的回答",
                        model=subagent_utils.AskAIToolParam,
                        function=self.ask_ai_tool_call,
                    ),
                ]
            )
            self.ai_chat_manager = ai_utils.AiChatManager(
                system_message_content,
                tool_calls=tools,
                name=f"AIPlugin-{group_info.group_name}",
            )
        return self.ai_chat_manager

    async def generate_message(self, event_data: qq_message.Message):
        ai_memory_content = await ai_memory.search_memory(
            f"[{event_data.author.username}] [{event_data.author.id}] {event_data.content}",
            group_open_id=self.group_openid,
            # user_open_id=event_data.author.union_openid,
            filter_object_ids=self.load_memory_id_list,  # 传入已加载的记忆ID列表，避免重复加载
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

        mentions = getattr(event_data, "mentions", None)
        if mentions:
            for mention in mentions:
                if mention.id == (await self.bot.qq_api.get_bot_info()).union_openid:
                    message_type_flag.append("被@")

        matched_message = (
            "\n".join(memory.model_dump_json() for memory in ai_memory_content)
            if ai_memory_content
            else "无"
        )

        message_sticker_result = message_sticker.extract_faceType_tags(
            event_data.content
        )

        message_sticker_result_str = "\n".join(
            [
                f"{sticker.raw}: {sticker.encoded_ext}"
                for sticker in message_sticker_result
            ]
        )
        messages_content_str = f"""[{event_data.timestamp}][{
            getattr(event_data.author, "member_nickname", "未知")
        }({event_data.author.username})]({event_data.author.id})[{
            event_data.message_type.name
        }]{message_type_flag}: {event_data.content}
[{"]\n[".join(message_metadata)}]

## 命中的记忆内容
{matched_message}

## 消息中的表情转换结果
{message_sticker_result_str if message_sticker_result else "无"}
"""
        messages_content: list[ChatCompletionContentPartParam] = [
            ai_utils.make_text_content(messages_content_str)
        ]
        if event_data.attachments:
            for attachment in event_data.attachments:
                # if attachment.asr_refer_text:
                #     event_data.content += f"\n[语音转文字]: {attachment.asr_refer_text}"
                if attachment.content_type.startswith("image"):
                    log.debug(f"处理图片消息: {attachment}")
                    messages_content.append(
                        await get_image_from_url(attachment.url, attachment.filename)
                    )

                elif attachment.content_type.startswith("voice"):
                    if attachment.asr_refer_text:
                        messages_content.append(
                            ai_utils.make_text_content(
                                f"[语音转文字]: {attachment.asr_refer_text}",
                            )
                        )
                    else:
                        messages_content.append(
                            ai_utils.make_text_content(
                                "[语音消息]: 无法识别语音内容",
                            )
                        )

        messages: list[ChatCompletionMessageParam] = [
            ai_utils.make_user_message(messages_content),
        ]

        return messages

    async def handle_ai(
        self,
        event_datas: Iterable[qq_message.Message | AiRawMessages],
    ):
        messages: list[ChatCompletionMessageParam] = []
        for event_data in event_datas:
            if isinstance(event_data, qq_message.GroupMessage):
                messages.extend(await self.generate_message(event_data))
            elif isinstance(event_data, AiRawMessages):
                messages.append(event_data.content)
            else:
                log.warning(f"未知的消息类型: {type(event_data)}，跳过处理。")
                continue

        # pylance 还没支持这种写法，到时候看看
        # messages = [*(await self.generate_message(event_data)) for event_data in event_datas]

        ai_chat_manager = await self.get_ai_chat_manager()
        return await ai_chat_manager.handle_ai(messages)

    async def worker(self):
        log.debug(f"启动AI插件工作线程，处理群聊 {self.group_openid} 的消息。")
        while True:
            event_datas = [await self.group_message_queue.get()]
            try:
                while True:
                    event_datas.append(self.group_message_queue.get_nowait())
            except asyncio.QueueEmpty:
                pass
            log.debug(
                f"群聊 {self.group_openid} 在上次处理期间收到 {len(event_datas)} 条消息，开始处理AI请求。"
            )
            try:
                await self.handle_ai(event_datas)
            except Exception:  # noqa: BLE001
                log.exception("AI 插件处理消息时发生异常")
            finally:
                for _ in event_datas:
                    self.group_message_queue.task_done()

    async def handle_message(self, event_data: qq_message.GroupMessage | AiRawMessages):
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
async def chat_black_list_command(event_data: qq_message.Message, bot: QQ_Bot):
    if isinstance(event_data, qq_message.GroupMessage):
        await bot.qq_api.send_group_message(
            event_data.group_openid,
            send_message.GroupMessage(content=f"当前聊天黑名单: {GROUP_ID_BLACKLIST}"),
        )


@plugin.on_command(("chat_clear", "重置上下文"), "重置上下文", "清除当前群聊的上下文")
async def clear_command(event_data: qq_message.Message, bot: QQ_Bot):
    if isinstance(event_data, qq_message.GroupMessage):
        await (
            await AIPlugin.get_group_worker(bot, event_data.group_openid)
        ).clear_messages()
        await bot.qq_api.send_group_message(
            event_data.group_openid,
            send_message.GroupMessage(content="清理当前群聊的上下文成功"),
        )
