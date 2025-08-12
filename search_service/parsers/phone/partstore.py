import os
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

SOURCE = "partstore.crm-onebox.com"
FILE_NAME = f"partstore_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"

LOGIN = os.getenv("PARTSTORE_LOGIN")
PASSWORD = os.getenv("PARTSTORE_PASS")

# if not LOGIN or not PASSWORD:
#     raise Exception("PARTSTORE_LOGIN or PARTSTORE_PASS is not set")


class PartStore1Parser(BaseParser):
    def parse(self):
        with sync_playwright() as playwright:
            run(playwright, self.query, self.filename)


def parse_availability(td_element) -> bool:
    rows = td_element.locator("table tbody tr")
    count = rows.count()
    for j in range(count):
        row = rows.nth(j)
        count_str = row.locator("td").nth(1).text_content().strip()
        count_str = count_str.replace(">", "").replace("<", "")
        if int(count_str) > 0:
            return True
    return False


def run(playwright: Playwright, query: str, filename: str) -> None:
    if check_parser_file(filename):
        return filename

    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(**base_context)
    page = context.new_page()
    page_number = 0
    base_url = "https://partstore.crm-onebox.com"
    url = f"{base_url}/client/login/"

    page.goto(url)
    page.locator("input[name=\"login\"]").click()
    page.locator("input[name=\"login\"]").fill(LOGIN)
    page.locator("input[name=\"password\"]").click()
    page.locator("input[name=\"password\"]").fill(PASSWORD)
    page.get_by_role("button", name="Войти в кабинет клиента").click()
    page.get_by_role("link", name="Продукты").click()
    page.get_by_role("textbox", name="Название продукта").click()
    page.get_by_role("textbox", name="Название продукта").fill(query)
    page.get_by_role("button", name="Показать").click()

    empty = page.locator("div.nc-message-info")

    if empty.count() == 1:
        return

    selector = "table.os-table > tbody > tr"
    page.wait_for_selector(selector)
    items_ = []
    while True:
        items = page.locator(selector)
        visible_items = items.filter(has=page.locator(":visible"))
        count = visible_items.count()

        if count == 0:
            break

        for i in range(count):
            item = items.nth(i)
            name = item.locator("td").nth(1).text_content().strip()
            name = name.replace(",", "")
            availability_td = item.locator("td").nth(3)

            if not parse_availability(availability_td):
                continue

            status = "В наявності"
            price_input = item.locator("> td").nth(5).locator("input")
            count_price = price_input.count()

            if count_price == 0:
                continue

            price = float(price_input.first.get_attribute("value"))

            item_data = Item(
                src=SOURCE,
                category="All",
                name=name,
                price=price,
                url=url,
                status=status,
            )
            items_.append(item_data)
        paginator = page.locator("div.ob-block-stepper")
        next_button = paginator.locator("a.next")

        if next_button.count():
            page_number += 1
            if page_number > 1:  # Two pages
                break
            query = re.sub(r"\s+", "+", query)
            url_ = f"https://partstore.crm-onebox.com/client/product/list/?filternameproduct={query}&articul=&avail=1&currency=&page={page_number}"
            page.goto(url_, wait_until="networkidle")
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
    query = "1 2"
    main(query)
