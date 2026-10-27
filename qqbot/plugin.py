import collections.abc
from typing import Any

from .types.qq_event import QQEventType


class PluginManager:
    def __init__(self):
        self.plugins: list[Plugin] = []

    def add_plugin(self, plugin_class: Plugin, bot):
        # plugin = plugin_class(bot)
        self.plugins.append(plugin_class)
        # return plugin

    async def handle_event(self, event_type: QQEventType, event_data: dict, bot_obj):
        for plugin in self.plugins:
            await plugin._event_listener_handler(event_type, event_data, bot_obj)

    async def handle_message_event(self, event_data: QQEventType, bot_obj):
        for plugin in self.plugins:
            await plugin._message_event_handler(event_data, bot_obj)

class Plugin:
    def __init__(self, name, description, version: str | None = None):
        self.name = name
        self.description = description
        self.version = version
        # self._bot = bot
        self._EventListeners: dict[QQEventType, list[EventListener]] = {}

    def register_event_listener(self, event_type: QQEventType, listener: EventListener):
        if event_type not in self._EventListeners:
            self._EventListeners[event_type] = []
        self._EventListeners[event_type].append(listener)

    def get_event_listeners(self, event_type: QQEventType):
        return self._EventListeners.get(event_type, [])

    def get_all_event_listeners(self):
        return self._EventListeners

    def __str__(self):
        return f"Plugin(name={self.name}, description={self.description}, version={self.version})"

    def on_message(self, name, message_type):
        def decorator(func):
            event_name = f"message_{name}({message_type})"
            listener = EventListener(event_name, func)
            self.register_event_listener(QQEventType.GROUP_MESSAGE_CREATE, listener)
            return func

        return decorator

    def on_command(self, command_name):
        pass

    async def _event_listener_handler(self, event_type: QQEventType, event_data: dict, bot_obj):
        # listeners = self.get_event_listeners(event_type)
        for listener in self.get_event_listeners(event_type):
            await listener.listener(event_data, bot_obj)

    async def _message_event_handler(self, event_data, bot_obj):
        for listener in self.get_event_listeners(QQEventType.GROUP_MESSAGE_CREATE):
            await listener.listener(event_data, bot_obj)


class EventListener:
    def __init__(
        self,
        event_name,
        listener: collections.abc.Callable[..., collections.abc.Awaitable[Any]],
    ):
        self.event_name = event_name
        self.listener = listener
        self.__call__ = self.listener

    # def __call__(self, *args, **kwargs):
    #     return self.listener(*args, **kwargs)

    def __str__(self):
        return f"EventListener(event_name={self.event_name}, listener={self.listener})"
