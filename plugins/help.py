from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
import jinja2

bot = plugin.Plugin("帮助")

@bot.命令("帮助", ["/help"])
async def 帮助(消息, data):
    插件列表 = plugin.插件列表
    log.debug("插件列表：", 插件列表)
    模板 = jinja2.Template("""帮助：
{% for plugin in plugins %}
{{ plugin.名称 }} :
    {% for 命令 in plugin.命令 %}
        {{ 命令.get("命令名称") }}
    {% endfor %}
{% endfor %}""")
    消息内容 = 模板.render(plugin=插件列表)
    await api.发送群消息(data.get("group_id"), 消息内容)
