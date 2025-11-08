from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot.types.message_event import MessageEvent

import jinja2
import psutil
import sys
import platform
from datetime import datetime

bot = plugin.Plugin("状态")


@bot.command("状态", ["status", "状态"])
async def status_command(event: MessageEvent):
    # log.info("收到状态命令")
    cpu_usage = psutil.cpu_percent(interval=0.5)
    per_core_usage = psutil.cpu_percent(interval=0.5, percpu=True)
    logical_cores = psutil.cpu_count()
    physical_cores = psutil.cpu_count(logical=False)
    cpu_freq = psutil.cpu_freq()
    system_load = psutil.getloadavg()
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk_partitions = psutil.disk_partitions()
    # disk_usage_percent = psutil.disk_usage('/').percent
    network = psutil.net_io_counters()
    network_sent = network.bytes_sent
    network_received = network.bytes_recv
    disk = psutil.disk_io_counters()
    if disk:
        disk_written = disk.write_bytes
        disk_read = disk.read_bytes
    else:
        disk_written = 0
        disk_read = 0
    if platform.system() == "Linux":
        temperatures = psutil.sensors_temperatures() # type: ignore
    else:
        temperatures = {}
    boot_time = datetime.fromtimestamp(
        psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    python_version = sys.version

    def disk_usage(path):
        disk_usage_info = psutil.disk_usage(path)
        return f"{disk_usage_info.percent}% ({disk_usage_info.used / 1024/1024/1024:.2f}GB/{disk_usage_info.total/1024/1024/1024:.2f}GB)"

    def format_disk_info():
        disk_info = []
        for item in disk_partitions:
            disk_info.append(f"""
        驱动器: {item.device}
            挂载点: {item.mountpoint}
            文件系统: {item.fstype}
            使用率: {disk_usage(item.mountpoint)}""")
        return "".join(disk_info)

    def format_temperature_info():
        temperature_info = []
        for name, entries in temperatures.items():
            temperature_info.append(f"""
        {name}: {entries[0].current}℃ (最高温度: {entries[0].high}℃)""")
        return "".join(temperature_info)

    message = f"""状态:
    CPU: 
        使用率: {cpu_usage}% {per_core_usage}
        频率: {cpu_freq.current}Mhz ({cpu_freq.min} - {cpu_freq.max})
        逻辑核心数: {logical_cores}
        物理核心数: {physical_cores}
    系统load: {" ".join([str(round(item, 2)) for item in system_load])}
    内存: {memory.percent}% ({memory.used/1024/1024/1024:.2f}GB/{memory.total/1024/1024/1024:.2f}GB)
    交换分区: {swap.percent}% ({swap.used/1024/1024/1024:.2f}GB/{swap.total/1024/1024/1024:.2f}GB)
    磁盘: {format_disk_info()}
    网络IO: 发送: {network_sent/1024/1024/1024:.2f}GB / 接收: {network_received/1024/1024/1024:.2f}GB
    磁盘IO: 读取: {disk_read/1024/1024/1024:.2f}GB / 写入: {disk_written/1024/1024/1024:.2f}GB
    温度: {format_temperature_info()}
    系统启动时间: {boot_time}
    Python版本: {python_version}"""

    await api.send_message(event, message)