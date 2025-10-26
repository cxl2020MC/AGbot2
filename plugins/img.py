from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot.types.message import MessageEvent

import aiohttp

bot = plugin.Plugin("图片")


@bot.command("随机st", ["st"])
async def 随机色图(event: MessageEvent):
    req_data = {"proxy": "https://100148461.xyz/https://i.pixiv.re/"}
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.lolicon.app/setu/v2", json=req_data) as response:
            data = await response.json()
            log.debug(data)
            data = data["data"]
            message = f"""[CQ:image,file={data[0]["urls"]["original"]}]
pid: {data[0]["pid"]}
uid: {data[0]["uid"]}
标题: {data[0]["title"]}
作者: {data[0]["author"]}
标签: {data[0]["tags"]}"""
    await api.send_message(event, message)


@bot.command("获取bing壁纸", ["bing"])
async def 获取bing壁纸(event: MessageEvent):
    api_url = 'https://cn.bing.com/HPImageArchive.aspx'
    params = {'format': 'js', 'idx': 0, 'n': 1, 'mkt': 'zh-CN'}
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, params=params) as response:
            data = await response.json()
            log.debug(data)
            img_data = data["images"][0]
            url = 'https://cn.bing.com' + img_data["url"]
            url = url.replace('_1920x1080', '_UHD')
            message = f"""[CQ:image,file={url}]
{img_data["title"]}
{img_data["copyright"]}"""
            await api.send_message(event, message)