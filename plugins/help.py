from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
import jinja2

bot = plugin.Plugin("帮助")

@bot.命令("帮助", ["/help"])
async def 帮助(消息, data):
    plugin_list = plugin.plugin_list
    log.debug(f"plugin_list: {plugin_list}")
    模板 = jinja2.Template("""帮助：{% for plugin in plugins %}{% for 命令 in plugin.command_list %}
    {{ 命令["命令名称"] }}: {{ 命令["command_list"] }}{% endfor %}{% endfor %}""")
    消息内容 = 模板.render(plugins=plugin_list)
    await api.send_message(data, 消息内容)
