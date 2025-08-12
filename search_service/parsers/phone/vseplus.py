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

SOURCE = "vseplus.com"
FILE_NAME = f"vseplus_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class VseplusParser(BaseParser):
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
    base_url = "https://vseplus.com"
    url = f"{base_url}/search/p-{page_number}?s=-price&q={query}"
    page.goto(url)
    selector = "div.card-product.list-cards-product__item div.card-product__content"
    empty = page.locator("div.empty")

    if empty.count():
        return

    paginator_text = page.locator("div.paginator__summary").text_content().strip()
    pages = int(paginator_text.split(" ")[-1])
    items_ = []

    while True:
        items = page.locator(selector)
        count = page.locator(selector).count()

        for i in range(count):
            item = items.nth(i)
            name = (
                item.locator("div.card-product__info a.card-product__link")
                .text_content()
                .strip()
                .replace(",", "")
            )

            if not any(word.lower() in name.lower() for word in separated_query):
                continue

            item_url = (
                base_url
                + item.locator("div.card-product__info a.card-product__link")
                .get_attribute("href")
                .strip()
            )
            price = float(
                item.locator("p.product-price__current strong")
                .text_content()
                .replace("\xa0", "")
                .strip()
            )
            status = item.locator("p.product-availability").text_content().strip()

            if status != "В наличии":
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
        page_number += 1

        if page_number > 5 or page_number > pages:
            break

        url = f"{base_url}/search/p-{page_number}?s=-price&q={query}"
        page.goto(url)
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
