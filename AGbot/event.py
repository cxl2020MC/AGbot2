
class Event:
    def __init__(self, data) -> None:
        self.data = data


class MessageEvent(Event):
    def __init__(self, data) -> None:
        super().__init__(data)
        self.message = data["message"]
        self.raw_message = data["raw_message"]
        self.message = self.raw_message
        self.message_id = data["message_id"]
        


