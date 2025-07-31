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

SOURCE = "smartparts.in.ua"
FILE_NAME = f"smartparts_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class SmartpartsParser(BaseParser):
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
    base_url = "https://smartparts.in.ua/"
    url = f"{base_url}/ua/site_search?search_term={query}"
    page.goto(url)
    items_ = []
    while True:
        page.wait_for_selector(".cs-product-gallery__item")
        items = page.locator(".cs-product-gallery__item")
        count = page.locator(".cs-product-gallery__item").count()
        # print(f"Count: {count}")
        for i in range(count):
            item = items.nth(i)
            status = item.locator("span.cs-goods-data__state").text_content().strip()
            if status == "Немає в наявності":
                continue
            name = item.locator("div.cs-product-gallery__title a.cs-goods-title").text_content().strip().replace(",", "")
            if not any(word.lower() in name.lower() for word in separated_query):
                # print(f"Words not found in {name}")
                continue
            url = base_url + item.locator("div.cs-product-gallery__title a.cs-goods-title").get_attribute("href").strip()
            price = ascii(item.locator("div.cs-goods-price span.cs-goods-price__value_type_current").text_content().strip())

            item_data = Item(
                src=SOURCE,
                category="ALL",
                name=name,
                price=float(price),
                url=url,
                status=status,
            )
            items_.append(item_data)
        next_button = page.locator("div.b-pager a.b-pager__link_pos_last")
        if next_button.count():
            url = base_url + next_button.get_attribute("href")
            if "page_6" in url:
                break
            next_button.click()
            # page.goto(url)
        else:
            break
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
