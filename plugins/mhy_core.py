import asyncio
import aiohttp
from yarl import URL
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


class Launcher(Enum):
    CN = 1
    GLOBAL = 2
    BILIBILIYS = 3
    BILIBILISR = 4
    BILIBILIZZZ = 5


type LauncherLiteral = Literal[Launcher.CN, Launcher.GLOBAL,
                               Launcher.BILIBILIYS, Launcher.BILIBILISR, Launcher.BILIBILIZZZ]


# https://github.com/Scighost/Starward/blob/main/src/Starward.Core/HoYoPlay/HoYoPlayClient.cs
class HYPLauncher:
    def __init__(self, area: LaucherAreaLiteral, launcher: LauncherLiteral, language: str = "zh-cn"):
        self.area = area
        self.launcher = launcher
        self.api_base = self._get_hyp_api_base(area)
        self.launcher_id = self._get_launcher_id(launcher)
        self.hyp_api_url = self.get_hyp_api_url()
        self.hyp_game_chunk_api_base = self._get_game_chunk_api_base(area)
        self.hyp_game_chunk_api_url = self.get_hyp_game_chunk_api_url()
        self.language = language

    @staticmethod
    def _get_launcher_id(laucher: LauncherLiteral) -> str:
        match laucher:
            case Launcher.CN:
                return "jGHBHlcOq1"
            case Launcher.GLOBAL:
                return "VYTpXlbWo8"
            case Launcher.BILIBILIYS:
                return "umfgRO5gh5"
            case Launcher.BILIBILISR:
                return "6P5gHMNyK3"
            case Launcher.BILIBILIZZZ:
                return "xV0f4r1GT0"
            case _:
                raise Exception("不支持的启动器")

    @staticmethod
    def _get_hyp_api_base(area: LaucherAreaLiteral) -> str:
        match area:
            case LaucherArea.CN:
                return "hyp-api.mihoyo.com"
            case LaucherArea.GLOBAL:
                return "sg-hyp-api.hoyoverse.com"
            case _:
                raise Exception("不支持的启动器")

    @staticmethod
    def _get_game_chunk_api_base(area: LaucherAreaLiteral) -> str:
        match area:
            case LaucherArea.CN:
                return "downloader-api.mihoyo.com"
            case LaucherArea.GLOBAL:
                return "sg-downloader-api.hoyoverse.com"
            case _:
                raise Exception("不支持的启动器")

    def get_hyp_api_params(self) -> dict:
        return {
            "launcher_id": self.launcher_id,
            "language": self.language,
            # "game_id": get_game_id(游戏)
        }

    def get_hyp_api_url(self) -> URL:
        api_url_str = f"https://{self.api_base}/hyp/hyp-connect/api"
        return URL(api_url_str)

    def get_hyp_game_chunk_api_url(self) -> URL:
        api_url_str = f"https://{self.hyp_game_chunk_api_base}/downloader/sophon_chunk/api"
        return URL(api_url_str)

    async def fetch_hyp_api(self, path: str, params: dict | None = None) -> dict:
        api_url = self.hyp_api_url / path
        api_params = self.get_hyp_api_params()
        if params is not None:
            api_params.update(params)
        log.debug(f"请求 URL: {api_url}\n请求参数: {api_params}")
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=api_params) as response:
                log.debug(f"编码 URL: {response.url}")
                response.raise_for_status()
                res = await response.json()
                log.debug(f"响应数据: {res}")
                if res.get("retcode") != 0:
                    raise Exception(f"API 请求错误: {res}")
                return res.get("data")

    async def get_games(self):
        data = await self.fetch_hyp_api("getGames")
        return data

    async def use_game_biz_get_game_id(self, game_biz: str) -> str:
        data = await self.get_games()
        for game_data in data["games"]:
            if game_data["biz"] == game_biz:
                return game_data["id"]
        raise Exception(f"游戏 {game_biz} 不存在")

    async def get_games_basic_info(self, game_id: str | None = None):
        if game_id is None:
            params = None
        else:
            params = {
                "game_id": game_id
            }
        data = await self.fetch_hyp_api("getAllGameBasicInfo", params)
        return data

    # https://hyp-api.mihoyo.com/hyp/hyp-connect/api/getGameContent?launcher_id=jGHBHlcOq1&game_id=1Z8W5NHUQb&language=zh-cn
    async def get_game_content(self, game_id: str):
        params = {
            "game_id": game_id
        }
        data = await self.fetch_hyp_api("getGameContent", params)
        return data

    async def get_game_packages(self, game_id: str | None = None):
        if game_id is None:
            params = None
        else:
            params = {
                "game_id": game_id
            }
        data = await self.fetch_hyp_api("getGamePackages", params)
        return data

    async def get_game_branches(self, game_ids: list[str] | None = None):
        if game_ids is None:
            params = None
        else:
            params = {
                "game_ids[]": game_ids
            }
        data = await self.fetch_hyp_api("getGameBranches", params)
        return data

    async def fetch_hyp_chunk_api(self, path: str, params: dict | None = None):
        api_url = self.hyp_game_chunk_api_url / path
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                log.debug(f"编码 URL: {response.url}")
                response.raise_for_status()
                res = await response.json()
                log.debug(f"响应数据: {res}")
                if res.get("retcode") != 0:
                    raise Exception(f"API 请求错误: {res}")
                return res.get("data")
        
    async def post_hyp_chunk_api(self, path: str, params: dict | None = None):
        api_url = self.hyp_game_chunk_api_url / path
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                log.debug(f"编码 URL: {response.url}")
                response.raise_for_status()
                res = await response.json()
                log.debug(f"响应数据: {res}")
                if res.get("retcode") != 0:
                    raise Exception(f"API 请求错误: {res}")
                return res.get("data")

    async def get_game_chunk_bulid(self, branch: str, package_id: str, password: str, tag: str | None = None):
        params = {
            "branch": branch,
            "package_id": package_id,
            "password": password
        }
        if tag:
            params["tag"] = tag
        data = await self.fetch_hyp_chunk_api("getBuild", params)
        return data

    async def get_game_chunk_patch_bulid(self, branch: str, package_id: str, password: str, tag: str | None = None):
        params = {
            "branch": branch,
            "package_id": package_id,
            "password": password
        }
        # 神秘，前面都是get这里突然变成post
        data = await self.post_hyp_chunk_api("getPatchBuild", params)
        return data


HYP_API_DATA = {
    LaucherArea.CN: {
        "api_base": "hyp-api.mihoyo.com",
        "launcher_ids": {
            Launcher.CN: "jGHBHlcOq1",
            Launcher.BILIBILIYS: "umfgRO5gh5",
            Launcher.BILIBILISR: "6P5gHMNyK3",
            Launcher.BILIBILIZZZ: "xV0f4r1GT0",
        }
    },
    LaucherArea.GLOBAL: {
        "api_base": "hyp-api.mihoyo.com",
        "launcher_ids": {
            Launcher.GLOBAL: "VYTpXlbWo8",
        }
    },
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
    launcher = HYPLauncher(LaucherArea.CN, Launcher.CN)
    data = asyncio.run(launcher.get_games_basic_info("1Z8W5NHUQb"))
    data = asyncio.run(launcher.get_game_packages())
    data = asyncio.run(launcher.get_game_branches(["1Z8W5NHUQb"]))
    data = asyncio.run(launcher.get_game_chunk_bulid(
        "main", "FfGDa3bsvp", "FJCF1CT6Z4nz"))
    print(data)
