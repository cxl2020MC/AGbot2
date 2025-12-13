import asyncio
import aiofiles

import random
import json
from AGbot import utils
from AGbot.log import logger as log
import genshin
from pydantic import BaseModel
from typing import Literal


class Config(BaseModel):
    user: int
    group: int
    rewards: list[Game]


class Game(BaseModel):
    region: Literal["cn", "os"]
    games: list[Literal["ys", "sr", "zzz"]]
    cookie: str


async def get_config():
    config_path = await utils.get_data_path() / "rewards.json"
    async with aiofiles.open(config_path, "r") as f:
        config = json.loads(await f.read())
        config_data = [Config.model_validate(i) for i in config]
        return config_data


async def main():
    client = genshin.Client(lang="zh-cn")

    client.region = genshin.Region.CHINESE
    client.game = genshin.Game.GENSHIN
    configs = await get_config()
    log.debug(f"签到配置: {configs}")
    for config in configs:
        log.debug(f"签到用户: {config.user}")
        for reward in config.rewards:
            log.debug(f"开始签到: {reward.region}")
            region_map = {"cn": genshin.Region.CHINESE, "os": genshin.Region.OVERSEAS}
            client.region = region_map[reward.region]
            log.debug(f"当前签到区域: {client.region}")
            client.set_cookies(reward.cookie)
            for game in reward.games:
                game_map = {
                    "ys": genshin.Game.GENSHIN,
                    "sr": genshin.Game.STARRAIL,
                    "zzz": genshin.Game.ZZZ
                }
                game = game_map[game]
                log.debug(f"开始签到: {game}")
                client.game = game
                signed_in, claimed_rewards = await client.get_reward_info()
                log.debug(f"签到状态: {signed_in} | 累计签到天数: {claimed_rewards}")
                try:
                    reward = await client.claim_daily_reward(game=game)
                except genshin.AlreadyClaimed:
                    log.warning("每日奖励已领取")
                else:
                    log.success(f"领取成功 {reward.name}x{reward.amount}")
                # get all claimed rewards
                await asyncio.sleep(5)
                



        
