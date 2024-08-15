from AGbot import plugin
from AGbot.log import logger as log

bot = plugin.plugin("关于")

@bot.命令("关于", ["/about"])
async def about(self, data, ws):
    log.info("收到关于命令")
    return 
    await api(f"""AGbot2""")