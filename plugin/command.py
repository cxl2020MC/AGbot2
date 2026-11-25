lazy import asyncio
lazy import sys

lazy import anyio

from qqbot import plugin, qq_api

# from qqbot.types.bot_event import MessageEventType
from qqbot.types.qq_api import api_type, send_message
from qqbot.types.qq_events import qq_message
lazy from qqbot.qq_bot import QQ_Bot

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


@plugin.on_command(
    ("asyncio_call_graph",), "asyncio call graph", "获取当前的 asyncio 调用图"
)
async def asyncio_call_graph_command(event_data: qq_message.Message, bot: QQ_Bot):
    print(event_data)
    if isinstance(event_data, qq_message.GroupMessage):
        await bot.qq_api.send_group_message(
            event_data.group_openid,
            send_message.GroupMessage(content=asyncio.format_call_graph()),
        )


@plugin.on_command(
    ("asyncio_get_all_tasks",), "asyncio get all tasks", "获取当前的 asyncio 所有任务"
)
async def asyncio_get_all_tasks_command(event_data: qq_message.Message, bot: QQ_Bot):
    print(event_data)
    if isinstance(event_data, qq_message.GroupMessage):
        await bot.qq_api.send_group_message(
            event_data.group_openid,
            send_message.GroupMessage(content="\n".join(str(task) for task in asyncio.all_tasks())),
        )


@plugin.on_command(("img_send_test",), "img send test", "图片发送测试命令")
async def img_send_test_command(event_data: qq_message.Message, bot: QQ_Bot):
    print(event_data)
    if isinstance(event_data, qq_message.GroupMessage):
        await (await bot.qq_api.get_file_uploader()).update_small_file(
            type=api_type.ApiType.GROUP,
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
            type=api_type.ApiType.GROUP,
            open_id=event_data.group_openid,
            file_type=qq_api.file_update.FileType.视频,
            file_name="test.mp4",
            file_data=await anyio.open_file("data/test.mp4", "rb"),
            srv_send_msg=True,
        )
