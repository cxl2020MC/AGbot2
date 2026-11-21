import asyncio
import os
from datetime import datetime
from enum import StrEnum

import openai

# from typing import Annotated
from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic_mongo import ObjectIdField
from pymongo.operations import SearchIndexModel

from qqbot.log import logger as log
from qqbot.utils import db

client = openai.AsyncOpenAI(
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"), api_key="ollama"
)
db_collection: db.AsyncCollection | None = None


vector_search_index = SearchIndexModel(
    name="vector_search_index",
    type="vectorSearch",
    definition={
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": 768,
                "similarity": "cosine",
                "quantization": "scalar",
            },
            {"type": "filter", "path": "_id"},
        ]
    },
)


async def init():
    global db_collection
    db_collection = (await db.get_db()).get_collection("ai_memory")
    log.info("初始化记忆数据库")
    # await db_collection.create_index({"keywords": 1})
    await db_collection.create_search_index(vector_search_index)
    log.info("记忆数据库初始化完成")
    asyncio.create_task(memory_cleanup_task(), name="ai_memory_cleanup_task")


async def get_collection() -> db.AsyncCollection:
    if db_collection is None:
        await init()
    assert db_collection is not None
    return db_collection


async def get_embedding(text: str) -> list[float]:
    response = await client.embeddings.create(
        model="embeddinggemma-2:270m",
        input=text,
    )
    embedding = response.data[0].embedding
    log.debug(f"获取文本 {text} 向量成功, embedding 维度: {len(embedding)}")
    return embedding


async def search_memory(
    content: str,
    limit: int = 5,
    group_open_id: str | None = None,
    user_open_id: str | None = None,
    *,
    filter_score: float = 0.7,
    filter_object_ids: list[str] | None = None,
):
    db_collection = await get_collection()
    embedding = await get_embedding(content)
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_search_index",
                "queryVector": embedding,
                "path": "embedding",
                "numCandidates": limit * 20,
                "limit": limit,
                "filter": {},
            },
        },
        {
            "$addFields": {
                "score": {"$meta": "vectorSearchScore"},
            },
        },
        {
            "$match": {"score": {"$gt": filter_score}},
        },
        {
            "$project": {"embedding": 0},
        },
    ]
    if group_open_id:
        log.debug(f"搜索记忆时的群ID: {group_open_id}")
        pipeline[0]["$vectorSearch"]["filter"].update(
            {
                "group_open_id": {
                    "$or": [
                        {"$eq": ["$group_open_id", group_open_id]},
                        {"$eq": ["$group_open_id", None]},
                    ]
                }
            }
        )
    if user_open_id:
        log.debug(f"搜索记忆时的用户ID: {user_open_id}")
        pipeline[0]["$vectorSearch"]["filter"].update(
            {
                "user_open_id": {
                    "$or": [
                        {"$eq": ["$user_open_id", user_open_id]},
                        {"$eq": ["$user_open_id", None]},
                    ]
                }
            }
        )
    if filter_object_ids:
        log.debug(f"搜索记忆时过滤的ObjectId: {filter_object_ids}")
        pipeline[0]["$vectorSearch"]["filter"].update(
            {"_id": {"$nin": filter_object_ids}}
        )
    db_results = await (await db_collection.aggregate(pipeline)).to_list()
    log.debug(f"搜索记忆原始结果: {db_results}")
    results = [Memory.model_validate(memory) for memory in db_results]
    log.debug(f"搜索记忆结果: {results}")
    return results


class MemoryType(StrEnum):
    GROUP = "group"
    USER = "user"


class Memory(BaseModel):
    id: ObjectIdField = Field(
        alias="_id", default_factory=ObjectIdField, description="记忆ID"
    )
    level: int = Field(
        default=1, ge=1, le=5, description="记忆等级, 1-5, 1为最不重要, 5为最重要"
    )
    keywords: list[str]
    content: str
    ttl: int = Field(
        default=24 * 3,
        ge=0,
        le=24 * 30,
        description="记忆有效期（小时），0表示永久有效，其他值表示从上次更新时间开始的有效期",
    )
    memory_type: MemoryType = Field(
        default=MemoryType.GROUP,
        description="记忆类型, group表示群记忆, user表示用户记忆",
    )
    group_open_id: str | None = Field(default=None, description="记忆绑定的群ID")
    user_open_id: str | None = Field(default=None, description="记忆绑定的用户ID")
    create_time: datetime = Field(
        default_factory=datetime.now, description="记忆创建时间"
    )
    last_update_time: datetime = Field(
        default_factory=datetime.now, description="记忆最后更新时间"
    )

    embedding: list[float] | None = Field(
        default=None,
        description="记忆内容的向量表示，用于向量搜索",
    )
    # metadata: dict = {}


async def write_memory(memory: Memory):
    if memory.embedding is None:
        embedding = await get_embedding(memory.content)
        memory.embedding = embedding
    memory_dict = memory.model_dump(by_alias=True)
    db_collection = await get_collection()
    await db_collection.insert_one(memory_dict)


async def update_memory(
    memory_id: str,
    memory: Memory,
    *,
    update_time: bool = True,
    update_embedding: bool = True,
):
    db_collection = await get_collection()
    model_exclude = {"id", "embedding"}
    if memory.embedding is None and update_embedding:
        embedding = await get_embedding(memory.content)
        memory.embedding = embedding
        model_exclude.remove("embedding")

    if update_time:
        memory.last_update_time = datetime.now()
    return await db_collection.update_one(
        {"_id": ObjectId(memory_id)},
        {"$set": memory.model_dump(by_alias=True, exclude=model_exclude)},
    )


async def search_memory_by_keywords(
    match_keywords: list[str],
    limit: int = 10,
    *,
    filter_object_ids: list[str] | None = None,
):
    db_collection = await get_collection()
    db_results = await (
        await db_collection.aggregate(
            [
                {
                    "$match": {
                        "keywords": {"$in": match_keywords},
                        "_id": {"$nin": filter_object_ids or []},
                    }
                },
                # {"$sort": {"level": -1, "latest_read_time": 1}},
                # {"$limit": limit},
                {"$sample": {"size": limit}},  # 随机抽取 limit 条记录
            ]
        )
    ).to_list()
    results = [Memory.model_validate(memory) for memory in db_results]
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
    ttl: int = Field(
        default=24 * 3,
        ge=0,
        le=24 * 30,
        description="记忆有效期（小时），0表示永久有效，其他值表示从上次更新时间开始的有效期",
    )
    memory_type: MemoryType = Field(
        default=MemoryType.GROUP,
        description="记忆类型, group表示群记忆, user表示用户记忆",
    )
    group_open_id: str | None = Field(default=None, description="记忆绑定的群ID")
    user_open_id: str | None = Field(
        default=None, description="记忆绑定的用户ID, 没有则表示不绑定到任何用户"
    )
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
    ttl: int = Field(
        default=24 * 3,
        ge=0,
        le=24 * 30,
        description="记忆有效期（小时），0表示永久有效，其他值表示从上次更新时间开始的有效期",
    )
    memory_type: MemoryType = Field(
        default=MemoryType.GROUP,
        description="记忆类型, group表示群记忆, user表示用户记忆",
    )
    group_open_id: str | None = Field(default=None, description="记忆绑定的群ID")
    user_open_id: str | None = Field(
        default=None, description="记忆绑定的用户ID, 没有则表示不绑定到任何用户"
    )
    # metadata: dict = Field(default_factory=dict, description="记忆元数据")


class MemorySearchToolPram(BaseModel):
    content: str = Field(..., description="搜索内容")
    limit: int = Field(
        default=5, ge=1, le=20, description="搜索结果数量, 范围1～20, 默认为5"
    )


class MemoryDeleteToolPram(BaseModel):
    id: ObjectIdField = Field(..., description="需要删除的记忆ID")


async def write_memory_tool_call(tool_param: MemoryWriteToolPram):
    memory = Memory(
        level=tool_param.level,
        keywords=tool_param.keywords,
        content=tool_param.content,
        ttl=tool_param.ttl,
        memory_type=tool_param.memory_type,
        group_open_id=tool_param.group_open_id,
        user_open_id=tool_param.user_open_id,
    )
    await write_memory(memory)
    return f"记忆写入成功, 记忆ID: {memory.id}"


async def update_memory_tool_call(tool_param: MemoryUpdateToolPram):
    memory = Memory(
        _id=tool_param.id,
        level=tool_param.level,
        keywords=tool_param.keywords,
        content=tool_param.content,
        ttl=tool_param.ttl,
        memory_type=tool_param.memory_type,
        group_open_id=tool_param.group_open_id,
        user_open_id=tool_param.user_open_id,
    )
    await update_memory(str(memory.id), memory)
    return f"记忆更新成功, 记忆ID: {memory.id}"


async def search_memory_tool_call(tool_param: MemorySearchToolPram):
    results = await search_memory(
        content=tool_param.content,
        limit=tool_param.limit,
    )
    return str([memory.model_dump() for memory in results])


async def delete_memory_tool_call(tool_param: MemoryDeleteToolPram):
    await delete_memory(str(tool_param.id))
    return "记忆删除成功"


async def memory_cleanup_task():
    log.info("启动记忆清理任务...")
    db_collection = await get_collection()
    while True:
        now = datetime.now()
        expired_memories = await db_collection.find(
            {
                "ttl": {"$gt": 0},
                "$expr": {
                    "$lt": [
                        {
                            "$add": [
                                "$last_update_time",
                                {"$multiply": ["$ttl", 3600, 1000]},
                            ]
                        },
                        now,
                    ]
                },
            }
        ).to_list(length=100)
        if expired_memories:
            log.info(f"清理过期记忆: {len(expired_memories)} 条")
            for memory in expired_memories:
                await delete_memory(str(memory["_id"]))
        await asyncio.sleep(3600)  # 每小时检查一次


async def memory_embedding_update():
    log.info("启动记忆向量更新任务...")
    db_collection = await get_collection()
    memories_without_embedding = await db_collection.find({"embedding": None}).to_list(
        length=100
    )
    if memories_without_embedding:
        log.info(f"更新记忆向量: {len(memories_without_embedding)} 条")
        for memory in memories_without_embedding:
            memory_obj = Memory.model_validate(memory)
            await update_memory(str(memory_obj.id), memory_obj, update_embedding=True)


if __name__ == "__main__":
    # asyncio.run(memory_cleanup_task())
    # async def update_memory_test():
    #     db_collection = await get_collection()
    #     await db_collection.update_many(
    #         {"status": {"$exists": False}}, {"$set": {"ttl": 24 * 3}}
    #     )
    # asyncio.run(update_memory_test())
    async def test():
        await memory_embedding_update()
        await search_memory(
            "米葱苓sama🅥⁧~喵⁧‭[3D8574CD681F77EE1448095A26ED5F9A]: 去哪开gemini", limit=10
        )

    asyncio.run(test())
