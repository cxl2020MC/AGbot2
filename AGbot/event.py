from . import api
class Event:
    def __init__(self, data) -> None:
        self.data = data


class MessageEvent(Event):
    def __init__(self, data: dict) -> None:
        super().__init__(data)
        self.message: str = data.get("message", "")
        self.raw_message: list = data.get("raw_message", [])
        # self.message = self.raw_message
        self.message_id: int | None = data.get("message_id")
        self.sender: dict = data.get("sender", {})
        self.user_id = self.sender.get("user_id")
        self.sender_name = self.sender.get("nickname")
        self.sender_card = self.sender.get("card")
        
    def get_username(self, sender: dict) -> str:
        return self.sender.get("card", "") or self.sender.get("nickname", "")

