from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot.types.message import MessageEvent

import jinja2
import psutil
import sys
import platform
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
    磁盘 = psutil.disk_io_counters()
    if 磁盘:
        磁盘写入 = 磁盘.write_bytes
        磁盘读取 = 磁盘.read_bytes
    else:
        磁盘写入 = 0
        磁盘读取 = 0
    if platform.system() == "Linux":
        温度 = psutil.sensors_temperatures() # type: ignore
    else:
        温度 = {}
    系统启动时间 = datetime.fromtimestamp(
        psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    Python版本 = sys.version

    def 磁盘使用率(路径):
        磁盘使用率 = psutil.disk_usage(路径)
        return f"{磁盘使用率.percent}% ({磁盘使用率.used / 1024/1024/1024:.2f}GB/{磁盘使用率.total/1024/1024/1024:.2f}GB)"

    def 格式化磁盘信息():
        磁盘信息 = []
        for item in 磁盘分区:
            磁盘信息.append(f"""
        驱动器: {item.device}
            挂载点: {item.mountpoint}
            文件系统: {item.fstype}
            使用率: {磁盘使用率(item.mountpoint)}""")
        return "".join(磁盘信息)

    def 格式化温度信息():
        温度信息 = []
        for name, entries in 温度.items():
            温度信息.append(f"""
        {name}: {entries[0].current}℃ (最高温度: {entries[0].high}℃)""")
        return "".join(温度信息)

    消息 = f"""状态:
    CPU: 
        使用率: {CPU使用率}% {每个核心的使用率}
        频率: {CPU频率.current}Mhz ({CPU频率.min} - {CPU频率.max})
        逻辑核心数: {逻辑核心数}
        物理核心数: {物理核心数}
    系统load: {" ".join([str(round(item, 2)) for item in 系统load])}
    内存: {内存.percent}% ({内存.used/1024/1024/1024:.2f}GB/{内存.total/1024/1024/1024:.2f}GB)
    交换分区: {交换分区.percent}% ({交换分区.used/1024/1024/1024:.2f}GB/{交换分区.total/1024/1024/1024:.2f}GB)
    磁盘: {格式化磁盘信息()}
    网络IO: 发送: {网络发送/1024/1024/1024:.2f}GB / 接收: {网络接收/1024/1024/1024:.2f}GB
    磁盘IO: 读取: {磁盘读取/1024/1024/1024:.2f}GB / 写入: {磁盘写入/1024/1024/1024:.2f}GB
    温度: {格式化温度信息()}
    系统启动时间: {系统启动时间}
    Python版本: {Python版本}"""

    await api.send_message(event, 消息)
