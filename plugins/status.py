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
    内存使用率 = psutil.virtual_memory()
    磁盘分区 = psutil.disk_partitions()
    # 磁盘使用率 = psutil.disk_usage('/').percent
    网络发送 = psutil.net_io_counters().bytes_sent
    网络接收 = psutil.net_io_counters().bytes_recv
    温度 = psutil.sensors_temperatures()
    
    磁盘模板 = jinja2.Template("""{% for item in 磁盘分区 %}
        驱动器: {{item.device}}
            挂载点: {{item.mountpoint}}
            文件系统: {{item.fstype}}
            使用率: {{disk_usage(item.mountpoint).percent}}%{% endfor %}""")

    温度模板 = jinja2.Template("""{% for name, emtries in 温度.items() %}
        {{name}}: {{emtries[0].current}}℃ (温度墙: {{emtries[0].high}}℃){% endfor %}""")

    消息 = f"""状态:
    CPU: 
        使用率{CPU使用率}%
        频率: {CPU频率.current}Mhz ({CPU频率.min} - {CPU频率.max})
        逻辑核心数: {逻辑核心数}
        物理核心数: {物理核心数}
    内存: 
        使用率: {内存使用率.percent}%
    磁盘: {磁盘模板.render(磁盘分区=磁盘分区, disk_usage=psutil.disk_usage)}
    网络: {网络发送} / {网络接收}
    温度: {温度模板.render(温度=温度)}"""
   
    await api.send_message(data, 消息)
