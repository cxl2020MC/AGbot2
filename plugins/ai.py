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

ai_white_list = [1035082529]

system_format = """你的名字叫做早喵，是一只猫娘，你的主人/开发者是: 陈鑫磊 (1176503930) ，你的任务是和群友聊天。
我会提供消息发送者的名字，QQ号以及消息id，你可以使用携带了cqcode的消息进行回复。
你当前处于的群聊为： {group_name}
你的QQ号为: {self_id}
如果消息没有回复价值，你可以说不回复"""

chat_history = {}


def add_chat_history(group_id, message: dict) -> list:
    if group_id not in chat_history:
        chat_history[group_id] = []
    chat_history[group_id].append(message)
    if len(chat_history[group_id]) > 10:
        chat_history[group_id].pop(0)
    return chat_history[group_id]

# @bot.on_message("group")
async def ai(event: GroupMessageEvent):
    group_id = event.group_id
    if group_id not in chat_history:
        chat_history[group_id] = []
    message2 = event.raw_message[4:]
    raw_message2 = ''.join(message2)
    log.info(raw_message2)
    message = {'role': 'user', 'content': raw_message2}
    chat_history[group_id].append(message)

    response = await client.chat.completions.create(
        model="glm-4.5-flash",
        messages=chat_history[group_id],
        stream=False
    )

    log.debug(response)
    log.debug(chat_history)
    content = response.choices[0].message.content
    log.info(content)
    chat_history[group_id].append(response.choices[0])
    await api.send_message(event, content)

@bot.command("ai", ["ai"])
async def ai2(event: GroupMessageEvent):
    raw_message = event.raw_message[4:]
    log.info(raw_message)
    message = {'role': 'user', 'content': f"{event.sender_card} ({event.user_id}): {raw_message} [{event.message_id}]"}
    
    messages = add_chat_history(event.group_id, message)
    messages.insert(0, {'role': 'system', 'content': system_format.format(group_name=await event.group_name, self_id=event.self_id)})

    log.debug(messages)
    response = await client.chat.completions.create(
        model="glm-4.5-flash",
        messages=messages,
        stream=False
    )
    log.debug(response)
    await api.send_message(event, response.choices[0].message.content)

@bot.command("清理AI聊天记录", ["clean"])
async def clean_history(event: GroupMessageEvent):
    chat_history.clear()
    await api.send_message(event, "AI聊天记录已清理")
