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

SOURCE = "all-spares.ua"
FILE_NAME = f"all_spares_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class AllSparesParser(BaseParser):
    def parse(self):
        with sync_playwright() as playwright:
            run(playwright, self.query, self.filename)


def ascii(text: str) -> str:
    return re.sub(r"[^\x00-\x7F]+", "", text)


def run(playwright: Playwright, query: str, filename: str) -> None:
    if check_parser_file(filename):
        return filename
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    query = re.sub(r"\s+", "+", query)
    base_url = "https://all-spares.ua"
    url = f"{base_url}/uk/search/?ipp=192&searchword={query}"
    page.goto(url)
    items = page.locator("article")
    count = page.locator("article").count()
    query_check_list = query.split("+")
    items_ = []
    for i in range(count):
        item = items.nth(i)
        name = (
            item.locator(".component_product_list_info_right h3 a")
            .text_content()
            .strip()
            .replace(",", "")
        )

        if not any(word.lower() in name.lower() for word in query_check_list):
            continue

        price = item.locator(".product-price .-current")

        if price.count():
            price = ascii(price.text_content().strip())
        else:
            price = "Ціна не вказана"

        url = base_url + item.locator(
            ".component_product_list_info_right h3 a"
        ).get_attribute("href")
        status = item.locator(".relative")

        if status.count():
            status = "Немає в наявності"
            continue
        else:
            status = "В наявності"

        item_data = Item(
            src=SOURCE,
            category="All",
            name=name,
            price=float(price),
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
    query = "блок живлення"
    main(query)
