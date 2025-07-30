from . import api


class Event:
    def __init__(self, data: dict) -> None:
        self.data: dict = data
        self.type: str = data.get("post_type", "")
        self.sub_type: str = data.get("sub_type", "")


class MessageEvent(Event):
    def __init__(self, data: dict) -> None:
        super().__init__(data)
        self.message_type: str = data.get("message_type", "")
        self.message: list[dict] = data.get("message", [])
        self.raw_message: str = data.get("raw_message", "")
        self.message_id: int | None = data.get("message_id")
        self.sender: dict = data.get("sender", {})
        self.user_id: int | None = self.sender.get("user_id")
        self.sender_nickname: str | None = self.sender.get("nickname")

    def get_username(self) -> str:
        return self.sender.get("card", "") or self.sender.get("nickname", "")


class GroupMessageEvent(MessageEvent):
    def __init__(self, data: dict) -> None:
        super().__init__(data)
        self.group_id: int | None = data.get("group_id")
        self.anonymous: dict | None = data.get("anonymous")
        self.sender_card: str | None = self.sender.get("card")

    @property
    async def group_name(self) -> str:
        return await api.获取群名称(self.group_id)


class PrivateMessageEvent(MessageEvent):
    def __init__(self, data: dict) -> None:
        super().__init__(data)
        # self.user_id: int | None = data.get("user_id")

class Sender:
    def __init__(self, sender: dict) -> None:
        self.user_id: int | None = sender.get("user_id")
        self.nickname: str | None = sender.get("nickname")


class GroupSender(Sender):
    def __init__(self, sender: dict) -> None:
        super().__init__(sender)

        self.card: str | None = sender.get("card")
        self.sex: str | None = sender.get("sex")
        self.age: int | None = sender.get("age")
