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


class Launcher(Enum):
    CN = 1
    GLOBAL = 2
    BILIBILIYS = 3
    BILIBILISR = 4
    BILIBILIZZZ = 5


# https://github.com/Scighost/Starward/blob/main/src/Starward.Core/HoYoPlay/HoYoPlayClient.cs
class HYPLauncher:
    def __init__(self, area: LaucherArea, launcher: Launcher, language: str = "zh-cn"):
        self.area = area
        self.launcher = launcher
        self.api_base = self._get_hyp_api_base(area)
        self.launcher_id = self._get_launcher_id(launcher)
        self.hyp_api_url = self.get_hyp_api_url()
        self.hyp_game_chunk_api_base = self._get_game_chunk_api_base(area)
        self.hyp_game_chunk_api_url = self.get_hyp_game_chunk_api_url()
        self.language = language

    @staticmethod
    def _get_launcher_id(laucher: Launcher) -> str:
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
    def _get_hyp_api_base(area: LaucherArea) -> str:
        match area:
            case LaucherArea.CN:
                return "hyp-api.mihoyo.com"
            case LaucherArea.GLOBAL:
                return "sg-hyp-api.hoyoverse.com"
            case _:
                raise Exception("不支持的启动器")

    @staticmethod
    def _get_game_chunk_api_base(area: LaucherArea) -> str:
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

    async def get_game_deprecated_file_configs(self, game_ids: list[str] | None = None):
        if game_ids is None:
            params = {}
        else:
            params: dict = {
                "game_ids[]": game_ids
            }
        if self.launcher in [Launcher.BILIBILISR, Launcher.BILIBILIYS, Launcher.BILIBILIZZZ]:
            params.update({
                "channel": 14,
                "sub_channel": 0
            })
        else:
            params.update({
                "channel": 1,
                "sub_channel": 1
            })
        data = await self.fetch_hyp_api("getGameDeprecatedFileConfigs", params)
        return data

    async def get_game_configs(self, game_ids: list[str] | None = None):
        if game_ids is None:
            params = None
        else:
            params = {
                "game_ids[]": game_ids
            }
        data = await self.fetch_hyp_api("getGameConfigs", params)
        return data

    async def get_game_scan_info(self, game_ids: str):
        if game_ids is None:
            params = None
        else:
            params = {
                "game_ids[]": game_ids
            }
        data = await self.fetch_hyp_api("getGameScanInfo", params)

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
            async with session.post(api_url, params=params) as response:
                log.debug(f"编码 URL: {response.url}")
                response.raise_for_status()
                res = await response.json()
                log.debug(f"响应数据: {res}")
                if res.get("retcode") != 0:
                    raise Exception(f"API 请求错误: {res}")
                return res.get("data")

    async def get_game_chunk_build(self, branch: str, package_id: str, password: str, tag: str | None = None):
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


if __name__ == "__main__":
    launcher = HYPLauncher(LaucherArea.CN, Launcher.CN)
    data = asyncio.run(launcher.get_games_basic_info("1Z8W5NHUQb"))
    data = asyncio.run(launcher.get_game_packages())
    data = asyncio.run(launcher.get_game_branches(["1Z8W5NHUQb"]))
    data = asyncio.run(launcher.get_game_chunk_build(
        "main", "FfGDa3bsvp", "FJCF1CT6Z4nz"))
    print(data)
