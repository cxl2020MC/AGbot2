import time
from AGbot import plugin
from AGbot.event import MessageEvent
from AGbot.log import logger as log
from AGbot import broswer
from AGbot import api
from AGbot import command_tools


bot = plugin.Plugin("Test")


@bot.command("网页截图", ["网页截图"])
async def 网页截图(event: MessageEvent):
    command = command_tools.Command(event.raw_message)
    url = command.get_arg(0)
    timeout = int(command.get_kwarg("timeout", "t", "30000") or 30000)
    no_wait = command.get_kwarg_bool("no_wait", "n")
    log.debug(url)
    log.debug(timeout)
    base64_image = await broswer.屏幕截图(url, timeout=timeout, no_wait=no_wait)
    log.debug(base64_image)
    await api.send_message(event, f"[CQ:image,file=base64://{base64_image}]")