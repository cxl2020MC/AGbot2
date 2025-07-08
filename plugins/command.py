from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot import command_tools
from AGbot.event import MessageEvent

import aiohttp
import time
# import tcping
import ping3
import os
import sys


bot = plugin.Plugin("命令")

@bot.command("命令", ["command", "命令"])
async def command(event: MessageEvent):
    log.info("收到命令")
    await api.send_message(event, f"""识别命令为: {bot.解析命令(event.message)}""")

@bot.command("抛出错误", ["error"])
async def error(event: MessageEvent):
    raise Exception("这是个主动抛出的错误")

@bot.command("http test", ["http-test"])
async def http_test(event: MessageEvent):
    命令 = bot.解析命令(event.message)
    url = 命令["参数列表"][0]
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            log.info(f"HTTP请求耗时: {time.time() - start_time}s")
            await api.send_message(event, f"HTTP请求耗时: {time.time() - start_time}s")

@bot.command("ping", ["ping"])
async def tcp_ping_func(event: MessageEvent):
    命令 = command_tools.Command(event.message)
    url = 命令.get_arg(0)
    # port = 命令["参数字典"].get("port", 443)
    # ping = tcping.Ping(url, port, 5)
    # ping.ping(4)
    # result = ping.result.raw
    if url is None:
        await api.send_message(event, "请输入要ping的地址")
        return
    results = []
    for i in range(4):
        result = ping3.ping(url)
        if result is None:
            result = "超时"
        elif result is False:
            result = "未知的主机名"
        else:
            result = f"{result*1000:.2f}ms"
        results.append(result)

    result = f"""正在ping {url}:
    {results[0]}
    {results[1]}
    {results[2]}
    {results[3]}"""
    await api.send_message(event, result)

@bot.command("重启", ["restart"])
async def stop(event: MessageEvent):
    log.info("收到重启命令，尝试停止")
    await api.send_message(event, f"正在尝试重启,请稍后")
    sys.exit(0)
    os._exit(0)

