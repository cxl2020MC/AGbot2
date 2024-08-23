from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from . import mhy_core
import jinja2

bot = plugin.Plugin("mhy")

@bot.命令("获取资讯", ["/获取资讯"])
async def 获取资讯(消息, data, ws):
    log.info("收到命令")
    命令 = bot.解析命令(消息)
    游戏 = 命令["参数列表"][0]
    资讯 = await mhy_core.获取资讯("国服", 游戏)
    log.debug(资讯)

    模板 = jinja2.Template("""轮播图:
{% for i in data['banners'] %}[CQ:image,file={{i['image']['url']}}]
{{i['image']['link']}}
{% endfor %}
资讯:
{% for i in data['posts'] %}{{i['title']}}
{{i['link']}}
{% endfor %}
""")
    消息 = 模板.render(data=资讯["data"].get("content"))
    await api.发送群消息(ws, data.get("group_id"), 消息)

