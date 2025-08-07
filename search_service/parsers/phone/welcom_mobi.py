import re
from datetime import datetime, timedelta

from playwright.sync_api import Playwright, expect, sync_playwright

from search_service.parsers.base import (
    BaseParser,
    Item,
    base_context,
    delete_file,
    write_to_csv,
)

SOURCE = "welcome-mobi.com.ua"
FILE_NAME = f"welcome-mobi_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class WelcomMobiParser(BaseParser):
    def parse(self):
        with sync_playwright() as playwright:
            run(playwright, self.query, self.filename)


def run(playwright: Playwright, query: str, filename: str) -> None:
    delete_file(filename)
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    dtime = datetime.now() + timedelta(hours=20)
    dtime = int(dtime.timestamp())
    cookies = [
        {
            "name": "per_page",
            "value": "96",
            "domain": ".welcome-mobi.com.ua",
            "path": "/",
            "expires": dtime,
            "httpOnly": False,
            "secure": False,
        },
    ]
    page = context.new_page()
    query = re.sub(r"\s+", "+", query)
    separated_query = query.split("+")
    base_url = "https://welcome-mobi.com.ua"
    url = f"{base_url}/shop/search?text={query}"
    page.goto("https://welcome-mobi.com.ua/")
    page.locator("#inputString").click()
    page.locator("#inputString").fill("дисплей iphone X")
    context.add_cookies(cookies)
    page.locator("#inputString").press("Enter")
    page.wait_for_selector(".swiper-slide")
    items = page.locator("li.swiper-slide")
    count = page.locator("li.swiper-slide").count()
    items_ = []
    for i in range(count):
        item = items.nth(i)
        name = item.locator(".title").text_content().strip().replace(",", "")

        if not any(word.lower() in name.lower() for word in separated_query):
            continue

        url = item.locator("a").get_attribute("href").strip()
        status1 = item.locator("div.btn.btn-def button")

        if status1.count():
            continue

        status = "В наявності"
        price1 = item.locator("div.d_i-b span").first.text_content().strip()
        price2 = item.locator("div.d_i-b sup").first.text_content().strip()
        price = float(f"{price1}.{price2}")
        item_data = Item(
            src=SOURCE,
            category="All",
            name=name,
            price=price,
            url=url,
            status=status,
        )
        items_.append(item_data)
    items_ = sorted(items_, key=lambda x: x.price, reverse=True)
    write_to_csv(items_, filename)
    del items_

    # ---------------------
    context.close()
    browser.close()


def main(query: str):
    with sync_playwright() as playwright:
        run(playwright, query, FILE_NAME)


if __name__ == "__main__":
    query = "батарея iphone X"
    main(query)
