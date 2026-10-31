from typing import TYPE_CHECKING

from .log import logger as log
from .types import bot_event
from .types.qq_events import qq_event, qq_message, qq_ready_event

if TYPE_CHECKING:
    from .qq_bot import QQ_Bot


async def handle_event(
    event_type: qq_event.QQEventType, event_data: dict, bot_obj: QQ_Bot
) -> None:
    match event_type:
        case qq_event.QQEventType.C2C_MESSAGE_CREATE:
            log.info(f"收到 C2C 消息: {event_data}")
        case qq_event.QQEventType.GROUP_MESSAGE_CREATE:
            event = qq_message.GroupMessage.model_validate(event_data)
            log.info(
                f"收到群 {event.group_openid} 内 {event.author.username}({event.author.member_openid} {event.author.union_openid}))[{event.author.member_role.name if event.author.member_role else '未知'}] 消息: {event.content}"
            )
            await event_handle(
                qq_event.QQEventType.GROUP_MESSAGE_CREATE, event_data, bot_obj
            )
            await handle_message(
                [bot_event.MessageEventType.GROUP_MESSAGE], event, bot_obj
            )
        case qq_event.QQEventType.GROUP_AT_MESSAGE_CREATE:
            event = qq_message.GroupMessage.model_validate(event_data)
            log.info(f"收到群 @ 消息: {event_data}")
            await event_handle(
                qq_event.QQEventType.GROUP_AT_MESSAGE_CREATE, event_data, bot_obj
            )
            await handle_message(
                [
                    bot_event.MessageEventType.GROUP_AT_MESSAGE,
                    bot_event.MessageEventType.GROUP_MESSAGE,
                ],
                event,
                bot_obj,
            )
        case qq_event.QQEventType.READY:
            event = qq_ready_event.SessionData.model_validate(event_data)
            log.info(
                f"收到 READY 事件: {event.user.username}({event.user.id}) 已登录, session_id: {event.session_id}, shard: {event.shard}"
            )

        case _:
            log.info(f"收到未知事件类型: {event_type}, 数据: {event_data}")

    # await event_handle(event_type, event_data, bot_obj)


async def event_handle(
    event_type: qq_event.QQEventType, event_data: dict, bot_obj: QQ_Bot
) -> None:
    plugin_manager = bot_obj.plugin_manager
    await plugin_manager.handle_event(event_type, event_data)


async def handle_message(
    event_types: list[bot_event.MessageEventType],
    event_data: qq_message.Message,
    bot_obj: QQ_Bot,
) -> None:
    plugin_manager = bot_obj.plugin_manager
    await plugin_manager.handle_message_event(event_types, event_data)

