from AGbot import client, config, plugin
from plugins import help, about, commend, mhy, ai

config.管理员QQ号 = [1176503930, 2130812665]
config.机器人QQ号 = 1176503930
config.群聊白名单 = [860769764, 463566277,
                959593907, 925603600, 993426084, 456912162]


plugin.load_pulgin(help.bot)
plugin.load_pulgin(about.bot)
plugin.load_pulgin(commend.bot)
plugin.load_pulgin(mhy.bot)
plugin.load_pulgin(ai.bot)


client.run()
