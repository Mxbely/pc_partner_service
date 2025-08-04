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

SOURCE = "room-parts.com.ua"
FILE_NAME = f"room_parts_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class RoomPartsParser(BaseParser):
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
    separated_query = query.split("+")
    page_number = 1
    base_url = "https://room-parts.com.ua"
    url = f"{base_url}/ua/katalog/search/filter/page={page_number}/?q={query}"
    page.goto(url)
    page.wait_for_timeout(300)
    page.get_by_role("button", name="✅ Так, мені все зрозуміло").click()

    page.wait_for_selector("div.catalog__content")
    empty = page.locator('div[data-catalog-view-block="products"]')
    if empty.count() == 1:
        empty_text = empty.text_content().strip()
        if "Товар очікується найближчим часом" in empty_text:
            return

    selector = "div.catalogCard-main"

    items_ = []
    while True:
        page.wait_for_selector("div.catalog__content")
        items = page.locator(selector)
        count = page.locator(selector).count()

        for i in range(count):
            item = items.nth(i)
            name = item.locator("div.catalogCard-title a").text_content().strip().replace(",", "").replace("\xd7", "x")
            if not any(word.lower() in name.lower() for word in separated_query):
                continue
            # print(f"Name: {name}")
            item_url = base_url + item.locator("div.catalogCard-title a").get_attribute("href").strip()
            price = float(item.locator("div.catalogCard-price").text_content().strip().replace("грн", "").replace(" ", "").replace("\xa0", ""))
            # print(f"Price: {price}")
            status = (
                item.locator("div.catalogCard-availability")
                .text_content()
                .strip()
            )
            # print(f"Status: {status}")
            if status == "Немає в наявності":
                continue
            # print(f"Name: {name}, Price: {price}, URL: {item_url}, Status: {status}")
            item_data = Item(
                src=SOURCE,
                category="All",
                name=name,
                price=price,
                url=item_url,
                status=status,
            )
            items_.append(item_data)
        next_button = page.locator("a.pager__item--forth:not(.is-disabled)")
        if next_button.count() == 1:
            if page_number >= 5:
                break
            page_number += 1
            # print(f"Next page: {page_number}")
            page.goto(f"{base_url}/ua/katalog/search/filter/page={page_number}/?q={query}")
            # time.sleep(2)
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
    query = "4"
    main(query)
