import re
import time
from datetime import datetime

import requests
from playwright.sync_api import Playwright, expect, sync_playwright

from search_service.parsers.base import (
    BaseParser,
    Item,
    base_context,
    delete_file,
    write_to_csv,
)

SOURCE = "https://motorolka.org.ua/"
FILE_NAME = f"motorolka_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class MotorolkaParser(BaseParser):
    def parse(self):
        # with sync_playwright() as playwright:
        run(self.query, self.filename)


def run(query, filename: str) -> None:
    print(f"Start query: {query}")
    delete_file(filename)
    url = "https://motorolka.org.ua/multisearch/searchProducts.php"
    params = {"search": query}
    headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}

    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    # print(f"Response: {data}")
    item_groups = data.get("results", {}).get("item_groups", {})
    items_ = []
    for group in item_groups.values():
        category_name = group["category"]["name"]
        for item in group["items"].values():
            # product = {
            #     "category": category_name,
            #     "name": item["name"],
            #     "price": item["price"],
            #     "url": item["url"]
            # }
            item = Item(
                src=SOURCE,
                category=category_name,
                name=item["name"].replace(",", ""),
                price=item["price"],
                url=item["url"],
                status="В наявності" if item["price"] else "Відсутній",
            )
            items_.append(item)
    write_to_csv(items_, filename)
    del items_


def main(query: str):

    with sync_playwright() as playwright:
        run(playwright, query, FILE_NAME)


if __name__ == "__main__":
    query = "екран"
    main(query)
