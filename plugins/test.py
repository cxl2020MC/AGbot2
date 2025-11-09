import time
from AGbot import plugin
from AGbot.types.message_event import MessageEvent
from AGbot.log import logger as log
from AGbot import browser
from AGbot import api
from AGbot import command_utils


bot = plugin.Plugin("Test")


@bot.command("网页截图", ["网页截图"])
async def 网页截图(event: MessageEvent):
    command = command_utils.Command(event.raw_message)
    url = command.get_arg(0)
    if str(url) in "file://":
        await api.send_message(event, "禁止使用此功能！")
        return
    timeout = int(command.get_kwarg("timeout", "t", "30000") or 30000)
    no_wait = command.get_kwarg_bool("no_wait", "n")
    log.debug(url)
    log.debug(timeout)
    base64_image = await browser.screenshot(url, timeout_ms=timeout, no_wait=no_wait)
    # log.debug(base64_image)
    await api.send_message(event, f"[CQ:image,file=base64://{base64_image}]")