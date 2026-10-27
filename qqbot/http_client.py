import httpx2
import yarl
from httpx2.websockets._api import AsyncWebSocketSession

client = httpx2.AsyncClient(http2=True)

type WebSocketSession = AsyncWebSocketSession


async def get(
    url: str | yarl.URL,
    params: dict | None = None,
    headers: dict | None = None,
):
    if isinstance(url, yarl.URL):
        url = str(url)
    return await client.get(url, params=params, headers=headers)


async def post(
    url: str | yarl.URL,
    json: dict | None = None,
    headers: dict | None = None,
):
    if isinstance(url, yarl.URL):
        url = str(url)
    return await client.post(url, json=json, headers=headers)
