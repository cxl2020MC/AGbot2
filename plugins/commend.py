from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
import aiohttp
import time
import tcping
import os

bot = plugin.Plugin("命令")

@bot.命令("命令", ["/commend", "/命令"])
async def commend(消息, data):
    log.info("收到命令")
    await api.发送群消息(data.get("group_id"), f"""识别命令为: {bot.解析命令(消息)}""")

@bot.命令("抛出错误", ["/error"])
async def error(消息, data):
    raise Exception("这是个主动抛出的错误")

@bot.命令("http test", ["/http-test"])
async def http_test(消息, data):
    命令 = bot.解析命令(消息)
    url = 命令["参数列表"][0]
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            log.info(f"HTTP请求耗时: {time.time() - start_time}s")
            await api.发送群消息(data.get("group_id"), f"HTTP请求耗时: {time.time() - start_time}s")

@bot.命令("ping", ["/ping"])
async def tcp_ping_func(消息, data):
    命令 = bot.解析命令(消息)
    url = 命令["参数列表"][0]
    ping = tcping.Ping(url, 443, 5)
    ping.ping(4)
    result = ping.result.raw
    await api.发送群消息(data.get("group_id"), result)

@bot.命令("/stop", ["/stop"])
async def stop(消息, data):
    log.info("收到停止命令，尝试停止")
    await api.发送群消息(data.get("group_id"), f"正在尝试停止,请稍后")
    os._exit(0)