from websockets.asyncio.client import connect
import asyncio

async def main(uri):
    async with connect(uri) as websocket:
        pass