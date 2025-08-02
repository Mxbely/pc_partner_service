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

SOURCE = "4nb.com.ua"
FILE_NAME = f"4nb_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class ForNBParser(BaseParser):
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
    base_url = "https://www.4nb.com.ua"
    url = f"{base_url}/search?search_query={query}"
    page.goto(url)
    items = page.locator("ul.product_list li.ajax_block_product")
    count = page.locator("ul.product_list li.ajax_block_product").count()
    items_ = []
    for i in range(count):
        item = items.nth(i)
        name_element = item.locator(".right-block h5").locator("a").nth(0)
        name = name_element.text_content().strip().replace(",", "")
        name = name.replace(",", "")
        if not any(word.lower() in name.lower() for word in separated_query):
            continue
        price = item.locator(".content_price span")
        if price.count():
            price = float(ascii(price.text_content().strip().replace(",", ".").replace(" ", "")))
        else:
            price = "Ціна не вказана"
            continue
        url = name_element.get_attribute("href")
        status = item.locator(".availability")
        if status.count():
            status = status.text_content().strip()
            if status == "Нет в наличии":
                continue
        else:
            status = "Невідомо"

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
    query = "екран acer"
    main(query)
