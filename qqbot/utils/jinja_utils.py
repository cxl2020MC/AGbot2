from anyio import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import data_url_utils

template_path = Path("plugin/web_static/templates")
static_path = Path("plugin/web_static/static")

env = Environment(
    loader=FileSystemLoader(template_path),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
    enable_async=True,
)


async def get_data_url(file_path):
    return await data_url_utils.get_data_url_by_file(static_path / file_path)


env.globals.update(
    {
        "get_data_url": data_url_utils.get_data_url_by_file,
        "template_path": template_path,
        "static_path": static_path,
    }
)
