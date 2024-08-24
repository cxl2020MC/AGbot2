import aiohttp
import asyncio


def get_hyp_api_url(区服: str, api: str, language: str = "zh-cn") -> str:
    if 区服 == '国服':
        host = "hyp-api.mihoyo.com"
        launcher_id = "jGHBHlcOq1"
    else:
        raise Exception("不支持的启动器")
    url = f"https://{host}/hyp/hyp-connect/api/{api}?launcher_id={launcher_id}&language={language}"
    return url

async def get_game_id(游戏: str) -> str:
    if 游戏 == "原神":
        return "1Z8W5NHUQb"
    elif 游戏 == "绝区零":
        return "x6znKlJ0xK"
    elif 游戏 == "崩坏星穹铁道":
        return "64kMb5iAWu"
    else:
        raise Exception("不支持的游戏")


# https://hyp-api.mihoyo.com/hyp/hyp-connect/api/getGameContent?launcher_id=jGHBHlcOq1&game_id=1Z8W5NHUQb&language=zh-cn
async def 获取资讯(区服, game_id: str, language="zh-cn") -> dict:
    url = get_hyp_api_url(区服, "getGameContent", language) + f"&game_id={game_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

async def 获取全部游戏(区服, language="zh-cn"):
    url = get_hyp_api_url(区服, "getGames", language)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

async def 获取全部游戏基本信息(区服, language="zh-cn") -> dict:
    url = get_hyp_api_url(区服, "getAllGameBasicInfo", language)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

async def 获取游戏(区服, game_id: str, language="zh-cn") -> dict:
    url = get_hyp_api_url(区服, "getGames", language) + f"&game_id={game_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

async def 获取游戏基本信息(区服, game_id: str, language="zh-cn") -> dict:
    url = get_hyp_api_url(区服, "getAllGameBasicInfo", language) + f"&game_id={game_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

async def 获取全部游戏安装包信息(区服, language="zh-cn") -> dict:
    url = get_hyp_api_url(区服, "getGamePackages", language)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

async def 获取游戏安装包信息(区服, game_id: str, language="zh-cn") -> dict:
    url = get_hyp_api_url(区服, "getGamePackages", language) + f"&game_id={game_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

if __name__ == "__main__":
    print(asyncio.run(获取全部游戏安装包信息("国服", "x6znKlJ0xK")))