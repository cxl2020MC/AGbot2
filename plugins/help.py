from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot.types.message_event import MessageEvent


bot = plugin.Plugin("帮助")

@bot.command("帮助", ["help"])
async def help_command(event: MessageEvent):
    plugin_list = plugin.Plugin.plugin_list
    log.debug(f"plugin_list: {plugin_list}")
    message_content = "命令帮助：\n"
    for plugin_item in plugin_list:
        message_content += f"{plugin_item.name}:\n"
        for command_item in plugin_item.command_list:
            message_content += f'    {command_item["命令名称"]}: {", ".join(command_item["command_list"])}\n'

    await api.send_message(event, message_content)