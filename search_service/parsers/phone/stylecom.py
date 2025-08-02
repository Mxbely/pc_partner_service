import re
from datetime import datetime

from playwright.sync_api import Playwright, expect, sync_playwright

from search_service.parsers.base import (
    BaseParser,
    Item,
    base_context,
    delete_file,
    write_to_csv,
)

SOURCE = "stylecom.ua"
FILE_NAME = f"stylecom_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class StylecomParser(BaseParser):
    def parse(self):
        with sync_playwright() as playwright:
            run(playwright, self.query, self.filename)


def ascii(text: str) -> str:
    return re.sub(r"[^\x00-\x7F]+", "", text)


def run(playwright: Playwright, query: str, filename: str) -> None:
    delete_file(filename)
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    query = re.sub(r"\s+", "+", query)
    separated_query = query.split("+")
    base_url = "https://stylecom.ua/index.php"
    url = f"{base_url}?route=elasticsearch/elasticsearch/autocomplete&_route_=ua&search={query}"
    page.goto(url)
    items = page.locator(".product-tile--search-autocompleate")
    count = page.locator(".product-tile--search-autocompleate").count()
    items_ = []
    for i in range(count):
        item = items.nth(i)
        name = item.locator("a").first.get_attribute("title").strip().replace(",", "")
        if not any(word.lower() in name.lower() for word in separated_query):
            continue
        price = item.locator("div.product-tile__price span").first.text_content()
        price = price.replace("грн", "").replace(" ", "").strip()
        if not price:
            continue
        price = float(price)
        
        url = item.locator("a").first.get_attribute("href").strip()
        status = (
            item.locator(".product-tile__info .product-tile__stock")
            .text_content()
            .strip()
        )
        if status == "Скоро з'явиться":
            continue

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
    query = "батарея iphone x"
    main(query)
