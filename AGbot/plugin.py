import functools
import traceback
import shlex
from .log import logger as log
from . import api
from . import utils
from .event import MessageEvent

from collections.abc import Callable
from typing import Any

def load_pulgin(plugin):
    log.info(f"加载插件 {plugin.name} 中...")
    Plugin.plugin_list.append(plugin)
    Plugin.command_list += plugin.command_list
    log.info(f"加载插件 {plugin.name} 成功")


async def 匹配命令(data):
    """匹配命令"""
    消息: str = data.get("raw_message", "")
    if not 消息:
        log.warning("消息为空")
        return
    elif 消息[0] == "/":
        # 匹配命令
        # 忽略第一位/
        message_list = 消息[1:].split(" ")
        for command_list in Plugin.command_list:
            if message_list[0] in command_list["command_list"]:
                log.debug(f"匹配到命令: {message_list[0]} 位于 {command_list['command_list']}")
                event = MessageEvent(data)
                await command_list["函数"](event)


class Plugin:
    plugin_list = []
    command_list = []
    def __init__(self, 名称) -> None:
        self.name = 名称
        self.command_list = []

    def command[F: Callable[..., Any]](self, 名称, command_list: list) -> Callable[..., Any]:
        def director(func):
            @functools.wraps(func)
            async def wrapper(event: MessageEvent, *args, **kwargs):
                try:
                    return await func(event, *args, **kwargs)
                except Exception as e:
                    exc = traceback.format_exc()
                    log.error(f"命令 {名称} 执行出错: {exc}")
                    try:
                        error_id = await utils.储存错误追踪(event.data, exc)
                    except Exception as e2:
                        error_id = None
                        log.error(f"储存错误追踪失败: {e2}")
                    await api.send_message(event, f"命令 {名称} 执行出错: {e.__class__.__name__}: {e}\nerror_id: {error_id}")
            command_data = {"command_list": command_list, "命令名称": 名称, "插件名称": self.name, "函数": wrapper}
            self.command_list.append(command_data)
            log.debug(f"注册命令: {command_list} 成功")
            return wrapper
        return director

    def 解析命令(self, 命令: str):
        command_list = shlex.split(命令)
        command_data = {"命令": command_list[0], "参数列表": [], "参数字典": {}, "指定参数": []}
        for 参数 in command_list[1:]:
            if 参数.startswith("-"):
                指定参数 = 参数.split("=")
                if len(指定参数) == 2:
                    command_data["参数字典"][指定参数[0][1:]] = 指定参数[1]
                else:
                    command_data["指定参数"].append(指定参数[0][1:])
            else:
                command_data["参数列表"].append(参数)
        return command_data

