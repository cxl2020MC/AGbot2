from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot import config
from AGbot.event import MessageEvent

import mcstatus
import aiofiles
import json

bot = plugin.Plugin("MC服务器")


@bot.command("MC", ["mc", "查服"])
async def about(event: MessageEvent):
    log.info("收到mc命令")
    if not event.command_text:
        return
    服务器地址 = event.command_text.split(" ")[1]
    
    服务器 = await mcstatus.JavaServer.async_lookup(服务器地址)
    延迟 = await 服务器.async_ping()
    状态 = await 服务器.async_status()
    log.debug(状态)
    # 查询 = await 服务器.async_query()
    if 状态.players.sample:
        当前在线 = [玩家.name for 玩家 in 状态.players.sample]
    else:
        当前在线 = "无"

    await api.send_message(event, f"""服务器状态:
    地址: {服务器地址}
    版本: {状态.version.name}
    描述: {状态.motd.raw}
    延迟: {延迟:.2f}ms
    在线人数: {状态.players.online}/{状态.players.max}
    当前在线: {", ".join(当前在线)}
注: 匿名玩家可能为假人""")