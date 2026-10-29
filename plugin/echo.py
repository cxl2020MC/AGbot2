from qqbot import plugin
from qqbot.qq_bot import QQ_Bot
from qqbot.types.qq_events import qq_message

plugin = plugin.Plugin("echo", "一个简单的回声插件", "1.0.0")


@plugin.on_message("echo", "text")
async def echo_message(event_data: qq_message.GroupMessage, bot: QQ_Bot):
    print(event_data)
    message_content = event_data.get("content", "")
    group_openid = event_data.get("group_openid", "")
    if message_content and group_openid:
        await bot.qq_api.send_group_message(group_openid, {"content": message_content})
