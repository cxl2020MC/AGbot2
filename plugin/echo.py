from qqbot import plugin
from qqbot.qq_bot import QQ_Bot

# from qqbot.types.bot_event import MessageEventType
from qqbot.types.qq_api import send_message
from qqbot.types.qq_events import qq_message

plugin = plugin.Plugin("echo", "一个简单的回声插件", "1.0.0")


@plugin.on_command(("echo",), "echo", "回声命令")
async def echo_message(
    event_data: qq_message.GroupMessage | qq_message.Message, bot: QQ_Bot
):
    print(event_data)
    if isinstance(event_data, qq_message.GroupMessage):
        message_content = event_data.content
        group_openid = event_data.group_openid
        if message_content and group_openid:
            await bot.qq_api.send_group_message(
                group_openid, send_message.GroupMessage(content=message_content)
            )
