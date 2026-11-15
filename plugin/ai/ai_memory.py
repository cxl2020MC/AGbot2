from datetime import datetime
from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer
from pydantic_mongo import ObjectIdField

from qqbot.log import logger as log
from qqbot.utils import db

# 定义一个可复用的 ObjectId 类型
# type PyObjectId = Annotated[
#     ObjectId,
#     BeforeValidator(lambda v: ObjectId(v) if isinstance(v, (str, ObjectId)) else v),
#     PlainSerializer(lambda v: str(v), return_type=str, when_used="json"),
# ]

type PyObjectId = ObjectIdField

db_collection: db.AsyncCollection | None = None


async def init():
    global db_collection
    db_collection = (await db.get_db()).get_collection("ai_memory")
    await db_collection.create_index({"keywords": 1})


async def get_collection() -> db.AsyncCollection:
    if db_collection is None:
        await init()
    assert db_collection is not None
    return db_collection


class Memory(BaseModel):
    id: PyObjectId = Field(
        alias="_id", default_factory=ObjectIdField, description="记忆ID"
    )
    level: int = Field(
        default=1, ge=1, le=5, description="记忆等级, 1-5, 1为最不重要, 5为最重要"
    )
    keywords: list[str]
    content: str
    create_time: datetime = Field(default_factory=datetime.now)
    latest_read_time: datetime = Field(default_factory=datetime.now)
    last_update_time: datetime = Field(default_factory=datetime.now)

    # metadata: dict = {}


class MemoryWriteToolPram(BaseModel):
    level: int = Field(
        default=1, ge=1, le=5, description="记忆等级, 1-5, 1为最不重要, 5为最重要"
    )
    keywords: list[str] = Field(
        ...,
        description="记忆关键词列表, 用于搜索匹配, 如果要绑定到群成员上最好包含群成员ID",
    )
    content: str = Field(..., description="记忆内容")
    # metadata: dict = Field(default_factory=dict, description="记忆元数据")


class MemoryUpdateToolPram(BaseModel):
    id: PyObjectId = Field(..., description="记忆ID")
    level: int = Field(
        default=1, ge=1, le=5, description="记忆等级, 1-5, 1为最不重要, 5为最重要"
    )
    keywords: list[str] = Field(
        ...,
        description="记忆关键词列表, 用于搜索匹配, 如果要绑定到群成员上最好包含群成员ID",
    )
    content: str = Field(..., description="记忆内容")
    # metadata: dict = Field(default_factory=dict, description="记忆元数据")


async def write_memory(memory: Memory):
    db_collection = await get_collection()
    await db_collection.insert_one(memory.model_dump(by_alias=True))


async def update_memory(memory_id: str, memory: Memory):
    db_collection = await get_collection()
    memory.last_update_time = datetime.now()
    await db_collection.update_one(
        {"_id": ObjectId(memory_id)}, {"$set": memory.model_dump(by_alias=True)}
    )


async def search_memory(content: str, limit: int = 5):
    db_collection = await get_collection()
    all_keywords = await db_collection.distinct("keywords")
    match_keywords = []
    for keyword in all_keywords:
        if keyword in content:
            log.debug(f"搜索到记忆关键词: {keyword}")
            match_keywords.append(keyword)
    if not match_keywords:
        log.debug(f"未搜索到记忆关键词, content: {content}")
        return []

    db_results = await db_collection.find(
        {"keywords": {"$in": match_keywords}}
    ).to_list(length=limit)
    results = [Memory.model_validate(memory) for memory in db_results]
    for result in results:
        result.latest_read_time = datetime.now()
        await update_memory(str(result.id), result)
    log.debug(f"搜索记忆结果: {results}")
    return results
