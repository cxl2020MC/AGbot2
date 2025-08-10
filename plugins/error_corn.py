from calendar import c
from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot import config
from AGbot import command_utils
from AGbot.event import MessageEvent

import aiofiles
import pathlib
import json


bot = plugin.Plugin("错误罐头")


@bot.command("查看错误罐头", ["error-corn"])
async def 查看错误罐头(event: MessageEvent):
    cmd = command_utils.Command(event.raw_message)
    filename = cmd.get_arg(0)
    if filename is None:
        await api.send_message(event, "请输入要查看的错误追踪文件名")
        return
    filename = filename + ".json"
    path = pathlib.Path(config.数据文件夹) / "错误追踪" / filename
    if not path.exists():
        await api.send_message(event, "未找到该错误追踪文件")
        return
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        json_str = await f.read()
        data: dict = json.loads(json_str)
    消息内容 = f"""错误追踪文件: {filename}
发生时间：{data.get("time")}
上报数据: {data.get("data")}
错误追踪: {data.get("traceback")}"""
    await api.send_message(event, 消息内容)
