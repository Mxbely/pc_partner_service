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

SOURCE = "allnotebookparts.ua"
FILE_NAME = f"allnotebookparts_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class AllnotebookpartsParser(BaseParser):
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

    base_url = "https://allnotebookparts.com.ua"
    url = f"{base_url}/ua/site_search?search_term={query}"
    page.goto(url)
    selector = "li.cs-product-gallery__item"
    empty_text = page.locator("span.cs-count.cs-search-result-info__counter").text_content().strip()
    counter = int(empty_text.split(" ")[0])
    if counter == 0:
        return

    items_ = []
    while True:
        items = page.locator(selector)
        count = page.locator(selector).count()

        for i in range(count):
            item = items.nth(i)
            name = item.locator("div.cs-goods-title-wrap a.cs-goods-title").text_content().strip().replace(",", "")
            if not any(word.lower() in name.lower() for word in separated_query):
                continue
            item_url = base_url + item.locator("div.cs-goods-title-wrap a.cs-goods-title").get_attribute("href").strip()
            price = item.locator("div.cs-goods-price.cs-product-gallery__price span.cs-goods-price__value").first.text_content().strip()
            if price == "Ціну уточнюйте":
                continue
            price = float(price.replace("від", "").replace("/пара", "").replace("₴", "").replace("\xa0", "").replace(" ", "").replace(",", "."))
            status = (
                item.locator("span.cs-goods-data__state").first
                .text_content()
                .strip()
            )
            if status == "Немає в наявності":
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
        next_button = page.locator("div.b-pager a.b-pager__link.b-pager__link_pos_last")
        if next_button.count() == 1:
            next_button.click()
            page.wait_for_selector(selector)
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
    query = "батарея lenovo V310-15IKB"
    main(query)
