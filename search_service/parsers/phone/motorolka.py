from datetime import datetime

import requests

from search_service.parsers.base import (
    BaseParser,
    Item,
    base_context,
    delete_file,
    write_to_csv,
)

SOURCE = "motorolka.org.ua"
FILE_NAME = f"motorolka_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class MotorolkaParser(BaseParser):
    def parse(self):
        run(self.query, self.filename)


def run(query, filename: str) -> None:
    delete_file(filename)
    url = "https://motorolka.org.ua/multisearch/searchProducts.php"
    params = {"search": query}
    headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}

    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    item_groups = data.get("results", {}).get("item_groups", {})
    items_ = []
    for group in item_groups.values():
        category_name = group["category"]["name"]
        for item in group["items"].values():
            price = item["price"]
            if not price:
                continue
            item = Item(
                src=SOURCE,
                category=category_name,
                name=item["name"].replace(",", ""),
                price=item["price"],
                url=item["url"],
                status="В наявності",
            )
            items_.append(item)
    write_to_csv(items_, filename)
    del items_


def main(query: str):

    run(query, FILE_NAME)


if __name__ == "__main__":
    query = "екран"
    main(query)
