from AGbot import client, config, plugin
from plugins import command, help, about, status, mc, test, img, error_corn, statistics, ai

config.ADMIN_QQ = [1176503930, 2130812665]
config.BOT_QQ = 1176503930
# config.群聊白名单 = [860769764, 463566277,
#                 959593907, 925603600, 993426084, 456912162, 1035082529, 1045889338]
config.PLAYWRIGHT_CHROMIUM_ENDPOINT = "ws://localhost:3456/cxl2020mc"


plugin.load_plugin(help.bot)
plugin.load_plugin(about.bot)
plugin.load_plugin(command.bot)
# plugin.load_plugin(mhy.bot)
plugin.load_plugin(ai.bot)
plugin.load_plugin(status.bot)
plugin.load_plugin(mc.bot)
plugin.load_plugin(test.bot)
plugin.load_plugin(img.bot)
plugin.load_plugin(error_corn.bot)
plugin.load_plugin(statistics.bot)