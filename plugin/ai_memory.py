import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from qqbot.utils import data

memory_file_path = data.get_file_path("ai_memory.jsonl")


class Memory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid7()))
    keywords: list[str]
    content: str
    time: datetime = Field(default_factory=datetime.now)

    metadata: dict = {}


async def read_memory():
    async for i, memory in data.read_jsonl_file(memory_file_path):
        yield i, Memory.model_validate(memory)


async def write_memory(memory: Memory):
    await data.write_jsonl_file(memory_file_path, memory.model_dump_json())


async def search_memory(content: str, limit: int = 5):
    results: list[Memory] = []
    async for i, memory in read_memory():
        if memory.content in content:
            print(f"找到记忆:{i} {memory}")
            results.append(memory)
    return results
