from AGbot import client, api
from AGbot.log import logger as log
import os

routes = client.web.RouteTableDef()


@routes.post('/push')
async def push(request: client.web.Request):
    data = await request.json()
    log.debug(f"收到 push 事件数据: {data}")
    push_token = os.getenv("PUSH_TOKEN")
    if push_token and data.get("token") == push_token:
        log.info("验证 push token 成功")
        push_data = await api.send_group_message(1053371582, f"收到 push 事件数据: {data}")
        return client.web.json_response({"status": "OK", "data": push_data})
    else:
        log.warning("push token 验证失败")
        return client.web.json_response({"status": "Error"})