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

SOURCE = "gsm-complect.ua"
FILE_NAME = f"gsm_complect_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class GsmComplectParser(BaseParser):
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
    separated_query = query.split()

    base_url = "https://gsm-komplekt.ua/ua"
    page.goto(base_url)
    page.get_by_role("textbox", name="Пошук").click()
    page.get_by_role("textbox", name="Пошук").fill(query)
    page.get_by_role("button", name="Пошук").click()
    page.wait_for_selector("div.content")
    empty_text = page.locator("div.content p.alert.alert-warning")
    if empty_text.count() == 1:
        return
    page.wait_for_selector("div.product-container")
    button_counter = 1
    while True:
        button = page.locator("div.ajax-btn-container div.ajax-more-btn:not([style*='display: none'])")
        if button.count() == 1 and button.is_visible():
            if button_counter > 5:
                break
            prev_count = page.locator("div.product-container").count()
            button.click()
            button_counter += 1
            page.wait_for_function(
                "oldCount => document.querySelectorAll('div.product-container').length > oldCount",
                arg=prev_count,
                timeout=10000,
            )
        else: 
            break
    selector = "div.product-container"

    items_ = []
    items = page.locator(selector)
    count = page.locator(selector).count()

    for i in range(count):
        item = items.nth(i)
        name = item.locator("p.product-name-p a").text_content().strip().replace(",", "")
        if not any(word.lower() in name.lower() for word in separated_query):
            continue
        item_url = item.locator("p.product-name-p a").get_attribute("href").strip()
        price = item.locator("div.content_price div.prices-container-div-price span").first
        if price.count() == 0:
            continue
        price = float(
            price.text_content().strip().replace("грн", "").replace(" ", "").replace("\xa0", "")
        )
        status = (
            item.locator("span.availability span")
            .last
            .text_content()
            .strip()
        )
        if status != "Є в наявності":
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
    query = "батарея ipad"
    main(query)
