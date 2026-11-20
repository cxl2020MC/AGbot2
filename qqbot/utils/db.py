import os

from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from ..log import logger as log

# 建议从环境变量读取
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "AGbot2")

_client: AsyncMongoClient | None = None


async def init_db() -> None:
    """在应用启动时调用一次。AsyncMongoClient 是惰性连接，此处不会真正建立 TCP 连接。"""
    global _client
    log.info("初始化数据库连接池……")
    log.debug(f"MongoDB URI: {MONGODB_URI}")
    if _client is not None:
        log.warning("数据库已初始化，重复调用 init_db() 将被忽略。")
        return
    _client = AsyncMongoClient(
        MONGODB_URI,
        # maxPoolSize=50,  # 异步驱动不需要过大，50 通常足够覆盖多数场景
        # minPoolSize=2,  # 保持少量热连接，降低冷启动延迟
        # maxIdleTimeMS=45000,  # 空闲超过 45s 的连接由驱动自动回收
        # serverSelectionTimeoutMS=5000,  # 快速失败，避免启动时长时间无响应
    )
    # 启动时主动 ping 一次，尽早暴露配置/网络/认证问题
    await _client.admin.command("ping")


async def close_db() -> None:
    """在应用关闭时调用，释放连接池。"""
    global _client
    if _client is not None:
        await _client.close()
        _client = None


async def get_client() -> AsyncMongoClient:
    if _client is None:
        await init_db()  # 尝试获取数据库对象，如果未初始化则抛出异常
        # raise RuntimeError("数据库未初始化，请先调用 init_db()。")
    assert _client is not None
    return _client


async def get_db() -> AsyncDatabase:
    """获取数据库对象，默认使用 DB_NAME 指定的数据库。"""
    return (await get_client()).get_database(DB_NAME)
