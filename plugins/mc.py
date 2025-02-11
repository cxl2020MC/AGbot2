from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
import mcstatus

bot = plugin.Plugin("MC服务器")

@bot.command("MC", ["mc", "查服"])
async def about(消息, data):
    log.info("收到mc命令")
    
    服务器 = await mcstatus.JavaServer.async_lookup("ifeng.asia:1")
    延迟 = await 服务器.async_ping()
    状态 = await 服务器.async_status()
    # 查询 = await 服务器.async_query()


    await api.send_message(data, f"""服务器状态:
延迟: {延迟}ms
在线人数: {状态.players.online}/{状态.players.max}
{状态}

""")