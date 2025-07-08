from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot.event import MessageEvent

bot = plugin.Plugin("关于")

@bot.command("关于", ["about", "关于"])
async def about(event: MessageEvent):
    log.info("收到关于命令")

    await api.send_message(event, f"""关于AGbot2
版本: 2.0.0-dev
作者: cxl2020mc
开源地址: https://github.com/cxl2020MC/AGbot2""")