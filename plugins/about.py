from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api

bot = plugin.Plugin("关于")

@bot.命令("关于", ["/about", "/关于"])
async def about(消息, data):
    log.info("收到关于命令")

    await api.发送群消息(data.get("group_id"), f"""关于AGbot2
版本: 1.0-dev
作者: cxl2020mc
开源地址: https://github.com/cxl2020MC/AGbot2""")