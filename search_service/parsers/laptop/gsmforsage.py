from datetime import datetime

import requests

from search_service.parsers.base import (
    BaseParser,
    Item,
    base_context,
    delete_file,
    write_to_csv,
)

SOURCE = "gsm-forsage.com.ua"
FILE_NAME = f"gsm-forsage_{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"


class GSMForsageParser(BaseParser):
    def parse(self):
        run(self.query, self.filename)


def run(query, filename: str) -> None:
    delete_file(filename)
    url = "https://gsm-forsage.com.ua/qmultisearch/result/get/"
    params = {
        "query": query,
        "id": "12083",
        "s": "large",
        "fields": "true",
        "results": "1",
        "lang": "uk",
        "categories": "0",
        "uid": "necb9ru2rr",
        "limit": "100",
        "offset": "0",
        "sort": "ordering.asc",
    }
    headers = {"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"}
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    items = data.get("results", {}).get("items", {})
    items_ = []
    for item in items:
        if not any(stock for stock in item["stocks"] if stock["qty"] == "В наявності"):
            continue
        item = Item(
            src=SOURCE,
            category="all",
            name=item["name"].replace(",", ""),
            price=float(item["price"].replace(",", ".").replace(" грн.", "")),
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
