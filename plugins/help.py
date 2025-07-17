from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot.event import MessageEvent

import jinja2

bot = plugin.Plugin("帮助")

@bot.command("帮助", ["help"])
async def 帮助(event: MessageEvent):
    plugin_list = plugin.Plugin.plugin_list
    log.debug(f"plugin_list: {plugin_list}")
    模板 = jinja2.Template("""帮助：
{% for 插件 in 插件列表 %}{{ 插件.name }}:
{% for 命令 in 插件.command_list %}
    {{ 命令["命令名称"] }}: {{ ", ".join(命令["command_list"]) }}{% endfor %}{% endfor %}""")
    消息内容 = 模板.render(插件列表=plugin_list)
    await api.send_message(event, 消息内容)
