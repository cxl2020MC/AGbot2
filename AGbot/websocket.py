
ws = None

def set_ws(ws_):
    global ws
    ws = ws_

async def get_ws():
    if ws is None:
        raise Exception("Websocket连接已断开")
    return ws