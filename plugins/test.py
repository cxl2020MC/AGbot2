from AGbot import plugin
from AGbot.event import MessageEvent
from AGbot.log import logger as log
from AGbot import broswer
from AGbot import api
from AGbot import command_tools


bot = plugin.Plugin("Test")


@bot.command("网页截图", ["网页截图"])
async def 网页截图(event: MessageEvent):
    url = command_tools.Command(event.message).get_arg(1)
    base64_image = await broswer.屏幕截图(url)
    log.debug(base64_image)
    await api.send_message(event, f"[CQ:image,file=base64://{base64_image}]")