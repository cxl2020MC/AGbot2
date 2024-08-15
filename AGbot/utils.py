import aiohttp


def set_ws(websocket: aiohttp.ClientWebSocketResponse):
    global ws
    ws = websocket

def get_ws() -> aiohttp.ClientWebSocketResponse:
    return ws