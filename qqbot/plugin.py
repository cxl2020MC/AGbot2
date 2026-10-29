import collections.abc
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Concatenate

from .log import logger as log
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

    async def handle_message_event(self, event_data: QQEventType):
        for plugin in self.plugins:
            await plugin._message_event_handler(event_data, self.bot_obj)


class Plugin:
    def __init__(self, name, description, version: str | None = None):
        self.name = name
        self.description = description
        self.version = version
        # self._bot = bot
        self._EventListeners: dict[QQEventType, list[EventListener]] = {}
        self._MessageEventListeners: dict[QQEventType, list[EventListener]] = {}
        self._CommandEventListeners: dict[list[str], list[Command]] = {}

    def register_event_listener(self, event_type: QQEventType, listener: EventListener):
        if event_type not in self._EventListeners:
            self._EventListeners[event_type] = []
        self._EventListeners[event_type].append(listener)

    def get_event_listeners(self, event_type: QQEventType):
        return self._EventListeners.get(event_type, [])

    def get_all_event_listeners(self):
        return self._EventListeners

    def register_command_event_listener(self, commands: list[str], listener: Command):
        if commands not in self._CommandEventListeners:
            self._CommandEventListeners[tuple(commands)] = []
        self._CommandEventListeners[tuple(commands)].append(listener)

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

    def on_message(self, name, message_type):
        def decorator(func):
            event_name = f"message_{name}({message_type})"
            listener = EventListener(event_name, func)
            self.register_event_listener(QQEventType.GROUP_MESSAGE_CREATE, listener)
            return func

        return decorator

    def on_command(
        self,
        command: list[str],
        command_name: str | None = None,
        command_description: str | None = None,
    ):

        def decorator(func: MeaasgePluginEventListener):
            # event_name = f"command_{command_name or command}"
            # listener = EventListener(event_name, func)
            # self.register_event_listener(QQEventType.GROUP_MESSAGE_CREATE, listener)
            return func

        return decorator

    async def _event_listener_handler(
        self, event_type: QQEventType, event_data: dict, bot_obj
    ):
        # listeners = self.get_event_listeners(event_type)
        for listener in self.get_event_listeners(event_type):
            await listener.listener(event_data, bot_obj)

    async def _message_event_handler(self, event_data, bot_obj):
        for listener in self.get_event_listeners(QQEventType.GROUP_MESSAGE_CREATE):
            await listener.listener(event_data, bot_obj)

    async def _command_event_handler(self, event_data: qq_message.Message, bot_obj):
        if event_data.content.startswith("/"):
            command_text = event_data.content.strip().split()[0]
            for command in self.get_command_event_listeners(command_text) or []:
                await command.function(event_data, bot_obj)


class EventListener:
    def __init__(
        self,
        event_name,
        listener: PluginEventListener,
    ):
        self.event_name = event_name
        self.listener = listener
        self.__call__ = self.listener

    # def __call__(self, *args, **kwargs):
    #     return self.listener(*args, **kwargs)

    def __str__(self):
        return f"EventListener(event_name={self.event_name}, listener={self.listener})"


@dataclass
class Command:
    function: MeaasgePluginEventListener

    command: str
    command_name: str | None = None
    command_description: str | None = None
