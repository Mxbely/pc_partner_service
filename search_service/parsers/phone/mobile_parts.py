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

SOURCE = "mobile-parts.com.ua"
FILE_NAME = f"mobile_parts_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class MobilePartsParser(BaseParser):
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
    page_number = 1
    base_url = "https://mobile-parts.com.ua"
    url = f"{base_url}/search/?search={query}&limit=100&page={page_number}"
    page.goto(url, wait_until="networkidle")
    selector = "div.product-item-container"
    empty = page.locator("div.products-category")

    if empty.count() == 0:
        return

    paginator_text = (
        page.locator("div.product-filter-bottom div.form-group").text_content().strip()
    )
    pages = int(paginator_text.split(" ")[-2])
    items_ = []
    while True:
        items = page.locator(selector)
        count = page.locator(selector).count()

        for i in range(count):
            item = items.nth(i)
            name = item.locator("h4 a").text_content().strip().replace(",", "")

            if not all(word.lower() in name.lower() for word in separated_query):
                continue

            item_url = item.locator("h4 a").get_attribute("href").strip()
            price = float(
                item.locator("div.price span")
                .first.text_content()
                .replace("\xa0", "")
                .replace(" ", "")
                .replace("грн", "")
                .strip()
            )
            status = item.locator("div.stock-status")
            status_text = ""

            if status.count() == 1:
                status_text = status.text_content().strip()
                if status_text == "Предзаказ" or status_text == "Нет в наличии":
                    continue

            status_text = status_text or "В наличии"
            item_data = Item(
                src=SOURCE,
                category="All",
                name=name,
                price=price,
                url=item_url,
                status=status_text,
            )
            items_.append(item_data)
        page_number += 1

        if page_number > 3 or page_number > pages:
            break

        url = f"{base_url}/search/?search={query}&limit=100&page={page_number}"
        page.goto(url, wait_until="networkidle")
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
    query = "1234567890"
    main(query)
