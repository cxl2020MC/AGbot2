from qqbot import http_client
from qqbot.log import logger as log

cilent = http_client.client


async def fetch_file(url: str) -> bytes:
    try:
        response = await cilent.get(url)
        response.raise_for_status()
        return await response.aread()
    except Exception:
        log.exception(f"从 {url} 获取文件失败")
        raise


# async def fetch_image(url: str) -> bytes:
#     try:
#         response = await cilent.get(url)
#         response.raise_for_status()
#         return await response.aread()
#     except Exception:
#         log.exception(f"从 {url} 获取图片失败")
#         raise
