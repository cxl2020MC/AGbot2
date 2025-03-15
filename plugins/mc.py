from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
import mcstatus

bot = plugin.Plugin("MC服务器")

server_map = {
    993426084: "ifeng.asia:1",
    860769764: "home.cxl2020mc.top",
    925603600: "110.40.58.165:18260"
}

@bot.command("MC", ["mc", "查服"])
async def about(消息, data):
    log.info("收到mc命令")

    群号 = data.get("group_id")
    if 群号 not in server_map:
        await api.send_message(data, "该群没有配置mc服务器地址")
        return
    
    服务器地址 = server_map[群号]
    
    服务器 = await mcstatus.JavaServer.async_lookup(服务器地址)
    延迟 = await 服务器.async_ping()
    状态 = await 服务器.async_status()
    log.debug(状态)
    # 查询 = await 服务器.async_query()
    if 状态.players.sample:
        当前在线 = [玩家.name for 玩家 in 状态.players.sample]
    else:
        当前在线 = "无"

    await api.send_message(data, f"""服务器状态:
    地址: {服务器地址}
    版本: {状态.version.name}
    描述: {状态.motd.raw}
    延迟: {延迟:.2f}ms
    在线人数: {状态.players.online}/{状态.players.max}
    当前在线: {", ".join(当前在线)}""")