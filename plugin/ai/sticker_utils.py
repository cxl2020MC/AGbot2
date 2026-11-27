import asyncio
import os
from enum import StrEnum

import openai

# from typing import Annotated
from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic_mongo import ObjectIdField
from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel

from qqbot.log import logger as log
from qqbot.utils import db

client = openai.AsyncOpenAI(
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"), api_key="ollama"
)
db_collection: db.AsyncCollection | None = None


search_index_definition = {
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
}

vector_search_index = SearchIndexModel(
    name="vector_search_index",
    type="vectorSearch",
    definition=search_index_definition,
)


async def init():
    global db_collection
    db_collection = (await db.get_db()).get_collection("stickers")
    log.info("初始化表情包数据库")
    # await db_collection.create_index({"keywords": 1})
    try:
        await db_collection.create_search_index(vector_search_index)
    except OperationFailure:
        await db_collection.update_search_index(
            "vector_search_index", search_index_definition
        )
    log.info("表情包数据库初始化完成")


async def get_collection() -> db.AsyncCollection:
    if db_collection is None:
        await init()
    assert db_collection is not None
    return db_collection


