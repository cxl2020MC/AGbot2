from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
import jinja2

bot = plugin.Plugin("帮助")

@bot.命令("帮助", ["/help"])
async def 帮助(消息, data):
    插件列表 = plugin.插件列表
    log.debug(f"插件列表: {插件列表}")
    模板 = jinja2.Template("""帮助：{% for plugin in plugins %}{% for 命令 in plugin.命令列表 %}
    {{ 命令["命令名称"] }}: {{ 命令["命令列表"] }}{% endfor %}{% endfor %}""")
    消息内容 = 模板.render(plugins=插件列表)
    await api.发送消息(data, 消息内容)


