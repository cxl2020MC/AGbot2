import functools
import traceback
import shlex
from .log import logger as log
from . import api
from . import utils

plugin_list = []
command_list = []
command_map = {}

def 加载插件(插件):
    global plugin_list, command_list, command_map
    plugin_list.append(插件)
    command_list += 插件.command_list
    for 命令 in 插件.command_list:
        for command_data in 命令["command_list"]:
            command_map.update({command_data: 命令})
    log.info(f"加载插件 {插件.name} 成功")


async def 匹配命令(data):
    """匹配命令"""
    消息: str = data.get("raw_message", "")
    if not 消息:
        log.warning("消息为空")
        return
    elif 消息[0] == "/":
        message_list = 消息.split(" ")
        for plugin_command_list in command_list:
            if message_list[0] in plugin_command_list["command_list"]:
                log.debug(f"匹配到命令: {message_list[0]} 位于 {plugin_command_list['command_list']}")
                await plugin_command_list["函数"](消息, data)


class Plugin:
    def __init__(self, 名称) -> None:
        self.name = 名称
        self.command_list = []

    def command(self, 名称, command_list: list):
        def director(func):
            @functools.wraps(func)
            async def wrapper(消息, data, *args, **kwargs):
                try:
                    return await func(消息, data, *args, **kwargs)
                except Exception as e:
                    exc = traceback.format_exc()
                    log.error(f"命令 {名称} 执行出错: {exc}")
                    try:
                        error_id = await utils.储存错误追踪(data, exc)
                    except Exception as e:
                        error_id = None
                        log.error(f"储存错误追踪失败: {e}")
                    await api.send_message(data, f"命令 {名称} 执行出错: {e.__class__.__name__}: {e}\nerror_id: {error_id}")
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


class CommandLineParser:
    def __init__(self):
        self.positional_args = []
        self.options = {}

    def add_argument(self, *args, **kwargs):
        for arg in args:
            self.options[arg] = kwargs.get('default', None)

    def parse_args(self, command_str):
        tokens = shlex.split(command_str)

        for i, token in enumerate(tokens):
            if token.startswith('-'):
                if token in self.options:
                    if i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
                        self.options[token] = tokens[i + 1]
                        i += 1
                    elif self.options[token] is None:
                        self.options[token] = True
                    else:
                        raise ValueError(f"Option {token} requires an argument")
                else:
                    raise ValueError(f"Unknown option: {token}")
            else:
                self.positional_args.append(token)

        return self

    def __str__(self):
        return f"Positional arguments: {self.positional_args}\nOptions: {self.options}"

# 创建解析器实例
parser = CommandLineParser()

# 添加命令行参数
parser.add_argument('command', help='The main command')
parser.add_argument('-f', '--file', help='File to process', default=None)
parser.add_argument('-v', '--verbose', help='Enable verbose mode', action='store_true')

# 解析命令行字符串
command_str = 'main_command -f file.txt -v'
parsed_args = parser.parse_args(command_str)

# 打印解析结果
print(parsed_args)