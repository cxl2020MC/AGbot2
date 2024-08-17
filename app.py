from AGbot import cilent, config, plugin
import asyncio
from plugins import about, commend

config.管理员QQ号  = [1176503930]
config.机器人QQ号 = 1176503930
config.群聊白名单 = [860769764, 463566277, 959593907]


plugin.bot.加载插件(about.bot)
plugin.bot.加载插件(commend.bot)

asyncio.run(cilent.run())