import collections.abc
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Concatenate

from .log import logger as log
from .types import bot_event
from .types.qq_events.qq_event import QQEventType

if TYPE_CHECKING:
    from .qq_bot import QQ_Bot
    from .types.qq_events import qq_message

type MeaasgePluginEventListener = collections.abc.Callable[
    Concatenate[qq_message.Message, QQ_Bot, ...], collections.abc.Awaitable[Any]
]

type PluginEventListener = collections.abc.Callable[
    Concatenate[dict, QQ_Bot, ...], collections.abc.Awaitable[Any]
]


class PluginManager:
    def __init__(self, bot_obj: QQ_Bot):
        self.plugins: list[Plugin] = []
        self.bot_obj = bot_obj

    def add_plugin(self, plugin_class: Plugin):
        # plugin = plugin_class(bot)
        self.plugins.append(plugin_class)
        # return plugin

    async def handle_event(self, event_type: QQEventType, event_data: dict):
        for plugin in self.plugins:
            await plugin._event_listener_handler(event_type, event_data, self.bot_obj)

    async def handle_message_event(
        self,
        message_event_types: list[bot_event.MessageEventType],
        event_data: qq_message.Message,
    ):
        for message_event_type in message_event_types:
            for plugin in self.plugins:
                await plugin._message_event_handler(
                    message_event_type, event_data, self.bot_obj
                )

    async def handle_command_event(self, event_data: qq_message.Message):
        for plugin in self.plugins:
            await plugin._command_event_handler(event_data, self.bot_obj)


class Plugin:
    def __init__(self, name, description, version: str | None = None):
        self.name = name
        self.description = description
        self.version = version
        # self._bot = bot
        self._EventListeners: dict[QQEventType, list[EventListener]] = {}
        self._MessageEventListeners: dict[
            bot_event.MessageEventType, list[MessageListener]
        ] = {}
        self._CommandEventListeners: dict[list[str], list[CommandListener]] = {}

    def register_event_listener(self, event_type: QQEventType, listener: EventListener):
        if event_type not in self._EventListeners:
            self._EventListeners[event_type] = []
        self._EventListeners[event_type].append(listener)

    def get_event_listeners(self, event_type: QQEventType):
        return self._EventListeners.get(event_type, [])

    def get_all_event_listeners(self):
        return self._EventListeners

    def get_message_listeners(self, event_types: list[bot_event.MessageEventType]):
        listeners = []
        for event_type in event_types:
            listeners.extend(self._MessageEventListeners.get(event_type, []))
        return listeners

    def register_message_event_listener(
        self, message_event_type: bot_event.MessageEventType, listener: MessageListener
    ):
        if message_event_type not in self._MessageEventListeners:
            self._MessageEventListeners[message_event_type] = []
        self._MessageEventListeners[message_event_type].append(listener)

    def get_all_message_listeners(self):
        return self._MessageEventListeners

    def register_command_event_listener(
        self, commands: list[str], listener: CommandListener
    ):
        if commands not in self._CommandEventListeners:
            self._CommandEventListeners[commands] = []
        self._CommandEventListeners[commands].append(listener)

    def get_all_command_event_listeners(self):
        return self._CommandEventListeners

    def get_command_event_listeners(self, command: str):
        for cmd, listeners in self._CommandEventListeners.items():
            if command in cmd:
                log.debug(f"找到命令 {command} : {listeners}")
                return listeners
        log.warning(f"未找到命令 {command}")
        # return self._CommandEventListeners.get(command, [])

    def __str__(self):
        return f"Plugin(name={self.name}, description={self.description}, version={self.version})"

    def on_message(
        self, name: str, message_types: list[bot_event.MessageEventType] | None = None
    ):
        if message_types is None:
            message_types = [
                bot_event.MessageEventType.PRIVATE_MESSAGE,
                bot_event.MessageEventType.GROUP_MESSAGE,
                bot_event.MessageEventType.GROUP_AT_MESSAGE,
            ]

        def decorator(func):
            for message_type in message_types:
                event_name = f"message_{name}({message_type})"
                listener = MessageListener(event_name, message_type, func)
                self.register_message_event_listener(message_type, listener)
            return func

        return decorator

    def on_command(
        self,
        command: list[str],
        command_name: str | None = None,
        command_description: str | None = None,
    ):

        def decorator(func: MeaasgePluginEventListener):
            self.register_command_event_listener(
                command,
                CommandListener(
                    function=func,
                    command=command[0],
                    command_name=command_name,
                    command_description=command_description,
                ),
            )
            return func

        return decorator

    async def _event_listener_handler(
        self, event_type: QQEventType, event_data: dict, bot_obj
    ):
        # listeners = self.get_event_listeners(event_type)
        for listener in self.get_event_listeners(event_type):
            await listener.listener(event_data, bot_obj)

    async def _message_event_handler(
        self,
        message_event_type: bot_event.MessageEventType,
        event_data: qq_message.Message,
        bot_obj,
    ):
        pass

    async def _command_event_handler(self, event_data: qq_message.Message, bot_obj):
        command_start_with = "/"
        if event_data.content.startswith(command_start_with):
            command_text = event_data.content.strip().split()[0][
                len(command_start_with) :
            ]
            for command in self.get_command_event_listeners(command_text) or []:
                await command.function(event_data, bot_obj)


@dataclass
class EventListener:
    event_name: str
    listener: PluginEventListener


@dataclass
class MessageListener:
    listener_name: str
    message_type: str
    listener: PluginEventListener


@dataclass
class CommandListener:
    function: MeaasgePluginEventListener

    command: str
    command_name: str | None = None
    command_description: str | None = None
