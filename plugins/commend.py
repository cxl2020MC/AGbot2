from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
import aiohttp
import time
import tcping
import os
import sys
from ollama import AsyncClient

bot = plugin.Plugin("命令")

@bot.command("命令", ["/commend", "/命令"])
async def commend(消息, data):
    log.info("收到命令")
    await api.send_message(data, f"""识别命令为: {bot.解析命令(消息)}""")

@bot.command("抛出错误", ["/error"])
async def error(消息, data):
    raise Exception("这是个主动抛出的错误")

@bot.command("http test", ["/http-test"])
async def http_test(消息, data):
    命令 = bot.解析命令(消息)
    url = 命令["参数列表"][0]
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            log.info(f"HTTP请求耗时: {time.time() - start_time}s")
            await api.send_message(data, f"HTTP请求耗时: {time.time() - start_time}s")

@bot.command("ping", ["/ping"])
async def tcp_ping_func(消息, data):
    命令 = bot.解析命令(消息)
    url = 命令["参数列表"][0]
    port = 命令["参数字典"].get("port", 443)
    ping = tcping.Ping(url, port, 5)
    ping.ping(4)
    result = ping.result.raw
    await api.send_message(data, result)

@bot.command("重启", ["/restart"])
async def stop(消息, data):
    log.info("收到重启命令，尝试停止")
    await api.send_message(data, f"正在尝试重启,请稍后")
    sys.exit(0)
    os._exit(0)

ollama_history = []

@bot.command("AI", ["/ai"])
async def ai(消息, data):
    message2 = 消息[4:]
    raw_message2 = ''.join(message2)
    log.info(raw_message2)
    message = {'role': 'user', 'content': raw_message2}
    ollama_history.append(message)
    response = await AsyncClient().chat(model='qwen2:0.5b', messages=ollama_history)
    log.info(response)
    log.debug(ollama_history)
    ollama_history.append(dict(response["message"]))
    await api.send_message(data, response["message"]["content"])