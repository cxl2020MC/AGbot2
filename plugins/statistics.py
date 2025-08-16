from AGbot import plugin
from AGbot.log import logger as log
from AGbot import api
from AGbot.event import GroupMessageEvent

import time

bot = plugin.Plugin("统计")


start_time = time.time()
data = {
    "group_message_count": 0,
}

@bot.on_message("group")
async def 事件统计(event: GroupMessageEvent) -> None:
    # log.info(f"{event.get_username()}在群{await api.获取群名称(event.group_id)}发送了消息")
    data["group_message_count"] += 1
    log.debug(f"群消息数: {data['group_message_count']}")

@bot.command("统计", ["统计"])
async def 统计(event: GroupMessageEvent) -> None:
    run_time = time.time() - start_time
    await api.send_message(event, f"""bot运行时间: {int(run_time/60/60/24)}天{int(run_time/60/60%24)}小时{int(run_time/60%60)}分{int(run_time%60)}秒
处理群消息数: {data['group_message_count']}
共处理了： {len(api.群信息缓存)} 个群的消息 """)