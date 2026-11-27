import base64
import mimetypes
from typing import TYPE_CHECKING

lazy import anyio
lazy import filetype

if TYPE_CHECKING:
    from os import PathLike


async def get_data_url_by_file(path: PathLike[str]):
    mime_type, _ = await get_filename_minetype(path)
    if mime_type is None:
        raise ValueError(f"无法猜测文件的MIME类型: {path}")

    async with await anyio.open_file(path, "rb") as f:
        data = await f.read()
        return await get_data_url_by_bytes(data, mime_type)


async def get_filename_minetype(path: PathLike[str]):
    mime_type, _ = mimetypes.guess_file_type(path)
    if mime_type is None:
        raise ValueError(f"无法猜测文件的MIME类型: {path}")
    return mime_type


async def get_bytes_minetype(data: bytes):
    kind = filetype.guess(data)
    if kind is None:
        raise ValueError("无法猜测字节数据的MIME类型")
    return kind.mime


async def get_data_url_by_bytes(data: bytes, mime_type: str):
    encoded_data = base64.b64encode(data).decode("utf-8")
    return f"data:{mime_type};base64,{encoded_data}"
