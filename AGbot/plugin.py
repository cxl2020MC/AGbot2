import functools
from .log import logger as log


class plugin:
    def __init__(self, 插件名称: str) -> None:
        self.插件名称 = 插件名称
        self.命令列表 = []
    
    def 命令(self, 名称, 命令列表: list):
        async def director(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            命令数据 = {"命令列表": 命令列表, "名称":名称, "函数": wrapper}
            self.命令列表.append(命令数据)
            log.debug(f"注册命令: {命令列表} 成功")
            return wrapper
        return director