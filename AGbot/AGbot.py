import aiohttp
from . import handler

class App:
    def __init__(self, ws_url: str|None = "ws://localhost:3001/") -> None:
        self.ws_url = ws_url
        self.commend = []

    async def run(self):
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.ws_url) as ws:
                async for msg in ws:
                    # print(msg.type)
                    data = msg.json()
                    print(data)
                    handler.main(self, data)
                    # if msg.type == aiohttp.WSMsgType.TEXT:
                        # print(msg.json())
                    # elif msg.type == aiohttp.WSMsgType.ERROR:
                        # break
    
    def commend(self, commend):
        pass
