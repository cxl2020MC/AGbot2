from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
import jinja2

bot = plugin.Plugin("帮助")

@bot.command("帮助", ["help"])
async def 帮助(消息, data):
    plugin_list = plugin.Plugin.plugin_list
    log.debug(f"plugin_list: {plugin_list}")
    模板 = jinja2.Template("""帮助：{% for 插件 in 插件列表 %}{% for 命令 in 插件.command_list %}
    {{ 命令["命令名称"] }}: {{ 命令["command_list"] }}{% endfor %}{% endfor %}""")
    消息内容 = 模板.render(插件列表=plugin_list)
    await api.send_message(data, 消息内容)
