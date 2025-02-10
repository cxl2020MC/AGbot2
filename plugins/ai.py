from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api

from ollama import AsyncClient

bot = plugin.Plugin("AI")

ollama_history = {}

@bot.command("AI", ["ai"])
async def ai(消息, data):
    group_id = data.get("group_id")
    if group_id not in ollama_history:
        ollama_history[group_id] = []
    message2 = 消息[4:]
    raw_message2 = ''.join(message2)
    log.info(raw_message2)
    message = {'role': 'user', 'content': raw_message2}
    ollama_history[group_id].append(message)
    response = await AsyncClient().chat(model='deepseek-r1:1.5b', messages=ollama_history[group_id])
    log.info(response)
    log.debug(ollama_history)
    ollama_history[group_id].append(dict(response["message"]))
    await api.send_message(data, response["message"]["content"])

@bot.command("清理AI聊天记录", ["clean"])
async def clean_history(消息, data):
    ollama_history.clear()
    await api.send_message(data, "AI聊天记录已清理")
    