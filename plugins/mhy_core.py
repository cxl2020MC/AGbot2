# import aiohttp
import asyncio
import httpx
import json
from typing import Literal, TypedDict
from enum import Enum

from AGbot.log import logger as log
# from  import models


class LaucherArea(Enum):
    "启动器api地区"
    CN = 1
    GLOBAL = 2


type LaucherAreaLiteral = Literal[LaucherArea.CN, LaucherArea.GLOBAL]

client = httpx.AsyncClient()


# def get_hyp_api_url(area: str, api: str) -> str:
#     match area:
#         case "国服":
#             host = "hyp-api.mihoyo.com"
#         case "国际服":
#             host = "sg-hyp-api.hoyoverse.com"
#         case _:
#             raise Exception("不支持的启动器")
#     url = f"https://{host}/hyp/hyp-connect/api/{api}"
#     return url


def get_hyp_api_url(area, api: str) -> str:
    hyp_api_bases = {
        LaucherArea.CN: "hyp-api.mihoyo.com",
        LaucherArea.GLOBAL: "sg-hyp-api.hoyoverse.com",
    }
    host = hyp_api_bases.get(area)
    if host is None:
        raise Exception("不支持的启动器")
    url = f"https://{host}/hyp/hyp-connect/api/{api}"
    return url

# def get_launcher_id(laucher: str) -> str:
#     match laucher:
#         case "国服":
#             return "jGHBHlcOq1"
#         case "国际服":
#             return "VYTpXlbWo8"
#         case "B服原神":
#             return "umfgRO5gh5"
#         case "B服星铁":
#             return "6P5gHMNyK3"
#         case "B服绝区零":
#             return "xV0f4r1GT0"
#         case _:
#             raise Exception("不支持的启动器")


class Laucher(Enum):
    CN = 1
    GLOBAL = 2
    BILIBILIYS = 3
    BILIBILISR = 4
    BILIBILIZZZ = 5


type LauncherLiteral = Literal[Laucher.CN, Laucher.GLOBAL,
                               Laucher.BILIBILIYS, Laucher.BILIBILISR, Laucher.BILIBILIZZZ]


def get_launcher_id(laucher: LauncherLiteral) -> str:
    launcher_ids = {
        Laucher.CN: "jGHBHlcOq1",
        Laucher.GLOBAL: "VYTpXlbWo8",
        Laucher.BILIBILIYS: "umfgRO5gh5",
        Laucher.BILIBILISR: "6P5gHMNyK3",
        Laucher.BILIBILIZZZ: "xV0f4r1GT0",
    }
    laucher_id = launcher_ids.get(laucher)
    if not laucher_id:
        raise Exception("不支持的启动器")
    return laucher_id


def get_laucher_data(laucher: str) -> dict:
    return {}


async def get_game_id(laucher: str, game: str) -> str:
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


class Launcher:
    def __init__(self, area, launcher, api_base: str, launcher_id: str, language: str = "zh-cn"):
        self.area = area
        self.launcher = launcher
        self.api_base = api_base
        self.launcher_id = launcher_id
        self.language = language

    @staticmethod
    def _get_launcher_id(laucher: LauncherLiteral) -> str:
        match laucher:
            case Laucher.CN:
                return "jGHBHlcOq1"
            case Laucher.GLOBAL:
                return "VYTpXlbWo8"
            case Laucher.BILIBILIYS:
                return "umfgRO5gh5"
            case Laucher.BILIBILISR:
                return "6P5gHMNyK3"
            case Laucher.BILIBILIZZZ:
                return "xV0f4r1GT0"
            case _:
                raise Exception("不支持的启动器")

    @staticmethod
    def get_hyp_api_base(area: LaucherAreaLiteral) -> str:
        # hyp_api_bases = {
        #     LaucherArea.CN: "hyp-api.mihoyo.com",
        #     LaucherArea.GLOBAL: "sg-hyp-api.hoyoverse.com",
        # }
        # host = hyp_api_bases.get(area)
        # if host is None:
        #     raise Exception("不支持的启动器")
        # return host
        match area:
            case LaucherArea.CN:
                return "hyp-api.mihoyo.com"
            case LaucherArea.GLOBAL:
                return "sg-hyp-api.hoyoverse.com"
            case _:
                raise Exception("不支持的启动器")


HYP_API_DATA = {
    LaucherArea.CN: {
        "api_base": "hyp-api.mihoyo.com",
        "launcher_ids": {
            Laucher.CN: "jGHBHlcOq1",
            Laucher.BILIBILIYS: "umfgRO5gh5",
            Laucher.BILIBILISR: "6P5gHMNyK3",
            Laucher.BILIBILIZZZ: "xV0f4r1GT0",
        }
    },
    LaucherArea.GLOBAL: {
        "api_base": "hyp-api.mihoyo.com",
        "launcher_ids": {
            Laucher.GLOBAL: "VYTpXlbWo8",
        }
    },
}


def create_launcher(laucher: Laucher, area: LaucherArea):
    return Launcher(HYP_API_DATA[area]["api_base"], HYP_API_DATA[area]["launcher_ids"][laucher])


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
