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

SOURCE = "tplus.market"
FILE_NAME = f"tplus.market_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class TplusParser(BaseParser):
    def parse(self):
        with sync_playwright() as playwright:
            run(playwright, self.query, self.filename)


def run(playwright: Playwright, query: str, filename: str) -> None:
    delete_file(filename)
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(**base_context)   
    page = context.new_page()
    page.set_default_timeout(10000)
    query = re.sub(r"\s+", "+", query)
    base_url = "https://tplus.market"
    url = f"{base_url}/search?search={query}&limit=50"
    page.goto(url)
    page.get_by_role("button", name="Погоджуюсь").click()

    button = page.locator("button.v-btn.v-btn--has-bg.theme--light.v-size--default.primary")
    if button.count():
        return

    page.wait_for_selector(".product-item")
    items = page.locator(".product-item")
    count = page.locator(".product-item").count()
    items_ = []
    for i in range(count):
        item = items.nth(i)
        name = (
            item.locator("a.product-item--name div span")
            .text_content()
            .strip()
            .replace(",", "")
        )
        url = (
            base_url
            + item.locator("a.product-item--name").get_attribute("href").strip()
        )
        price = (
            item.locator("div.product-item--price span")
            .text_content()
            .strip()
            .replace(",", ".")
        )
        status_none = item.locator(
            ".v-icon.notranslate.mdi.mdi-calendar-clock.theme--dark"
        )
        status_nth = item.locator(
            ".v-icon.notranslate.mdi.mdi-basket-plus-outline.theme--light"
        )
        status_offer = item.locator(
            ".v-icon.notranslate.mdi.mdi-human-dolly.theme--dark"
        )
        if status_nth.count() or status_none.count():
            continue
        status = "В наявності"
        if status_offer.count():
            status = "Можна замовити"
        item_data = Item(
            src=SOURCE,
            category="all",
            name=name,
            price=price,
            url=url,
            status=status,
        )
        items_.append(item_data)
    write_to_csv(items_, filename)
    del items_

    # ---------------------
    context.close()
    browser.close()


def main(query: str):

    with sync_playwright() as playwright:
        run(playwright, query, FILE_NAME)


if __name__ == "__main__":
    query = "батарея acer AS"
    main(query)
