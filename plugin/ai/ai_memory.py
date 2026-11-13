import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from qqbot.utils import data
from qqbot.log import logger as log

memory_file_path = data.get_file_path("ai_memory.jsonl")


class Memory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid7()))
    keywords: list[str]
    content: str
    time: datetime = Field(default_factory=datetime.now)

    metadata: dict = {}


class MemoryWriteToolPram(BaseModel):
    keywords: list[str] = Field(
        ...,
        description="记忆关键词列表, 用于搜索匹配, 如果要绑定到群成员上最好包含群成员ID",
    )
    content: str = Field(..., description="记忆内容")
    # metadata: dict = Field(default_factory=dict, description="记忆元数据")


async def read_memory():
    async for i, memory in data.read_jsonl_file(memory_file_path):
        yield i, Memory.model_validate(memory)


async def write_memory(memory: Memory):
    await data.write_jsonl_file(memory_file_path, memory.model_dump_json())


async def search_memory(content: str, limit: int = 5):
    results: list[Memory] = []
    async for i, memory in read_memory():
        for keyword in memory.keywords:
            if keyword in content:
                log.debug(f"在第 {i} 行找到记忆: {memory}")
                results.append(memory)
                break
    log.debug(f"搜索记忆结果: {results}")
    return results
