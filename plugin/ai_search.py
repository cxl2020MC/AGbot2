from qqbot import http_client
lazy import os


async def get_deepseek_api_key():
    api_key = os.environ.get("DEEPSEEK_API_KEY", None)
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 环境变量未设置.")
    return api_key


async def web_search(query: str, count: int = 10, need_content: bool = False):
    api_key = await get_deepseek_api_key()

    url = "https://api.deepseek.ai/v1/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "count": count,
        "need_content": need_content,
    }

    response = await http_client.post(url, json=payload, headers=headers)
    # response.raise_for_status()
    return response.json()

async def web_fetch(url: str):
    api_key = await get_deepseek_api_key()

    fetch_url = "https://api.deepseek.ai/v1/fetch"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
    }
    response = await http_client.post(fetch_url, json=payload, headers=headers)
    # response.raise_for_status()
    return response.json()