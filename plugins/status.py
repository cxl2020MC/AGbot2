from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot.event import MessageEvent

import jinja2
import psutil
import sys
from datetime import datetime

bot = plugin.Plugin("状态")


@bot.command("状态", ["status", "状态"])
async def about(event: MessageEvent):
    # log.info("收到状态命令")
    CPU使用率 = psutil.cpu_percent(interval=0.5)
    每个核心的使用率 = psutil.cpu_percent(interval=0.5, percpu=True)
    逻辑核心数 = psutil.cpu_count()
    物理核心数 = psutil.cpu_count(logical=False)
    CPU频率 = psutil.cpu_freq()
    系统load = psutil.getloadavg()
    内存 = psutil.virtual_memory()
    交换分区 = psutil.swap_memory()
    磁盘分区 = psutil.disk_partitions()
    # 磁盘使用率 = psutil.disk_usage('/').percent
    网络 = psutil.net_io_counters()
    网络发送 = 网络.bytes_sent
    网络接收 = 网络.bytes_recv
    温度 = psutil.sensors_temperatures()
    系统启动时间 = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    Python版本 = sys.version

    def 磁盘使用率(路径):
        磁盘使用率 = psutil.disk_usage(路径)
        return f"{磁盘使用率.percent}% ({磁盘使用率.used /1024/1024/1024:.2f}GB/{磁盘使用率.total/1024/1024/1024:.2f}GB)"
    
    磁盘模板 = jinja2.Template("""{% for item in 磁盘分区 %}
        驱动器: {{item.device}}
            挂载点: {{item.mountpoint}}
            文件系统: {{item.fstype}}
            使用率: {{磁盘使用率(item.mountpoint)}}%{% endfor %}""")

    温度模板 = jinja2.Template("""{% for name, emtries in 温度.items() %}
        {{name}}: {{emtries[0].current}}℃ (温度墙: {{emtries[0].high}}℃){% endfor %}""")

    消息 = f"""状态:
    CPU: 
        使用率: {CPU使用率}% ({", ".join([f"{item}%" for item in 每个核心的使用率])})
        频率: {CPU频率.current}Mhz ({CPU频率.min} - {CPU频率.max})
        逻辑核心数: {逻辑核心数}
        物理核心数: {物理核心数}
    系统load: {" ".join([str(item) for item in 系统load])}
    内存: {内存.percent}% ({内存.used/1024/1024/1024:.2f}GB/{内存.total/1024/1024/1024:.2f}GB)
    交换分区: {交换分区.percent}% ({交换分区.used/1024/1024/1024:.2f}GB/{交换分区.total/1024/1024/1024:.2f}GB)
    磁盘: {磁盘模板.render(磁盘分区=磁盘分区, 磁盘使用率=磁盘使用率)}
    网络: 发送: {网络发送/1024/1024/1024:.2f}GB / 接收: {网络接收/1024/1024/1024:.2f}GB
    温度: {温度模板.render(温度=温度)}
    系统启动时间: {系统启动时间}
    Python版本: {Python版本}"""
   
    await api.send_message(event, 消息)
