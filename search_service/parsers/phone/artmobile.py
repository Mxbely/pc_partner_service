import re
from datetime import datetime
import time

from playwright.sync_api import Playwright, expect, sync_playwright

from search_service.parsers.base import (
    BaseParser,
    Item,
    base_context,
    delete_file,
    write_to_csv,
)

SOURCE = "artmobile.ua"
FILE_NAME = f"artmobile_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class ArtmobileParser(BaseParser):
    def parse(self):
        with sync_playwright() as playwright:
            run(playwright, self.query, self.filename)


def ascii(text: str) -> str:
    return re.sub(r"[^\x00-\x7F]+", "", text)


def run(playwright: Playwright, query: str, filename: str) -> None:
    delete_file(filename)
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(10000)
    query = re.sub(r"\s+", "+", query)

    base_url = "https://artmobile.ua"
    url = f"{base_url}/search?term={query}&perPage=96&sort=price.desc"
    page.goto(url)
    selector = "div.product-card"
    empty = page.locator("div.empty-text")
    if empty.count():
        return

    items_ = []
    items = page.locator(selector)
    count = page.locator(selector).count()

    for i in range(count):
        item = items.nth(i)
        name = item.locator("div.product-title a").text_content().strip().replace(",", "")
        item_url = item.locator("div.product-title a").get_attribute("href").strip()
        price = float(
            item.locator("div.price").text_content().strip().replace("грн", "").replace("\xa0", "")
        )
        status = (
            item.locator("div.page-stock")
            .text_content()
            .strip()
        )
        if status != "В наявності":
            continue

        item_data = Item(
            src=SOURCE,
            category="all",
            name=name,
            price=price,
            url=item_url,
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
    query = "батарея Samsung EB-BA166ABY"
    main(query)
