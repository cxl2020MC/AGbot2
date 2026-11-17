from playwright.async_api import Browser, async_playwright

browser: Browser | None = None


async def get_browser() -> Browser:
    global browser
    if browser is None:
        p = async_playwright()
        p = await p.start()
        browser = await p.chromium.connect("ws://127.0.0.1:3000/")

    return browser


async def close_browser():
    if browser:
        await browser.close()


async def screenshot(url: str, full_page: bool = True):
    browser = await get_browser()
    page = await browser.new_page()
    await page.goto(url)
    await page.wait_for_load_state("networkidle")
    screenshot_bytes = await page.screenshot(full_page=full_page)
    await page.close()
    return screenshot_bytes
