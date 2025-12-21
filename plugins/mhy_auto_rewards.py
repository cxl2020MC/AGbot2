import asyncio
import aiofiles
import random
import traceback
import json
from AGbot import utils, api, plugin
from AGbot.log import logger as log
import genshin
import schedule
from pydantic import BaseModel
from typing import Literal


type Game = Literal["ys", "sr", "zzz"]
type Region = Literal["cn", "os"]


class Config(BaseModel):
    user: int
    group: int
    rewards: list[Reward]


class Reward(BaseModel):
    region: Region
    games: list[Game]
    cookie: str


async def load_config():
    """加载 rewards.json 配置文件"""
    config_path = await utils.get_data_path() / "rewards.json"
    async with aiofiles.open(config_path, "r") as f:
        data = json.loads(await f.read())
        return [Config.model_validate(i) for i in data]


async def handle_error(e, group_id: int = 1053371582):
    """处理错误"""
    msg = f"""签到失败: {repr(e)}
{traceback.format_exc()}"""
    await api.send_group_message(group_id, msg)


def set_client_region(client: genshin.Client, region: Region):
    """设置客户端区域"""
    region_map = {"cn": genshin.Region.CHINESE, "os": genshin.Region.OVERSEAS}
    client.region = region_map[region]
    log.debug(f"已设置区域: {region} -> {client.region}")


def set_client_game(client: genshin.Client, game: Game):
    """设置客户端游戏"""
    game_map = {
        "ys": genshin.Game.GENSHIN,
        "sr": genshin.Game.STARRAIL,
        "zzz": genshin.Game.ZZZ
    }
    client.game = game_map[game]
    log.debug(f"已设置游戏: {game} -> {client.game}")


async def sign_in(client: genshin.Client, config: Config, reward: Reward):
    """签到"""
    log.debug(f"开始签到: {reward.region}")
    for game in reward.games:
        log.debug(f"开始签到游戏: {game}")
        set_client_region(client, reward.region)
        set_client_game(client, game)
        client.set_cookies(reward.cookie)
        msg = f"当前签到目标: {reward.region} | {game}\n"
        try:
            signed_in, claimed_rewards = await client.get_reward_info()
            log.debug(f"签到状态: {signed_in} | 累计签到天数: {claimed_rewards}")
            msg += f"累计签到天数: {claimed_rewards}\n"

            reward_item = await client.claim_daily_reward(game=client.game)
            log.success(
                f"领取成功: {reward_item.name}x{reward_item.amount}")
            msg += f"签到成功: {reward_item.name}x{reward_item.amount}"
        except genshin.AlreadyClaimed:
            log.warning("每日奖励已领取")
            msg += f"""你今日已经签到过了"""
        await api.send_group_message(config.group, msg)
        await asyncio.sleep(random.uniform(3, 8))


async def main():
    client = genshin.Client(lang="zh-cn")
    configs = await load_config()
    log.debug(f"签到配置: {configs}")

    for config in configs:
        log.debug(f"签到用户: {config.user} | 签到群: {config.group}")
        await api.send_group_message(config.group, f"[CQ:at,qq={config.user}] 签到提醒：开始执行米游社自动签到")
        for reward in config.rewards:
            try:
                await sign_in(client, config, reward)
            except Exception as e:
                await handle_error(e, config.group)


async def auto_sign_in():
    """自动签到"""
    await asyncio.sleep(random.uniform(0, 300))
    try:
        await main()
    except Exception as e:
        await handle_error(e)


def schedule_main():
    log.info("开始执行米游社自动签到")
    asyncio.run(auto_sign_in())


bot = plugin.Plugin("米游社自动签到")


@bot.command("手动触发米游社签到", ["米游社签到"])
async def qd(event: plugin.MessageEvent):
    await main()


schedule.every().day.at("07:30").do(schedule_main)
