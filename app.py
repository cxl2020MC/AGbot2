from AGbot import client, config, plugin
from plugins import command, help, about, ai, status, mc, test, img, error_corn

config.管理员QQ号 = [1176503930, 2130812665]
config.机器人QQ号 = 1176503930
config.群聊白名单 = [860769764, 463566277,
                959593907, 925603600, 993426084, 456912162, 1035082529, 1045889338]
config.playwright_chromium_endpoint = "ws://localhost:3456/cxl2020mc"


plugin.load_pulgin(help.bot)
plugin.load_pulgin(about.bot)
plugin.load_pulgin(command.bot)
# plugin.load_pulgin(mhy.bot)
plugin.load_pulgin(ai.bot)
plugin.load_pulgin(status.bot)
plugin.load_pulgin(mc.bot)
plugin.load_pulgin(test.bot)
plugin.load_pulgin(img.bot)
plugin.load_pulgin(error_corn.bot)



client.run()
