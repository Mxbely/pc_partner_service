from datetime import datetime

import requests

from search_service.parsers.base import (
    BaseParser,
    Item,
    base_context,
    check_parser_file,
    write_to_csv,
)

SOURCE = "motorolka.org.ua"
FILE_NAME = f"motorolka_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class MotorolkaParser(BaseParser):
    def parse(self):
        run(self.query, self.filename)


def run(query, filename: str) -> None:
    if check_parser_file(filename):
        return filename
    url = "https://motorolka.org.ua/multisearch/searchProducts.php"
    params = {"search": query}
    headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}
    try:
        response = requests.get(url, params=params, headers=headers)
    except requests.exceptions.RequestException as e:
        print(e)
        return
    data = response.json()
    item_groups = data.get("results", {}).get("item_groups", {})
    items_ = []

    for group in item_groups.values():
        category_name = group["category"]["name"].replace(",", "/")

        for item in group["items"].values():
            price = item["price"]

            if not price:
                continue

            item = Item(
                src=SOURCE,
                category=category_name,
                name=item["name"].replace(",", ""),
                price=float(item["price"].replace(",", ".")),
                url=item["url"],
                status="В наявності",
            )
            items_.append(item)
    items_ = sorted(items_, key=lambda x: x.price, reverse=True)
    write_to_csv(items_, filename)
    del items_


def main(query: str):
    run(query, FILE_NAME)


if __name__ == "__main__":
    query = "екран"
    main(query)
