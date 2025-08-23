from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot.event import GroupMessageEvent


import os
from openai import AsyncOpenAI

bot = plugin.Plugin("AI")

Api_key = os.getenv("ZAI_API_KEY")

client = AsyncOpenAI(
    api_key=Api_key,
    base_url="https://open.bigmodel.cn/api/paas/v4/"
)

ai_white_list = [1035082529, 860769764]

system_format = """你的名字叫做早喵，是一只猫娘，你的主人/开发者是: 陈鑫磊 (1176503930) ，你的任务是和群友聊天。
我会提供消息发送者的名字，QQ号以及消息id，消息id我会用中括号括起来，你可以使用携带了cqcode的消息进行回复。
你当前处于的群聊为： {group_name}
你的QQ号为: {self_id}
回复价值是这个消息与你的相关性，如果这个消息和你无关，没有at和叫你名字那就是无关消息
你不用每条消息都回复，如果消息没有回复价值，或者与你无关，你可以说: 无需回复
"""

chat_history = {}


def add_chat_history(group_id, message: dict) -> list:
    if group_id not in chat_history:
        chat_history[group_id] = []
    chat_history[group_id].append(message)
    if len(chat_history[group_id]) > 10:
        chat_history[group_id].pop(0)
    return chat_history[group_id]


@bot.on_message("group")
async def ai(event: GroupMessageEvent):
    if event.group_id not in ai_white_list:
        return
    raw_message = event.raw_message
    message = {'role': 'user',
               'content': f"{event.get_username()} ({event.user_id}): {raw_message} [{event.message_id}]"}

    messages = add_chat_history(event.group_id, message).copy()
    log.debug(f"聊天记录: {messages}")
    messages.insert(0, {'role': 'system', 'content': system_format.format(group_name=await event.group_name, self_id=event.self_id)})

    # tools = [
    #     {
    #         "type": "function",
    #         "function": {
    #             "name": "send_message",
    #             "description": "发送消息，返回消息id",
    #             "parameters": {
    #                 "type": "object",
    #                 "properties": {
    #                     "message": {
    #                         "type": "string",
    #                         "description": "要发送的消息"
    #                     }
    #                 },
    #                 "required": ["message"]
    #             }
    #         }
    #     }
    # ]

    response = await client.chat.completions.create(
        model="glm-4.5-flash",
        messages=messages,
        # response_format={"type": "json_object"}
        stream=False,
    )
    log.debug(response)
    ai_message = {'role': 'assistant',
                  'content': response.choices[0].message.content}
    add_chat_history(event.group_id, ai_message)
    if "无需回复" in str(response.choices[0].message.content):
        return
    await api.send_message(event, response.choices[0].message.content)


@bot.command("清理AI聊天记录", ["clean"])
async def clean_history(event: GroupMessageEvent):
    chat_history.clear()
    await api.send_message(event, "AI聊天记录已清理")
