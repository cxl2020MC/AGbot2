from plugin import echo
from qqbot import qq_bot


async def main():
    qq = qq_bot.QQ_Bot()
    qq.plugin_manager.add_plugin(echo.plugin)
    await qq.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
