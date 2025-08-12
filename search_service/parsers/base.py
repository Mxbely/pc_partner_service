import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from search_service.parsers import DEFAULT_DIR

base_context = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "viewport": {"width": 1280, "height": 800},
    "locale": "uk-UA",
    "timezone_id": "Europe/Kyiv",
    "permissions": ["geolocation", "notifications"],
    "java_script_enabled": True,
    "geolocation": {"longitude": 30.5238, "latitude": 50.4547},
    "is_mobile": False,
    "device_scale_factor": 1,
    "has_touch": False,
    "extra_http_headers": {"Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7"},
}


@dataclass
class Item:
    src: str
    category: str
    name: str
    price: str
    url: str
    status: str


class BaseParser:
    def __init__(self, query: str) -> None:
        self.query = query
        self.filename = os.path.join(
            DEFAULT_DIR,
            f"{self.query.replace(" ", "_")}_{type(self).__name__}{datetime.today().strftime('%Y-%m-%d')}.csv",
        )

    def parse(self):
        raise NotImplementedError


def check_parser_file(filename: str) -> str:
    if os.path.exists(filename):
        return filename


def write_to_csv(items: list[Item], filename: str):
    if os.path.exists(filename):
        os.remove(filename)
    with open(filename, "a") as f:
        f.write("src,category,name,price,url,status\n")
    with open(filename, "a") as f:
        for item in items:
            f.write(
                f"{item.src},{item.category},{item.name},{item.price},{item.url} ,{item.status}\n"
            )
