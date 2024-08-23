import aiohttp

async def get_hyp_api_url(启动器: str):
    if 启动器 == '国服':
        return "https://hyp-api.mihoyo.com/hyp/hyp-connect/api/{api}?launcher_id=jGHBHlcOq1&language=zh-cn"

async def get_game_id(游戏):
    if 游戏 == "原神":
        return "1Z8W5NHUQb"

