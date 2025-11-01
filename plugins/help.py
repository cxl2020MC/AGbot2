from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot.types.message_event import MessageEvent


bot = plugin.Plugin("帮助")

@bot.command("帮助", ["help"])
async def 帮助(event: MessageEvent):
    plugin_list = plugin.Plugin.plugin_list
    log.debug(f"plugin_list: {plugin_list}")
    消息内容 = "命令帮助：\n"
    for 插件 in plugin_list:
        消息内容 += f"{插件.name}:\n"
        for 命令 in 插件.command_list:
            消息内容 += f'    {命令["命令名称"]}: {", ".join(命令["command_list"])}\n'

    await api.send_message(event, 消息内容)
