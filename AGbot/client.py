from aiohttp import web

from .log import logger as log
from . import handler
from . import config


async def main(request):
    data = await request.json()
    log.debug(f"收到json消息: {data}")
    await handler.main(data)

    return web.json_response({"status": "OK"})

app = web.Application()
app.add_routes([web.post('/', main)])


def run():
    log.info(f"启动http服务器: {config.host}:{config.port}")
    web.run_app(app, host=config.host, port=config.port)

