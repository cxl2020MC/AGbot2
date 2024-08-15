import functools
from .log import logger as log


class _Bot:
    def __init__(self) -> None:
        self.插件列表 = []
        self.命令列表 = []

    def 加载插件(self, 插件):
        self.插件列表.append(插件)
        self.命令列表 += 插件.命令列表
        log.info(f"加载插件 {插件.名称} 成功")

    async def 匹配命令(self, bot_self, data, ws):
        """匹配命令"""
        消息 = data.get("message", "")
        if not 消息:
            return
        elif 消息[0] == "/":
            for 命令列表 in self.命令列表:
                if data["命令"] in 命令列表["命令列表"]:
                    log.debug(f"匹配到命令: {data['命令']}")
                    await 命令列表["函数"](bot_self, data, ws)


class Plugin:
    def __init__(self, 名称) -> None:
        self.名称 = 名称
        self.命令列表 = []

    def 命令(self, 名称, 命令列表: list):
        def director(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            命令数据 = {"命令列表": 命令列表, "命令名称": 名称, "插件名称": self.名称, "函数": wrapper}
            self.命令列表.append(命令数据)
            log.debug(f"注册命令: {命令列表} 成功")
            return wrapper
        return director


bot = _Bot()
