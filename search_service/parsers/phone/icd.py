from datetime import datetime

from playwright.sync_api import Playwright, expect, sync_playwright

from search_service.parsers.base import (
    BaseParser,
    Item,
    base_context,
    delete_file,
    write_to_csv,
)

SOURCE = "icd.com.ua"
FILE_NAME = f"icd_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class IcdParser(BaseParser):
    def parse(self):
        with sync_playwright() as playwright:
            run(playwright, self.query, self.filename)


def run(playwright: Playwright, query: str, filename: str) -> None:
    delete_file(filename)
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    separated_query = query.split()
    page_number = 1
    base_url = "https://icd.com.ua"
    url = f"{base_url}/katalog/search/filter/page={page_number}/?q={query}"
    page.goto(url)
    page.wait_for_selector("div.catalog__content")
    empty = page.locator("div[data-catalog-view-block='products'] p")

    if empty.count() == 1:
        return

    selector = "tr.productsTable-row"
    items_ = []

    while True:
        items = page.locator(selector)
        count = page.locator(selector).count()
        for i in range(count):
            item = items.nth(i)
            name = (
                item.locator("td.productsTable-cell.__title a")
                .text_content()
                .strip()
                .replace(",", "")
            )

            if not any(word.lower() in name.lower() for word in separated_query):
                continue

            item_url = (
                base_url
                + item.locator("td.productsTable-cell.__title a")
                .get_attribute("href")
                .strip()
            )
            status = (
                item.locator("td.productsTable-cell.__status ").text_content().strip()
            )

            if status == "Немає в наявності":
                continue

            price = float(
                item.locator("td.productsTable-cell.__price")
                .first.text_content()
                .strip()
                .replace("грн", "")
                .replace(" ", "")
                .replace("\xa0", "")
            )

            item_data = Item(
                src=SOURCE,
                category="All",
                name=name,
                price=price,
                url=item_url,
                status=status,
            )
            items_.append(item_data)
        next_page = page.locator(
            "div.pagination-container span.pager__item--forth.is-disabled"
        )

        if next_page.count() == 1 or page_number > 3:
            break

        page_number += 1
        url = url = f"{base_url}/katalog/search/filter/page={page_number}/?q={query}"
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
    query = "XS"
    main(query)
