from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot import command_utils
from AGbot.types.message_event import MessageEvent

import aiohttp
import time
# import tcping
import ping3
import os
import sys
import subprocess

bot = plugin.Plugin("命令")

@bot.command("命令", ["command", "命令"])
async def command_func(event: MessageEvent):
    log.info("收到命令")
    await api.send_message(event, f"""识别命令为: {bot.parse_command(event.raw_message)}""")

@bot.command("抛出错误", ["error"])
async def error_func(event: MessageEvent):
    raise Exception("这是个主动抛出的错误")

@bot.command("http test", ["http-test"])
async def http_test_func(event: MessageEvent):
    command_parsed = bot.parse_command(event.raw_message)
    url = command_parsed["参数列表"][0]
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            log.info(f"HTTP请求耗时: {time.time() - start_time}s")
            await api.send_message(event, f"HTTP请求耗时: {time.time() - start_time}s")

@bot.command("ping", ["ping"])
async def ping_func(event: MessageEvent):
    command_obj = command_utils.Command(event.raw_message)
    url = command_obj.get_arg(0)
    # port = command_parsed["参数字典"].get("port", 443)
    # ping = tcping.Ping(url, port, 5)
    # ping.ping(4)
    # result = ping.result.raw
    if url is None:
        await api.send_message(event, "请输入要ping的地址")
        return
    elif url in "|" or url in "&":
        await api.send_message(event, "请勿输入特殊字符")
        return
    
    result = subprocess.run(["ping", "-c", "4", url], capture_output=True, text=True)

    await api.send_message(event, result.stdout)

@bot.command("重启", ["restart"])
async def restart_func(event: MessageEvent):
    log.info("收到重启命令，尝试停止")
    await api.send_message(event, f"正在尝试重启,请稍后")
    sys.exit(0)
    os._exit(0)