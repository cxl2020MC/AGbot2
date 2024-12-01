import functools
import traceback
from .log import logger as log
from . import api


class _Bot:
    def __init__(self) -> None:
        self.plugin_list = []
        self.command_list = []

    def 加载插件(self, 插件):
        self.plugin_list.append(插件)
        self.command_list += 插件.command_list
        log.info(f"加载插件 {插件.name} 成功")

    async def 匹配命令(self, data):
        """匹配command"""
        消息: str = data.get("raw_message", "")
        if not 消息:
            log.warning("消息为空")
            return
        elif 消息[0] == "/":
            message_list = 消息.split(" ")
            for command_list in self.command_list:
                if message_list[0] in command_list["command_list"]:
                    log.debug(f"匹配到命令: {message_list[0]} 位于 {command_list['command_list']}")
                    await command_list["函数"](消息, data)


class Plugin:
    def __init__(self, 名称) -> None:
        self.name = 名称
        self.command_list = []

    def 命令(self, 名称, command_list: list):
        def director(func):
            @functools.wraps(func)
            async def wrapper(消息, data, *args, **kwargs):
                try:
                    return await func(消息, data, *args, **kwargs)
                except Exception as e:
                    log.error(f"命令 {名称} 执行出错: {traceback.format_exc()}")
                    await api.send_message(data, f"命令 {名称} 执行出错: {e.__class__.__name__}: {e}")
            command_data = {"command_list": command_list, "命令名称": 名称, "插件名称": self.name, "函数": wrapper}
            self.command_list.append(command_data)
            log.debug(f"注册命令: {command_list} 成功")
            return wrapper
        return director

    def 解析命令(self, 命令: str):
        command_list = 命令.split(" ")
        command_data = {"命令": command_list[0], "参数列表": [], "参数字典": {}}
        for 参数 in command_list[1:]:
            if 参数.startswith("-"):
                指定参数 = 参数.split("=")
                command_data["参数字典"][指定参数[0][1:]] = 指定参数[1]
            else:
                command_data["参数列表"].append(参数)
        return command_data


bot = _Bot()
