from playwright.async_api import async_playwright, Playwright
from . import config
from .log import logger as log

async def main():
    async with async_playwright() as p:
        log.info("连接浏览器")
        chromium = p.chromium
        broswer = await chromium.connect(config.playwright_chromium_endpoint)
