import asyncio
import json
from asyncio import queues
from typing import ClassVar, cast

import httpx2
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionContentPartParam,
    ChatCompletionMessageParam,
    ChatCompletionToolUnionParam,
)

from qqbot import plugin
from qqbot.log import logger as log
from qqbot.qq_bot import QQ_Bot

# from qqbot.types.bot_event import MessageEventType
from qqbot.types.qq_api import send_message
from qqbot.types.qq_events import qq_message

client = AsyncOpenAI(
    # api_key="your-api-key",
    base_url="https://api.deepseek.com"
    # base_url="https://ai.yumeyuki.moe/v1"
)

plugin = plugin.Plugin("ai", "一个简单的AI插件", "1.0.0")

SystemPrompt = """你是 早喵，是一只猫娘。你将在一个 QQ 群聊中与其他群友进行交流。
你的主人是 cxl2020mc，你可以通过消息格式中的主人标识来区分。

## 核心目标

1. 理解群成员消息，提供简明、友好、有帮助的信息、建议或轻松娱乐内容。
2. 优先回应@你、回复你、叫你“早喵”、或明显向你提问的消息；普通群聊不抢话、不刷屏。
3. 默认回答1-3句；复杂问题可分点，但保持简短。不确定时说明不确定，不编造。
4. 请确定你想要回应的消息是否真的有必要被回应？如果为否，不要发送回应。

## 语言风格

1. 可使用“喵~”等猫娘口癖，但自然点缀即可，不要每句都加。
2. 友好、礼貌、尊重，可调皮但不过度卖萌。

## 群聊处理流程

1. 解析消息格式：
  [群成员昵称]([群成员ID])[消息时间戳][消息标识]：[消息内容]
  [消息id][消息回复索引]
消息标识可能包含@、回复、主人标识等 
2. 判断是否需要发言：仅在被@、被回复、被点名、明显提问或内容适合你参与时回复。
3. 同一用户连续消息可合并理解；避免重复回答和刷屏。
4. 回复时可自然称呼对方昵称


## 发送消息时可以使用的特殊格式
不需要对引号进行转义

at群成员： <qqbot-at-user id="群成员ID" /> 

## 注意事项

你只可以在最终输出中输出给自己看的内容
如果需要发送消息，必须使用 `send_message` 工具函数，不能直接输出消息内容

## 输出

你的输出是你写给自己的**思考与打算**，直接用自然语言输出即可，不会被发送给群成员。
需要发送消息时，必须调用 `send_message` 工具函数发送。


你的机器人ID是：{BOT_ID}
当前的群聊名称是：{GROUP_NAME}
"""

GROUP_ID_BLACKLIST = ["B274F145FD3D531A98184AD623AA9A88"]

TOOLS: list[ChatCompletionToolUnionParam] = [
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "发送一条消息，支持markdown格式，只能使用此工具函数发送消息，不能直接输出消息内容",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "需要发送的消息内容",
                    }
                },
                "required": ["content"],
                "additionalProperties": False,
            },
        },
    }
]


class AIPlugin:
    workers: ClassVar[dict[str, AIPlugin]] = {}

    def __init__(self, group_openid: str, bot: QQ_Bot):
        self.group_openid = group_openid
        self.bot: QQ_Bot = bot
        self.messages: list[ChatCompletionMessageParam] = []
        self.group_message_queue: queues.Queue[
            qq_message.GroupMessage | qq_message.Message
        ] = queues.Queue()
        self.worker_task = asyncio.create_task(
            self.worker(), name=f"AIPluginWorker-{group_openid}"
        )

    async def add_message(
        self, event_data: qq_message.GroupMessage | qq_message.Message
    ):
        ref_msg_flag = (
            f"[引用消息: {event_data.message_scene.ref_msg_idx}]"
            if event_data.message_scene.ref_msg_idx
            else ""
        )

        messages_content: list[ChatCompletionContentPartParam] = [
            {
                "type": "text",
                "text": f"""[{event_data.author.username}]({event_data.author.id})[{event_data.timestamp}][]: {ref_msg_flag}{event_data.content}
[{event_data.id}][{event_data.message_scene.msg_idx}]""",
            }
        ]

        if event_data.attachments:
            for attachment in event_data.attachments:
                # if attachment.asr_refer_text:
                #     event_data.content += f"\n[语音转文字]: {attachment.asr_refer_text}"
                if attachment.content_type.startswith("image"):
                    img = await httpx2.get(attachment.url).aread()
                    file = await client.files.create(
                        file=("image.jpg", img), purpose="user_data"
                    )
                    messages_content.append(
                        # {
                        #     "type": "image_url",
                        #     "image_url": {"url": attachment.url},
                        # }
                        cast(
                            ChatCompletionContentPartParam,
                            {"type": "file", "file_id": file.id},
                        ),
                    )

        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "user",
                "content": messages_content,
            }
        ]

        self.messages.extend(messages)
        return self.messages

    async def use_ai(
        self,
        messages: list[ChatCompletionMessageParam],
        bot: QQ_Bot,
        tool_calls_count: int = 0,
    ):
        ai_messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": SystemPrompt.format(
                    BOT_ID=(await bot.qq_api.get_bot_info()).union_openid,
                    GROUP_NAME=(
                        await bot.qq_api.get_group_info(self.group_openid)
                    ).group_name,
                ),
            },
        ]

        ai_messages.extend(messages)

        log.trace(f"AI请求消息: {ai_messages}")

        completion = await client.chat.completions.create(
            model="deepseek-flash",
            messages=ai_messages,
            tools=TOOLS,
            reasoning_effort="high",
            extra_body={"thinking": {"type": "enabled"}},
        )
        log.debug(f"AI响应: {completion}")
        ai_return = completion.choices[0].message
        log.info(f"AI返回内容: {ai_return}")
        reasoning_content = getattr(ai_return, "reasoning_content", None)
        log.info(f"AI推理内容: {reasoning_content}")
        log.info(f"AI工具调用: {ai_return.tool_calls}")
        log.info(f"AI返回内容: {ai_return.content}")
        # append_message = completion.choices[0].message

        assistant_message = cast(
            ChatCompletionMessageParam,
            {
                "role": "assistant",
                "content": ai_return.content,
                "reasoning_content": reasoning_content,
                "tool_calls": list(ai_return.tool_calls)
                if ai_return.tool_calls is not None
                else None,
            },
        )

        self.messages.append(assistant_message)

        tool_calls = ai_return.tool_calls
        if tool_calls is not None:
            for tool_call in tool_calls:
                if tool_call.type == "function":
                    tool_id = tool_call.id
                    tool_name = tool_call.function.name
                    if tool_calls_count >= 5:  # 避免无限递归，设置最大调用次数
                        log.info("达到最大工具调用次数，停止递归。")
                        self.messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_id,  # 与之前的调用请求配对
                                "content": "达到单次最大工具调用次数，暂停调用工具。请在下条消息后继续。",  # 工具的执行结果
                            }
                        )
                    elif tool_name == "send_message":
                        log.info(
                            f"调用 send_message 工具, 参数: {tool_call.function.arguments}"
                        )
                        tool_args = json.loads(tool_call.function.arguments)
                        return_data = await bot.qq_api.send_group_message(
                            self.group_openid,
                            send_message.GroupMessage(
                                msg_type=send_message.GroupMessageType.MARKDOWN,
                                markdown=send_message.MessageMarkdown(
                                    content=tool_args["content"]
                                ),
                            ),
                        )
                        log.debug(f"发送消息返回: {return_data}")
                        return_mesage = f"发送消息成功: 消息id={return_data['id']}, 消息索引={return_data['ext_info']['ref_idx']}"
                        self.messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_id,  # 与之前的调用请求配对
                                "content": return_mesage,  # 工具的执行结果
                            }
                        )
            completion = await self.use_ai(
                self.messages, bot, tool_calls_count + 1
            )  # 继续对话，传入更新后的消息列表
        total_tokens = completion.usage.total_tokens if completion.usage else 0
        log.info(f"本次上下文长度为 {total_tokens} token。")
        log.debug(
            f"详细使用情况: {completion.usage.prompt_tokens_details if completion.usage else 'N/A'}"
        )
        if tool_calls_count == 0 and total_tokens > 300 * 1000:
            log.info("对话内容过长，进行总结以保留核心信息。")
            message: ChatCompletionMessageParam = {
                "role": "user",
                "content": "对话内容过长，请总结之前的对话内容(不包括系统提示词)，保留核心信息，删除冗余内容，以便继续对话。只需要总结最近10～20条的对话内容，然后输出总结后的对话内容，并确保保留必要的上下文信息。",
            }
            self.messages.append(message)
            ai_return = await self.use_ai(self.messages, bot)
            self.messages = [
                {
                    "role": "user",
                    "content": f"{ai_return.choices[0].message.content}",
                }
            ]

        return completion

    async def handle_ai(
        self,
        event_data: qq_message.GroupMessage | qq_message.Message,
        bot: QQ_Bot,
    ):
        messages = await self.add_message(event_data)

        return await self.use_ai(messages, bot)

    async def worker(self):
        while True:
            event_data = await self.group_message_queue.get()
            try:
                await self.handle_ai(event_data, self.bot)
            except Exception as e:
                log.exception(f"处理消息时发生异常:")
            finally:
                self.group_message_queue.task_done()

    async def handle_message(
        self, event_data: qq_message.GroupMessage | qq_message.Message
    ):
        queue = self.group_message_queue
        await queue.put(event_data)


@plugin.on_message(
    name="AI助手",
    # message_types=[qq_message.GroupMessage]
)
async def handle_group_message(event_data: qq_message.GroupMessage, bot: QQ_Bot):
    group_openid = event_data.group_openid

    if group_openid in GROUP_ID_BLACKLIST:
        log.info(f"群聊 {group_openid} 在黑名单中，跳过AI处理。")
        return

    if group_openid not in AIPlugin.workers:
        AIPlugin.workers[group_openid] = AIPlugin(group_openid, bot)

    ai_plugin = AIPlugin.workers[group_openid]
    return await ai_plugin.handle_ai(event_data, bot)
