import functools
import shlex
from .log import logger as log
from . import utils
from .event import MessageEvent

from collections.abc import Callable
from typing import Any
from enum import Enum


def load_pulgin(plugin):
    log.info(f"加载插件 {plugin.name} 中...")
    Plugin.plugin_list.append(plugin)
    Plugin.command_list += plugin.command_list
    Plugin.event_list += plugin.event_list
    log.info(f"加载插件 {plugin.name} 成功")



async def 匹配命令(event: MessageEvent):
    message_list = event.message
    if not message_list:
        log.warning("消息为空")
        return
    else:
        for msg in message_list:
            if msg.get("type") == "text":
                message: str = msg.get("data", {}).get("text", "")
                log.debug(f"检测消息文本: {message}")
                if message[0] == "/":
                    messages = message[1:].split(" ")
                    for command_list in Plugin.command_list:
                        if messages[0] in command_list["command_list"]:
                            log.debug(
                                f"匹配到命令: {messages[0]} 位于 {command_list['command_list']}")
                            event.command_text = message
                            await command_list["函数"](event)
        # return
        

# message_type = Enum("message_type", "group private all")

async def 匹配事件(event: MessageEvent):
    for event_type, data, func in Plugin.event_list:
        match event_type:
            case "message":
                if event.message_type == data["message_type"]:
                    log.debug(f"匹配到事件: {event_type}: {data}")
                    await func(event)
            # case "message_type":
            #     if event.message_type == data:
            #         log.debug(f"匹配到事件: {event_type}: {data}")
            #         await data["函数"](event)

class Plugin:
    plugin_list = []
    command_list = []
    event_list = []

    def __init__(self, name) -> None:
        self.name = name
        self.command_list = []
        self.event_list = []

    def command[F: Callable[..., Any]](self, 名称, command_list: list) -> Callable[..., Any]:
        def director(func):
            log.debug(f"注册命令: {command_list}")

            @functools.wraps(func)
            async def wrapper(event: MessageEvent, *args, **kwargs):
                try:
                    return await func(event, *args, **kwargs)
                except Exception as e:
                    await utils.log_error(event, f"命令 {名称}", e)
            command_data = {"command_list": command_list,
                            "命令名称": 名称, "插件名称": self.name, "函数": wrapper}
            self.command_list.append(command_data)
            log.debug(f"注册命令: {command_list} 成功")
            return wrapper
        return director

    def 解析命令(self, 命令: str):
        command_list = shlex.split(命令)
        command_data = {"命令": command_list[0],
                        "参数列表": [], "参数字典": {}, "指定参数": []}
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

    def _on[F: Callable[..., Any]](self, event_type, data) -> Callable[..., Any]:
        def director(func):
            @functools.wraps(func)
            async def wrapper(event: MessageEvent, *args, **kwargs):
                try:
                    return await func(event, *args, **kwargs)
                except Exception as e:
                    await utils.log_error(event, f"事件监听器 {event_type}: {data}", e, send_message=False)
            event_data = (event_type, data, wrapper)
            self.event_list.append(event_data)
            log.debug(f"注册事件监听器: {event_type}: {data} 成功")
            return wrapper
        return director

    def on_message(self, message_type: str) -> Callable[..., Any]:
        data = {
            "message_type": message_type or "all"
        }
        return self._on("message", data)
    


