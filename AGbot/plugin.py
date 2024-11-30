import functools
import traceback
import shlex
from .log import logger as log
from . import api
from . import utils

插件列表 = []
命令列表 = []


def 加载插件(插件):
    global 插件列表, 命令列表
    插件列表.append(插件)
    命令列表 += 插件.命令列表
    log.info(f"加载插件 {插件.名称} 成功")


async def 匹配命令(data):
    """匹配命令"""
    消息: str = data.get("raw_message", "")
    if not 消息:
        log.warning("消息为空")
        return
    elif 消息[0] == "/":
        消息列表 = 消息.split(" ")
        for 插件命令列表 in 命令列表:
            if 消息列表[0] in 插件命令列表["命令列表"]:
                log.debug(f"匹配到命令: {消息列表[0]} 位于 {插件命令列表['命令列表']}")
                await 插件命令列表["函数"](消息, data)


class Plugin:
    def __init__(self, 名称) -> None:
        self.名称 = 名称
        self.命令列表 = []

    def 命令(self, 名称, 命令列表: list):
        def director(func):
            @functools.wraps(func)
            async def wrapper(消息, data, *args, **kwargs):
                try:
                    return await func(消息, data, *args, **kwargs)
                except Exception as e:
                    exc = traceback.format_exc()
                    log.error(f"命令 {名称} 执行出错: {exc}")
                    await utils.储存错误追踪(data, exc)
                    await api.发送群消息(data.get("group_id"), f"命令 {名称} 执行出错: {e.__class__.__name__}: {e}")
            命令数据 = {"命令列表": 命令列表, "命令名称": 名称, "插件名称": self.名称, "函数": wrapper}
            self.命令列表.append(命令数据)
            log.debug(f"注册命令: {命令列表} 成功")
            return wrapper
        return director

    def 解析命令(self, 命令: str):
        命令列表 = shlex.split(命令)
        命令数据 = {"命令": 命令列表[0], "参数列表": [], "参数字典": {}, "指定参数": []}
        for 参数 in 命令列表[1:]:
            if 参数.startswith("-"):
                指定参数 = 参数.split("=")
                if len(指定参数) == 2:
                    命令数据["参数字典"][指定参数[0][1:]] = 指定参数[1]
                else:
                    命令数据["指定参数"].append(指定参数[0][1:])
            else:
                命令数据["参数列表"].append(参数)
        return 命令数据
