from qqbot import plugin, qq_api
from qqbot.qq_bot import QQ_Bot

# from qqbot.types.bot_event import MessageEventType
# from qqbot.types.qq_api import send_message
from qqbot.types.qq_events import qq_message
from qqbot.utils import browser

# lazy import os

plugin = plugin.Plugin("browser", "一个简单的浏览器插件", "1.0.0")


@plugin.on_command(("screenshot",), "网页截图", "网页截图命令")
async def screenshot_command(event_data: qq_message.Message, bot: QQ_Bot):
    print(event_data)
    if isinstance(event_data, qq_message.GroupMessage):
        url = event_data.content.strip().split()[1]
        img_bytes = await browser.screenshot(url)
        await (await bot.qq_api.get_file_uploader()).auto_update_file(
            type=qq_api.file_update.ApiType.GROUP,
            open_id=event_data.group_openid,
            file_type=qq_api.file_update.FileType.图片,
            file_name="screenshot.jpg",
            file_data=img_bytes,
            srv_send_msg=True,
        )
