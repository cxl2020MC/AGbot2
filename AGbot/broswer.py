from playwright.async_api import async_playwright   # , Playwright
import base64
from . import config
from .log import logger as log


async def remote_main(func):
    async with async_playwright() as p:
        log.info("连接浏览器")
        chromium = p.firefox  # chromium
        broswer = await chromium.connect(config.playwright_chromium_endpoint)
        log.info("连接浏览器成功")
        page = await broswer.new_page()
        ret_data = await func(page)
        await page.close()
        return ret_data


async def main(func):
    async with async_playwright() as p:
        log.info("启动浏览器")
        browser = await p.chromium.launch()
        log.info("启动浏览器成功")
        log.info("设置浏览器窗口大小")
        browser = await browser.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=1.5)
        log.info("设置浏览器窗口大小成功")
        page = await browser.new_page()
        ret_data = await func(page)
        log.info("关闭浏览器")
        await browser.close()
        return ret_data


async def 屏幕截图(url, full_page=True):
    async def func(page):
        log.info(f"开始截图: {url}")
        await page.goto(url)
        # log.debug("设置页面大小")
        # await page.set_viewport_size({"width": 1920, "height": 1080})
        log.debug("等待页面加载完成")
        await page.wait_for_load_state("networkidle")
        log.debug("页面加载完成")
        log.info("开始截图")
        screenshot_bytes = await page.screenshot(full_page=full_page, type="png")
        log.info("截图完成")
        img_base64 = base64.b64encode(screenshot_bytes).decode()
        return img_base64
    return await main(func)
