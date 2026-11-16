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
    id: ObjectIdField = Field(
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


async def write_memory(memory: Memory):
    db_collection = await get_collection()
    await db_collection.insert_one(memory.model_dump(by_alias=True))


async def update_memory(memory_id: str, memory: Memory, update_time: bool = True):
    db_collection = await get_collection()
    if update_time:
        memory.last_update_time = datetime.now()
    await db_collection.update_one(
        {"_id": ObjectId(memory_id)},
        {"$set": memory.model_dump(by_alias=True, exclude={"id"})},
    )


async def search_memory(content: str, limit: int = 10):
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

    # db_results = await db_collection.find(
    #     {"keywords": {"$in": match_keywords}}
    # ).to_list(length=limit)
    db_results = await (
        await db_collection.aggregate(
            [
                {"$match": {"keywords": {"$in": match_keywords}}},
                # {"$sort": {"level": -1, "latest_read_time": 1}},
                # {"$limit": limit},
                {"$sample": {"size": limit}},  # 随机抽取 limit 条记录
            ]
        )
    ).to_list()
    results = [Memory.model_validate(memory) for memory in db_results]
    for result in results:
        result.latest_read_time = datetime.now()
        await update_memory(str(result.id), result, update_time=False)
    log.debug(f"搜索记忆结果: {results}")
    return results


async def delete_memory(memory_id: str):
    db_collection = await get_collection()
    await db_collection.delete_one({"_id": ObjectId(memory_id)})


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
    id: ObjectIdField = Field(..., description="需要更新的记忆ID")
    level: int = Field(
        default=1, ge=1, le=5, description="记忆等级, 1-5, 1为最不重要, 5为最重要"
    )
    keywords: list[str] = Field(
        ...,
        description="记忆关键词列表, 用于搜索匹配, 如果要绑定到群成员上最好包含群成员ID",
    )
    content: str = Field(..., description="记忆内容")
    # metadata: dict = Field(default_factory=dict, description="记忆元数据")


class MemorySearchToolPram(BaseModel):
    content: str = Field(..., description="搜索内容")
    limit: int = Field(
        default=10, ge=1, le=20, description="搜索结果数量, 范围1～20, 默认为10"
    )


class MemoryDeleteToolPram(BaseModel):
    id: ObjectIdField = Field(..., description="需要删除的记忆ID")


async def write_memory_tool_call(tool_param: MemoryWriteToolPram):
    memory = Memory(
        level=tool_param.level,
        keywords=tool_param.keywords,
        content=tool_param.content,
    )
    await write_memory(memory)
    return f"记忆写入成功, 记忆ID: {memory.id}"


async def update_memory_tool_call(tool_param: MemoryUpdateToolPram):
    memory = Memory(
        _id=tool_param.id,
        level=tool_param.level,
        keywords=tool_param.keywords,
        content=tool_param.content,
    )
    await update_memory(str(memory.id), memory)
    return f"记忆更新成功, 记忆ID: {memory.id}"


async def search_memory_tool_call(content: str, limit: int = 10):
    results = await search_memory(content, limit)
    return [memory.model_dump() for memory in results]


async def delete_memory_tool_call(memory_id: str):
    await delete_memory(memory_id)
    return f"记忆删除成功, 记忆ID: {memory_id}"
