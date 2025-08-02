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

SOURCE = "radiodetal.com.ua"
FILE_NAME = f"radiodetal_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class RadiodetalParser(BaseParser):
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
    query = re.sub(r"\s+", "+", query)
    separated_query = query.split("+")

    base_url = "https://radiodetal.com.ua/"
    url = f"{base_url}index.php?route=product/search&search={query}&description=true&sort=p.price&order=DESC&limit=96"
    page.goto(url)
    selector = "div.product-thumb.uni-item"
    empty = page.locator("div.div-text-empty")
    if empty.count() == 1:
        return

    items_ = []
    items = page.locator(selector)
    count = page.locator(selector).count()

    for i in range(count):
        item = items.nth(i)
        name = item.locator("a.product-thumb__name").text_content().strip().replace(",", "")
        item_url = base_url + item.locator("a.product-thumb__name").get_attribute("href").strip()
        price = float(item.locator("div.product-thumb__price.price").get_attribute("data-price"))
        status = (
            item.locator("div.qty-indicator div.qty-indicator__text")
            .text_content()
            .strip()
        )
        if status == "Нет в наличии" or status == "Немає в наявності":
            continue
        item_data = Item(
            src=SOURCE,
            category="All",
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
    query = "asus"
    main(query)
