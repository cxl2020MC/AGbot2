from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api

bot = plugin.Plugin("命令")

@bot.命令("命令", ["/commend", "/命令"])
async def commend(消息, data, ws):
    log.info("收到命令")
    await api.发送群消息(ws, data.get("group_id"), f"""识别命令为: {bot.解析命令(消息)}""")