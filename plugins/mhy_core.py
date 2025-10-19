# import aiohttp
import asyncio
import httpx
import json
from AGbot.log import logger as log
# from  import models


client = httpx.AsyncClient()


def get_hyp_api_url(area: str, api: str) -> str:
    match area:
        case "国服":
            host = "hyp-api.mihoyo.com"
        case "国际服":
            host = "sg-hyp-api.hoyoverse.com"
        case _:
            raise Exception("不支持的启动器")
    url = f"https://{host}/hyp/hyp-connect/api/{api}"
    return url


def get_launcher_id(laucher: str) -> str:
    match laucher:
        case "国服":
            return "jGHBHlcOq1"
        case "国际服":
            return "VYTpXlbWo8"
        case "B服原神":
            return "umfgRO5gh5"
        case "B服星铁":
            return "6P5gHMNyK3"
        case "B服绝区零":
            return "xV0f4r1GT0"
        case _:
            raise Exception("不支持的启动器")


def get_laucher_data(laucher: str) -> dict:
    return {}


async def get_game_id(laucher: str, game: str) -> str:
    # if game == "原神":
    #     return "1Z8W5NHUQb"
    # elif game == "绝区零":
    #     return "x6znKlJ0xK"
    # elif game == "崩坏星穹铁道":
    #     return "64kMb5iAWu"
    # elif game == "崩坏3":
    #     return "osvnlOc0S8"
    # else:
    #     raise Exception("不支持的游戏")
    data = await 获取全部游戏(laucher)
    for i in data["data"]["games"]:
        if i["biz"] == game:
            return i["id"]
    raise Exception("不支持的游戏")


def get_hyp_api_params(laucher: str = "国服", language: str = "zh-cn") -> dict:
    return {
        "launcher_id": get_launcher_id(laucher),
        "language": language,
        # "game_id": get_game_id(游戏)
    }


# https://hyp-api.mihoyo.com/hyp/hyp-connect/api/getGameContent?launcher_id=jGHBHlcOq1&game_id=1Z8W5NHUQb&language=zh-cn
async def 获取游戏内容(laucher, game: str, language: str = "zh-cn") -> dict:
    url = get_hyp_api_url(laucher, "getGameContent")
    params = get_hyp_api_params(laucher, language)
    params["game_id"] = await get_game_id(laucher, game)
    resp = await client.get(url, params=params)
    log.debug(f"发送请求: {resp.url} 请求结果: {resp.text}")
    return resp.json()


async def 获取全部游戏(laucher, language="zh-cn"):
    url = get_hyp_api_url(laucher, "getGames")
    resp = await client.get(url, params=get_hyp_api_params(laucher, language))
    log.debug(f"发送请求: {resp.url} 请求结果: {resp.text}")
    return resp.json()


async def 获取全部游戏基本信息(laucher, language="zh-cn") -> dict:
    url = get_hyp_api_url(laucher, "getAllGameBasicInfo")
    resp = await client.get(url, params=get_hyp_api_params(laucher, language))
    log.debug(f"发送请求: {resp.url} 请求结果: {resp.text}")
    return resp.json()


async def 获取游戏(laucher, game: str, language="zh-cn") -> dict:
    url = get_hyp_api_url(laucher, "getGames")
    params = get_hyp_api_params(laucher, language)
    params["game_id"] = await get_game_id(laucher, game)
    resp = await client.get(url, params=params)
    log.debug(f"发送请求: {resp.url} 请求结果: {resp.text}")
    return resp.json()


async def 获取游戏基本信息(laucher, game: str, language="zh-cn") -> dict:
    url = get_hyp_api_url(laucher, "getAllGameBasicInfo")
    params = get_hyp_api_params(laucher, language)
    params["game_id"] = await get_game_id(laucher, game)
    resp = await client.get(url, params=params)
    log.debug(f"发送请求: {resp.url} 请求结果: {resp.text}")
    return resp.json()


async def 获取全部游戏安装包信息(laucher, language="zh-cn") -> dict:
    url = get_hyp_api_url(laucher, "getGamePackages")
    resp = await client.get(url, params=get_hyp_api_params(laucher, language))
    log.debug(f"发送请求: {resp.url} 请求结果: {resp.text}")
    return resp.json()


async def 获取游戏安装包信息(laucher, game: str, language="zh-cn") -> dict | None:
    ret_data = await 获取全部游戏安装包信息(laucher, language)
    game_id = await get_game_id(laucher, game)
    for i in ret_data["data"]["game_packages"]:
        if i["game"]["id"] == game_id:
            return i


async def 获取多个游戏安装包信息(laucher, game_ids: list[str], language="zh-cn") -> dict:
    url = get_hyp_api_url(laucher, "getGamePackages")
    params = get_hyp_api_params(laucher, language)
    params["game_ids"] = game_ids
    resp = await client.get(url, params=params)
    log.debug(f"发送请求: {resp.url} 请求结果: {resp.text}")
    return resp.json()


async def 获取游戏依赖(laucher, game: str, language="zh-cn") -> dict:
    url = get_hyp_api_url(
        laucher, "getGameDeprecatedFileConfigs")
    params = get_hyp_api_params(laucher, language)
    params["game_id"] = game
    resp = await client.get(url, params=params)
    log.debug(f"发送请求: {resp.url} 请求结果: {resp.text}")
    return resp.json()


async def 获取游戏配置(laucher, game: str, language="zh-cn") -> dict:
    url = get_hyp_api_url(laucher, "getGameConfigs")
    params = get_hyp_api_params(laucher, language)
    params["game_id"] = game
    resp = await client.get(url, params=params)
    log.debug(f"发送请求: {resp.url} 请求结果: {resp.text}")
    return resp.json()


if __name__ == "__main__":
    import json
    # print(asyncio.run(获取游戏配置("国服", "1Z8W5NHUQb")))
    # x6znKlJ0xK
    # print(asyncio.run(获取游戏配置("国服", "1Z8W5NHUQb")))
    data = asyncio.run(获取游戏内容("国服", "nap_cn"))
    # print(data)
    print(json.dumps(data, indent=4, ensure_ascii=False))
