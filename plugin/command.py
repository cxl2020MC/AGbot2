lazy import sys

lazy import anyio

from qqbot import plugin, qq_api
from qqbot.qq_bot import QQ_Bot

# from qqbot.types.bot_event import MessageEventType
from qqbot.types.qq_api import send_message
from qqbot.types.qq_events import qq_message

# lazy import os

plugin = plugin.Plugin("command", "一个简单的管理命令插件", "1.0.0")


@plugin.on_command(("reboot",), "reboot", "重启命令")
async def reboot_command(event_data: qq_message.Message, bot: QQ_Bot):
    print(event_data)
    if isinstance(event_data, qq_message.GroupMessage):
        await bot.qq_api.send_group_message(
            event_data.group_openid, send_message.GroupMessage(content="正在重启...")
        )
        sys.exit(0)  # 退出程序，假设有外部进程管理器会自动重启


@plugin.on_command(("img_send_test",), "img send test", "图片发送测试命令")
async def img_send_test_command(event_data: qq_message.Message, bot: QQ_Bot):
    print(event_data)
    if isinstance(event_data, qq_message.GroupMessage):
        await (await bot.qq_api.get_file_uploader()).update_small_file(
            type=qq_api.file_update.ApiType.GROUP,
            open_id=event_data.group_openid,
            file_type=qq_api.file_update.FileType.图片,
            file_name="test.jpg",
            file_data=await anyio.open_file("data/test.jpg", "rb"),
            srv_send_msg=True,
        )


@plugin.on_command(("video_send_test",), "video send test", "视频发送测试命令")
async def video_send_test_command(event_data: qq_message.Message, bot: QQ_Bot):
    print(event_data)
    if isinstance(event_data, qq_message.GroupMessage):
        await (await bot.qq_api.get_file_uploader()).update_large_file(
            type=qq_api.file_update.ApiType.GROUP,
            open_id=event_data.group_openid,
            file_type=qq_api.file_update.FileType.视频,
            file_name="test.webm",
            file_data=await anyio.open_file("data/test.webm", "rb"),
            srv_send_msg=True,
        )
