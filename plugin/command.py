lazy import sys

from qqbot import plugin
from qqbot.qq_bot import QQ_Bot

# from qqbot.types.bot_event import MessageEventType
from qqbot.types.qq_api import send_message
from qqbot.types.qq_events import qq_message

# lazy import os

plugin = plugin.Plugin("command", "一个简单的管理命令插件", "1.0.0")




@plugin.on_command(("reboot",), "reboot", "重启命令")
async def reboot_command(
    event_data: qq_message.GroupMessage | qq_message.Message, bot: QQ_Bot
):
    print(event_data)
    if isinstance(event_data, qq_message.GroupMessage):
        await bot.qq_api.send_group_message(
            event_data.group_openid, send_message.GroupMessage(content="正在重启...")
        )
        sys.exit(0)  # 退出程序，假设有外部进程管理器会自动重启
