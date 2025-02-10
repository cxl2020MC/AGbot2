from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
import jinja2
import psutil


bot = plugin.Plugin("状态")


@bot.command("状态", ["status", "状态"])
async def about(消息, data):
    log.info("收到关状态命令")
    CPU使用率 = psutil.cpu_percent(interval=0.2)
    逻辑核心数 = psutil.cpu_count()
    物理核心数 = psutil.cpu_count(logical=False)
    CPU频率 = psutil.cpu_freq()
    内存使用率 = psutil.virtual_memory().percent
    磁盘使用率 = psutil.disk_usage('/').percent
    网络发送 = psutil.net_io_counters().bytes_sent
    网络接收 = psutil.net_io_counters().bytes_recv

    模板 = jinja2.Template("""状态:
    CPU: {{ CPU使用率 }}
    CPU频率: {{ CPU频率 }}
    逻辑核心数: {{ 逻辑核心数 }}
    物理核心数: {{ 物理核心数 }}
    内存: {{ 内存使用率 }}
    磁盘: {{ 磁盘使用率 }}
    网络: {{ 网络发送 }} / {{ 网络接收 }}
""")
    msg = 模板.render(CPU使用率=CPU使用率, CPU频率=CPU频率, 逻辑核心数=逻辑核心数,
                    物理核心数=物理核心数, 内存使用率=内存使用率, 磁盘使用率=磁盘使用率, 网络发送=网络发送, 网络接收=网络接收)
    await api.send_message(data, msg)
