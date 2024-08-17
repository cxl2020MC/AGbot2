from AGbot import AGbot, config
import asyncio
from plugins import about, commend

config.管理员QQ号  = [1176503930]
config.机器人QQ号 = 1176503930
config.群聊白名单 = [860769764]

app = AGbot.App()
app.插件.加载插件(about.bot)
app.插件.加载插件(commend.bot)

asyncio.run(app.run())