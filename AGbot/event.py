from . import api
class Event:
    def __init__(self, data) -> None:
        self.data = data


class MessageEvent(Event):
    def __init__(self, data: dict) -> None:
        super().__init__(data)
        self.message: list = data.get("message", [])
        self.raw_message: str = data.get("raw_message", "")
        # self.message = self.raw_message
        self.message_id: int | None = data.get("message_id")
        self.sender: dict = data.get("sender", {})
        self.user_id: int | None = self.sender.get("user_id")
        self.sender_nickname: str | None = self.sender.get("nickname")
        self.sender_card: str | None = self.sender.get("card")
        
    def get_username(self) -> str:
        return self.sender.get("card", "") or self.sender.get("nickname", "")

