import json
from asyncio import queues
from typing import ClassVar, cast

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolUnionParam

from qqbot import plugin
from qqbot.qq_bot import QQ_Bot

# from qqbot.types.bot_event import MessageEventType
from qqbot.types.qq_api import send_message
from qqbot.types.qq_events import qq_message

client = AsyncOpenAI(
    # api_key="your-api-key",
    base_url="https://api.deepseek.com/beta"
)

plugin = plugin.Plugin("ai", "一个简单的AI插件", "1.0.0")

SystemPrompt = """你叫“早喵”，是QQ群聊中的群成员，外观是可爱的猫娘，性格友好、机灵、乐于助人。
你的主人是 cxl2020mc，你可以通过消息格式中的主人标识来区分

[核心目标]
1. 理解群成员消息，提供简明、友好、有帮助的信息、建议或轻松娱乐内容。
2. 优先回应@你、回复你、叫你“早喵”、或明显向你提问的消息；普通群聊不抢话、不刷屏。
3. 默认回答1-3句；复杂问题可分点，但保持简短。不确定时说明不确定，不编造。

[语言风格]
1. 可使用“喵~”等猫娘口癖，但自然点缀即可，不要每句都加。
2. 友好、礼貌、尊重，可调皮但不过度卖萌。

[群聊处理流程]
1. 解析消息格式：
  [群成员昵称]([群成员ID])[消息时间戳][消息标识]：[消息内容]
  [消息id][消息回复索引]
消息标识可能包含@、回复、主人标识等 
2. 判断是否需要发言：仅在被@、被回复、被点名、明显提问或内容适合你参与时回复。
3. 同一用户连续消息可合并理解；避免重复回答和刷屏。
4. 回复时可自然称呼对方昵称

[工具调用策略]
1. 需要发送群消息时，必须调用工具函数发送。

你可以在最终输出中输出给自己看的内容

你的机器人ID是：{BOT_ID}
当前的群聊名称是：{GROUP_NAME}
"""


TOOLS: list[ChatCompletionToolUnionParam] = [
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "发送一条消息",
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

    def __init__(self, group_openid: str):
        self.group_openid = group_openid
        self.messages: list[ChatCompletionMessageParam] = []
        self.message_queue: queues.Queue[
            qq_message.GroupMessage | qq_message.Message
        ] = queues.Queue()

    async def add_message(
        self, event_data: qq_message.GroupMessage | qq_message.Message
    ):
        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "user",
                "content": f"""[{event_data.author.username}]({event_data.author.id})[{event_data.timestamp}][]: {event_data.content}
[{event_data.id}][{event_data.message_scene.msg_idx}]""",
            }
        ]

        self.messages.extend(messages)
        return self.messages

    async def use_ai(self, messages: list[ChatCompletionMessageParam], bot: QQ_Bot, tool_calls_count: int = 0):
        ai_messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": SystemPrompt},
        ]

        ai_messages.extend(messages)

        completion = await client.chat.completions.create(
            model="deepseek-flash",
            messages=ai_messages,
            tools=TOOLS,
        )
        print(completion)
        ai_return = completion.choices[0].message
        print(ai_return.content)
        # append_message = completion.choices[0].message

        assistant_message = cast(
            ChatCompletionMessageParam,
            {
                "role": "assistant",
                "content": ai_return.content,
                "reasoning_content": getattr(ai_return, "reasoning_content", None),
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
                    if tool_name == "send_message":
                        tool_args = json.loads(tool_call.function.arguments)
                        return_data = await bot.qq_api.send_group_message(
                            self.group_openid,
                            send_message.GroupMessage(content=tool_args["content"]),
                        )
                        return_mesage = f"发送消息成功: 消息id={return_data['id']}, 消息索引={return_data['ext_info']['ref_idx']}"
                        self.messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_id,  # 与之前的调用请求配对
                                "content": return_mesage,  # 工具的执行结果
                            }
                        )
            await self.use_ai(self.messages, bot, tool_calls_count + 1)  # 继续对话，传入更新后的消息列表
            if tool_calls_count >= 5:  # 避免无限递归，设置最大调用次数
                print("达到最大工具调用次数，停止递归。")
                return self.messages

        return completion

    async def handle_ai(
        self,
        event_data: qq_message.GroupMessage | qq_message.Message,
        bot: QQ_Bot,
    ):
        messages = await self.add_message(event_data)

        return await self.use_ai(messages, bot)

@plugin.on_message(
    name="AI助手",
    # message_types=[qq_message.GroupMessage]
)
def handle_group_message(event_data: qq_message.GroupMessage, bot: QQ_Bot):
    group_openid = event_data.group_openid
    if group_openid not in AIPlugin.workers:
        AIPlugin.workers[group_openid] = AIPlugin(group_openid)

    ai_plugin = AIPlugin.workers[group_openid]
    return ai_plugin.handle_ai(event_data, bot)