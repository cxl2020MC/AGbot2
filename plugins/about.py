from AGbot import plugin
from AGbot.log import logger as log

bot = plugin.plugin("关于")

@bot.命令("关于", ["/about"])
async def about(self, data, ws):
    log.info("收到关于命令")

    await api.发送群消息(f"""关于AGbot2
版本: 1.0
作者: cxl2020mc""")