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
    game_id = await mhy_core.get_game_id(游戏)
    data = await mhy_core.获取资讯("国服", game_id)
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
    消息 = 模板.render(data=data["data"].get("content"))
    await api.发送群消息(ws, data.get("group_id"), 消息)

@bot.命令("获取启动器背景图", ["/获取启动器背景图"])
async def 获取启动器背景图(消息, data, ws):
    log.info("收到命令")
    命令 = bot.解析命令(消息)
    游戏 = 命令["参数列表"][0]
    game_id = await mhy_core.get_game_id(游戏)
    data = await mhy_core.获取游戏基本信息("国服", game_id)
    log.debug(data)

    消息 = f"背景图:\n[CQ:image,file={data[0]['background']['url']}]"
    await api.发送群消息(ws, data.get("group_id"), 消息)

@bot.命令("获取游戏最新版本", ["/获取游戏最新版本"])
async def 获取游戏最新版本(消息, data, ws):
    log.info("收到命令")
    命令 = bot.解析命令(消息)
    游戏 = 命令["参数列表"][0]
    game_id = await mhy_core.get_game_id(游戏)
    data = await mhy_core.获取游戏安装包信息("国服", game_id)
    log.debug(data)

    模板 = jinja2.Template("""最新版本: {{data['main']['major']['version']}}
预下载: {% if data['pre_download']['major'] %}{{data['pre_download']['major']['version']}}{% else %}预下载未开启{% endif %}""")
    消息 = 模板.render(data=data["data"]["game_packages"][0])
    await api.发送群消息(ws, data.get("group_id"), 消息)
