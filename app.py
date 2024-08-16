from AGbot import AGbot
import asyncio
from plugins import about, commend

app = AGbot.App()
app.插件.加载插件(about.bot)
app.插件.加载插件(commend.bot)

asyncio.run(app.run())