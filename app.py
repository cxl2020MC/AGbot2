import aiohttp
import asyncio

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('ws://localhost:3001/') as ws:
            async for msg in ws:
                print(msg.json())
                # if msg.type == aiohttp.WSMsgType.TEXT:
                    # print(msg.json())
                # elif msg.type == aiohttp.WSMsgType.ERROR:
                    # break

asyncio.run(main())