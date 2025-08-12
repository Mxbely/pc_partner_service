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

SOURCE = "4laptop.kiev.ua"
FILE_NAME = f"4laptop_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class ForLaptopKievParser(BaseParser):
    def parse(self):
        with sync_playwright() as playwright:
            run(playwright, self.query, self.filename)


def run(playwright: Playwright, query: str, filename: str) -> None:
    if check_parser_file(filename):
        return filename
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(**base_context)
    query = re.sub(r"\s+", "+", query)
    separated_query = query.split("+")
    page = context.new_page()
    base_url = "https://4laptop.kiev.ua"
    url = f"{base_url}/index.php?route=product/search&search={query}&limit=500"
    page.goto(url)
    selector = ".category-page .product-layout"
    items = page.locator(selector)

    if items.count() == 0:
        return

    items_ = []
    for i in range(items.count()):
        name = items.nth(i).locator(".product-name a").inner_text()
        name = name.replace(",", "")

        if not any(word.lower() in name.lower() for word in separated_query):
            continue

        link = items.nth(i).locator(".product-name a").get_attribute("href")
        price = float(
            items.nth(i)
            .locator(".price .price_no_format")
            .inner_text()
            .replace("грн.", "")
            .replace(" ", "")
        )
        status = items.nth(i).locator(".stock-status").inner_text()

        if status == "Нет в наличии":
            continue

        items_.append(
            Item(
                src=SOURCE,
                category="All",
                name=name,
                price=price,
                url=link,
                status=status,
            )
        )
    items_ = sorted(items_, key=lambda x: x.price, reverse=True)
    write_to_csv(items_, filename)

    # ---------------------
    context.close()
    browser.close()


def main(query: str):
    with sync_playwright() as playwright:
        run(playwright, query)


if __name__ == "__main__":
    query = "блок живлення"
    main(query)
