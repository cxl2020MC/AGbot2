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

chat_history = {}


@bot.on_message("group")
async def ai(event: GroupMessageEvent):
    if event.message_type == "private":
        return
    group_id = event.group_id
    if group_id not in chat_history:
        chat_history[group_id] = []
    message2 = event.raw_message[4:]
    raw_message2 = ''.join(message2)
    log.info(raw_message2)
    message = {'role': 'user', 'content': raw_message2}
    chat_history[group_id].append(message)

    response = await client.chat.completions.create(
        model="deepseek-chat",
        messages=chat_history[group_id],
        stream=False
    )

    log.debug(response)
    log.debug(chat_history)
    content = response.choices[0].message.content
    log.info(content)
    chat_history[group_id].append(response.choices[0])
    await api.send_message(event, content)


@bot.command("清理AI聊天记录", ["clean"])
async def clean_history(event: GroupMessageEvent):
    chat_history.clear()
    await api.send_message(event, "AI聊天记录已清理")
