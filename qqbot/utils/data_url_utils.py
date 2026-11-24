import base64
import mimetypes
from typing import TYPE_CHECKING

import anyio

if TYPE_CHECKING:
    from os import PathLike


async def get_data_url_by_file(path: PathLike[str]):
    mime_type, _ = mimetypes.guess_file_type(path)
    if mime_type is None:
        raise ValueError(f"无法猜测文件的MIME类型: {path}")

    async with await anyio.open_file(path, "rb") as f:
        data = await f.read()
        encoded_data = base64.b64encode(data).decode("utf-8")
        return f"data:{mime_type};base64,{encoded_data}"
