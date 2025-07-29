from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot.event import MessageEvent

import aiohttp

bot = plugin.Plugin("图片")


@bot.command("随机st", ["st"])
async def 随机色图(event: MessageEvent):
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.lolicon.app/setu/v2") as response:
            data = await response.json()
            log.debug(data)
            message = f"""[CQ:image,file={data[0]["urls"]["original"]}]
pid: {data[0]["pid"]}
uid: {data[0]["uid"]}
标题: {data[0]["title"]}
作者: {data[0]["author"]}
标签: {data[0]["tags"]}"""
    await api.send_message(event, message)
