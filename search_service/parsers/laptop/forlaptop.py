
from pathlib import Path
from search_service.parsers.base import BaseParser, base_context, Item, write_to_csv, delete_file
import re
from playwright.sync_api import Playwright, sync_playwright, expect
import time
from datetime import datetime

SOURCE = "4laptop.kiev.ua"
FILE_NAME = f"4laptop{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"

class ForLaptopKievParser(BaseParser):
    def parse(self):
        with sync_playwright() as playwright:
            run(playwright, self.query, self.filename)


def wait_for_stable_items(page, selector: str, stable_time: float = 1.5, timeout: float = 10.0, poll_interval: float = 0.2) -> int:
    """
    Чекає, поки кількість елементів за селектором перестане змінюватися.

    :param page: Playwright page object
    :param selector: CSS-селектор для елементів
    :param stable_time: час стабільності (сек.), після якого вважається, що елементи завантажено
    :param timeout: загальний таймаут очікування (сек.)
    :param poll_interval: як часто перевіряти (сек.)
    :return: остаточна кількість елементів
    """
    start = time.time()
    last_count = -1
    stable_since = time.time()

    while True:
        count = page.locator(selector).count()
        now = time.time()

        if count != last_count:
            last_count = count
            stable_since = now

        if now - stable_since >= stable_time:
            break

        if now - start >= timeout:
            break

        time.sleep(poll_interval)

    return last_count


def run(playwright: Playwright, query: str, filename: str) -> None:
    delete_file(filename)
    print(f"Start query: {query}")
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(**base_context)
    page = context.new_page()
    page.goto("https://4laptop.kiev.ua/ua")
    page.get_by_role("textbox", name="Пошук товару в магазині").click()
    page.get_by_role("textbox", name="Пошук товару в магазині").fill(query)
    page.get_by_role("textbox", name="Пошук товару в магазині").press("Enter")
    page.locator('button.btn-limits').click()
    page.wait_for_selector('ul.dropdown-menu')
    page.locator('ul.dropdown-menu a', has_text='100').click()

    selector = ".category-page .product-layout"

    count = wait_for_stable_items(page, selector)
    print(f"Count: {count}")
    items = page.locator(selector)

    if items.count() == 0:
        print("Lap No items found")
        return

    items_ = []
    for i in range(items.count()):
        name = items.nth(i).locator(".product-name a").inner_text()
        name = name.replace(",", "")
        link = items.nth(i).locator(".product-name a").get_attribute("href")
        price = items.nth(i).locator(".price .price_no_format").inner_text()
        status = items.nth(i).locator(".stock-status").inner_text()
        items_.append(Item(src=SOURCE, category="all", name=name, price=price, url=link, status=status))

    write_to_csv(items_, filename)

    # ---------------------
    context.close()
    browser.close()

def main(query: str):
    
    with sync_playwright() as playwright:
        run(playwright, query)

if __name__ == "__main__":
    query = "блок живлення"
    # query = "матриця 15.6"
    main(query)