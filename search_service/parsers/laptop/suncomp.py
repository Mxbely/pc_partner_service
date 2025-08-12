import re
from datetime import datetime

from playwright.sync_api import Playwright, expect, sync_playwright

from search_service.parsers.base import (
    BaseParser,
    Item,
    base_context,
    check_parser_file,
    write_to_csv,
)

SOURCE = "suncomp.com.ua"
FILE_NAME = f"suncomp_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class SuncompParser(BaseParser):
    def parse(self):
        with sync_playwright() as playwright:
            run(playwright, self.query, self.filename)


def run(playwright: Playwright, query: str, filename: str) -> None:
    if check_parser_file(filename):
        return filename
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    query = re.sub(r"\s+", "+", query)
    separated_query = query.split("+")
    base_url = "https://suncomp.com.ua"
    url = f"{base_url}/search/?search={query}&description=true&sub_category=true&limit=100"
    page.goto(url)
    items = page.locator(".product-item-card")
    count = page.locator(".product-item-card").count()
    items_ = []
    for i in range(count):
        item = items.nth(i)
        name = item.locator(".pr-name").text_content().strip().replace(",", "")

        if not any(word.lower() in name.lower() for word in separated_query):
            continue

        url = item.locator(".pr-name").get_attribute("href").strip()
        price = item.locator(".pr-prices .act span")

        if not price.count():
            price = "Ціна не вказана"
            continue

        price = float(price.text_content().replace(" ", "").strip())
        status = item.locator(".pr-prices span")

        if status.count():
            status = status.last.text_content().strip()
            if status != "в наличии":
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
    query = "батарея lenovo"
    main(query)
