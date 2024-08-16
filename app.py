from AGbot import AGbot
import asyncio
from plugins import about

app = AGbot.App()
app.插件.加载插件(about.bot)

asyncio.run(app.run())