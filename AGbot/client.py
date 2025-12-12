from aiohttp import web

from .log import logger as log
from . import handler
from . import config


async def main(request):
    data = await request.json()
    log.debug(f"收到 JSON 事件数据: {data}")
    await handler.main(data)

    return web.json_response({"status": "OK"})

async def on_app_startup(app: web.Application):
    """Application startup callback function"""
    log.success("http服务器已启动")

app = web.Application()
app.add_routes([web.post('/', main)])

app.on_startup.append(on_app_startup)

def run():
    log.info(f"启动http服务器: {config.HOST}:{config.PORT}")
    web.run_app(app, host=config.HOST, port=config.PORT)

