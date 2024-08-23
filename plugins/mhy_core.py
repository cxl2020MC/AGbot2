import aiohttp

async def get_hyp_api_url(区服: str, api: str, language: str = "zh-cn"):
    if 区服 == '国服':
        host = "hyp-api.mihoyo.com"
        laucher_id = "jGHBHlcOq1"
    else:
        raise Exception("不支持的启动器")
    url = f"https://{host}/hyp/hyp-connect/api/{api}?laucher_id={laucher_id}&language={language}"
    return url

async def get_game_id(游戏):
    if 游戏 == "原神":
        return "1Z8W5NHUQb"
    else:
        raise Exception("不支持的游戏")


# https://hyp-api.mihoyo.com/hyp/hyp-connect/api/getGameContent?launcher_id=jGHBHlcOq1&game_id=1Z8W5NHUQb&language=zh-cn
async def 获取资讯(启动器, 游戏, language="zh-cn"):
    url = await get_hyp_api_url(启动器, "getGameContent", language) + f"&game_id={await get_game_id(游戏)}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

