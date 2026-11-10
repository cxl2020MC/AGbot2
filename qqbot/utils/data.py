import json
import anyio

type Path = anyio.Path

DataDir = anyio.Path("data/")


def get_file_path(file_name):
    return DataDir / file_name


# TODO: 
async def create_data_dir():
    if not await DataDir.exists():
        print(f"创建数据目录: {DataDir}")
        await DataDir.mkdir(parents=True, exist_ok=True)


async def read_json_file(file_path: Path):
    if not file_path.exists():
        return None
    async with await anyio.open_file(file_path, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)




async def write_json_file(file_path: Path, data: dict):
    async with await anyio.open_file(file_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data))


async def read_jsonl_file(file_path: Path):

    async with await anyio.open_file(file_path, "r", encoding="utf-8") as f:
        i = 0
        async for line in f:
            line = line.strip()
            if line:
                yield (i, json.loads(line))
            i += 1


async def write_jsonl_file(file_path: Path, data: dict | str):
    async with await anyio.open_file(file_path, "a", encoding="utf-8") as f:
        data_str = data if isinstance(data, str) else json.dumps(data)
        await f.write(data_str + "\n")
