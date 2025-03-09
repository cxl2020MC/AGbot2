from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api

import os
from openai import AsyncOpenAI

bot = plugin.Plugin("AI")

deepseekApi_key = os.getenv("DS_API_KEY")

client = AsyncOpenAI(api_key=deepseekApi_key, base_url="https://api.deepseek.com")

chat_history = {}


@bot.command("AI", ["ai"])
async def ai(消息, data):
    group_id = data.get("group_id")
    if group_id not in chat_history:
        chat_history[group_id] = []
    message2 = 消息[4:]
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
    await api.send_message(data, content)

@bot.command("清理AI聊天记录", ["clean"])
async def clean_history(消息, data):
    chat_history.clear()
    await api.send_message(data, "AI聊天记录已清理")
