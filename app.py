from AGbot import cilent, config, plugin
import asyncio
from plugins import about, commend, mhy

config.管理员QQ号 = [1176503930, 2130812665]
config.机器人QQ号 = 1176503930
config.群聊白名单 = [860769764, 463566277, 959593907, 925603600]


plugin.bot.加载插件(about.bot)
plugin.bot.加载插件(commend.bot)
plugin.bot.加载插件(mhy.bot)


asyncio.run(cilent.run())
