from AGbot import client, config, plugin
from plugins import help, about, commend, mhy

config.管理员QQ号 = [1176503930, 2130812665]
config.机器人QQ号 = 1176503930
config.群聊白名单 = [860769764, 463566277,
                959593907, 925603600, 993426084, 456912162]


plugin.加载插件(help.bot)
plugin.加载插件(about.bot)
plugin.加载插件(commend.bot)
plugin.加载插件(mhy.bot)


client.run()
