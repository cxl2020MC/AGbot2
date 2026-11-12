from typing import TYPE_CHECKING

from .log import logger as log
from .types import bot_event
from .types.qq_events import qq_event, qq_message, qq_ready_event

if TYPE_CHECKING:
    from .qq_bot import QQ_Bot


async def handle_event(
    event_type: qq_event.QQEventType, event_data: dict | None, bot_obj: QQ_Bot
) -> None:
    if event_data is None:
        log.warning(f"收到事件 {event_type} 但没有数据")
        return
    match event_type:
        case qq_event.QQEventType.C2C_MESSAGE_CREATE:
            log.info(f"收到 C2C 消息: {event_data}")
        case qq_event.QQEventType.GROUP_MESSAGE_CREATE:
            event = qq_message.GroupMessage.model_validate(event_data)
            log.debug(f"收到群消息: {event}")
            group_info = await bot_obj.qq_api.get_group_info(event.group_openid)
            message_metadata: list[str] = [
                "消息ID: " + event.id,
                # "消息类型: " + event.message_type.name,
                f"消息索引: {event.message_scene.msg_idx}",
                f"引用目标消息索引: {event.message_scene.ref_msg_idx}",
            ]
            if event.msg_elements:
                message_metadata.append(f"消息元素: {event.msg_elements}")
            if event.parallel_message:
                message_metadata.append(f"消息节点: {event.parallel_message.msg_nodes}")

            log.info(
                f"""收到群 {group_info.group_name}({event.group_openid}) 内 {event.author.username}({event.author.id} {event.author.member_openid} {event.author.union_openid})[{event.author.member_role.name if event.author.member_role else "未知"}] 的 {event.message_type.name} 消息: {event.content}
[{"]\n[".join(message_metadata)}]"""
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
    await plugin_manager.handle_command_event(event_data)
    await plugin_manager.handle_message_event(event_types, event_data)
