from playwright.async_api import async_playwright
import base64

class AsyncBrowser:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def load_page(self, url: str) -> str:
        if not self.page:
            await self.start()
        await self.page.goto(url)
        await self.page.wait_for_load_state("networkidle")
        return await self.page.content()

    async def get_text_content(self) -> str:
        if not self.page:
            return ""
        return await self.page.evaluate("document.body.innerText")

    async def extract_links(self) -> list:
        if not self.page:
            return []
        return await self.page.evaluate("""
            Array.from(document.querySelectorAll('a')).map(a => a.href)
        """)

    async def screenshot_base64(self) -> str:
        if not self.page:
            return ""
        screenshot_bytes = await self.page.screenshot(full_page=True)
        return base64.b64encode(screenshot_bytes).decode("utf-8")
