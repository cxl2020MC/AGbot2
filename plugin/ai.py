from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

from qqbot import plugin
from qqbot.qq_bot import QQ_Bot

# from qqbot.types.bot_event import MessageEventType
from qqbot.types.qq_api import send_message
from qqbot.types.qq_events import qq_message

client = AsyncOpenAI(
    # api_key="your-api-key",
    base_url="https://api.deepseek.com"
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
  [群成员昵称]([群成员ID])[消息时间戳][消息id][消息标识]：[消息内容]
消息标识可能包含@、回复、主人标识等 
2. 判断是否需要发言：仅在被@、被回复、被点名、明显提问或内容适合你参与时回复。
3. 同一用户连续消息可合并理解；避免重复回答和刷屏。
4. 回复时可自然称呼对方昵称

[工具调用策略]
1. 需要发送群消息时，必须调用工具函数发送。

你可以在最终输出中输出给自己看的内容

你的机器人ID是：{BOT_ID}
"""

TOOLS = {
    "name": "send_message",
    "description": "发送一条消息",
    "parameters": {
        "type": "object",
        "properties": {"message": {"type": "string", "description": "需要发送的消息"}},
        "required": ["message"],
    },
}


async def use_ai(messages: list[ChatCompletionMessageParam]):
    ai_messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": SystemPrompt},
    ]

    ai_messages.extend(messages)

    completion = await client.chat.completions.create(
        model="deepseek-flash",
        messages=ai_messages,
    )

    print(completion.choices[0].message.content)


async def handle_ai(
    event_data: qq_message.GroupMessage | qq_message.Message,
    bot: QQ_Bot,
):
    pass
