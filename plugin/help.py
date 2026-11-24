from qqbot import plugin
from qqbot.utils import jinja_utils
from qqbot.qq_bot import QQ_Bot
from qqbot.types.qq_events import qq_message


plugin = plugin.Plugin("help", "一个简单的帮助插件", "1.0.0")

template = jinja_utils.env.get_template("help.html.jinja")


@plugin.on_command(("help", "帮助"), "帮助", "帮助命令")
async def help_command(event_data: qq_message.Message, bot: QQ_Bot):
    print(event_data)
    if isinstance(event_data, qq_message.GroupMessage):
        group_openid = event_data.group_openid
        help_content = template.render(
            plugin_list=bot.plugin_manager.plugins,
        )
        await bot.qq_api.send_group_message(
            group_openid, bot.qq_api.send_message.GroupMessage(content=help_content)
        )
