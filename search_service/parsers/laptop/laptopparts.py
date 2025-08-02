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

SOURCE = "laptopparts.com.ua"
FILE_NAME = f"laptopparts_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class LaptoppartsParser(BaseParser):
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

    base_url = "https://laptopparts.com.ua"
    url = f"{base_url}/ua/site_search?search_term={query}&product_items_per_page=48"
    page.goto(url)
    selector = "li.b-product-gallery__item"
    empty = page.locator("span.b-search-result-info__counter").text_content().strip()
    counter = int(empty.split(" ")[0])
    if counter == 0:
        return

    items_ = []
    items = page.locator(selector)
    count = page.locator(selector).count()

    for i in range(count):
        item = items.nth(i)
        name = item.locator("div.b-product-gallery__header a.b-product-gallery__title").text_content().strip().replace(",", "")
        if not any(word.lower() in name.lower() for word in separated_query):
            continue
        item_url = base_url + item.locator("div.b-product-gallery__header a.b-product-gallery__title").get_attribute("href").strip()
        price = float(
            item.locator("div.b-product-gallery__prices span.b-product-gallery__current-price").text_content().replace("/комплект", "").replace(",", ".").replace("₴", "").replace(" ", "").strip()
        )
        status = (
            item.locator("div.b-product-gallery__data span.b-product-gallery__state")
            .text_content()
            .strip()
        )
        if status == "Немає в наявності":
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
    query = "HDD"
    main(query)
