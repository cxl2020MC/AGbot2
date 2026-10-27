from typing import TYPE_CHECKING

from . import plugin
from .log import logger as log
from .types import message, qq_event, ready_event

if TYPE_CHECKING:
    from .qq_bot import QQ_Bot


async def handle_event(event_type, event_data, bot_obj) -> None:
    match event_type:
        case qq_event.QQEventType.C2C_MESSAGE_CREATE:
            log.info(f"收到 C2C 消息: {event_data}")
        case qq_event.QQEventType.GROUP_MESSAGE_CREATE:
            event = message.GroupMessage.model_validate(event_data)
            log.info(
                f"收到群 {event.group_openid} 内 {event.author.username}({event.author.member_openid} {event.author.union_openid}))[{event.author.member_role.name if event.author.member_role else '未知'}] 消息: {event.content}"
            )
        case qq_event.QQEventType.GROUP_AT_MESSAGE_CREATE:
            log.info(f"收到群 @ 消息: {event_data}")
        case qq_event.QQEventType.READY:
            event = ready_event.SessionData.model_validate(event_data)
            log.info(
                f"收到 READY 事件: {event.user.username}({event.user.id}) 已登录, session_id: {event.session_id}, shard: {event.shard}"
            )

        case _:
            log.info(f"收到未知事件类型: {event_type}, 数据: {event_data}")

    await event_handle(event_type, event_data, bot_obj)


async def event_handle(event_type, event_data, bot_obj: QQ_Bot) -> None:
    pulgin_manager = bot_obj.plugin_manager
    await pulgin_manager.handle_event(event_type, event_data, bot_obj)
