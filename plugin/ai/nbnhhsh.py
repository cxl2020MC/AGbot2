lazy import json

from pydantic import BaseModel, Field

from qqbot import http_client


async def get_nbnhhsh(word: str):
    url = "https://lab.magiconch.com/api/nbnhhsh/guess"
    response = await http_client.post(url, json={"text": word})
    data = response.json()
    return data



async def get_nbnhhsh_tool_call(args: NbnhhshToolParam):
    return json.dumps(await get_nbnhhsh(args.word), ensure_ascii=False)


class NbnhhshToolParam(BaseModel):
    word: str = Field(
        ..., description="要查询的拼音首字母缩写,可以使用 `,` 分隔多个缩写"
    )


if __name__ == "__main__":
    import asyncio
    args = NbnhhshToolParam(word="hyw")
    result = asyncio.run(get_nbnhhsh_tool_call(args))
    print(result)
