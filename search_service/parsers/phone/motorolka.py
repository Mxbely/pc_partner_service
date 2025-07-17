from datetime import datetime
import re
import time
from playwright.sync_api import Playwright, sync_playwright, expect
from search_service.parsers.base import BaseParser, base_context, Item, write_to_csv, delete_file

SOURCE = "https://motorolka.org.ua/"
FILE_NAME = f"motorolka{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class MotorolkaParser(BaseParser):
    def parse(self):
        with sync_playwright() as playwright:
            run(playwright, self.query, self.filename)


def run(playwright: Playwright, query, filename: str) -> None:
    print(f"Start query: {query}")
    delete_file(filename)
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(**base_context)
    page = context.new_page()
    page.goto("https://motorolka.org.ua/")
    page.wait_for_timeout(1000)
    page.get_by_role("textbox", name="Що шукаємо?)").click()
    page.wait_for_timeout(1000)
    page.locator("[id=\"q\"]").fill(query)
    page.wait_for_timeout(1000)
    page.locator("[id=\"q\"]").click()
    page.locator("[id=\"q\"]").press("Enter")
    # time.sleep(3)

    categories = page.locator("div.multi-taxon")
    print(f"Кількість категорій: {categories.count()}")

    if categories.count() == 0:
        print("Moto No items found")
        return
    
    for i in range(categories.count()):
        if i == 0:
            continue
        categories = page.locator("div.multi-taxon")
        category = categories.nth(i).locator("span").first.inner_text()
        # name = name.strip()
        print(f"Перехід на категорію: {category}")
        page.wait_for_timeout(500)

        # Клікаємо по div.multi-taxon
        categories.nth(i).click()
        page.wait_for_timeout(500)

        items = page.locator("div.multi-item")
        items_ = []
        print(f"Кількість елементів: {items.count()}")
        for i in range(items.count()):
            content = items.nth(i).locator(".multi-content")
            name = content.locator("a span").inner_text()
            name = name.replace(",", "")
            price = content.locator(".multi-price").inner_text()
            
            link = items.nth(i).locator(".multi-content a").get_attribute("href")
            status = "Відсутній"
            if price:
                status = "В наявності"
            items_.append(Item(src=SOURCE, category=category, name=name, price=price, url=link, status=status))
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