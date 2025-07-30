from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# base_context = {
#     "user_agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
#     "viewport": {"width": 1280, "height": 720},
#     "java_script_enabled": True,
#     "locale": "uk-UA",
#     "geolocation": {"longitude": 30.5238, "latitude": 50.4547},  # Київ
#     "device_scale_factor": 1,
#     "is_mobile": False,
#     "has_touch": False,
#     "timezone_id": "Europe/Kyiv",
#     "permissions": ["geolocation", "notifications"],
#     "reduced_motion": "no-preference",  # або "reduce"
#     "extra_http_headers": {"Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7"},
# }
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
    "extra_http_headers": {
        "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7"
    }
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
        self.filename = (
            f"{type(self).__name__}{datetime.today().strftime('%Y-%m-%d_%H-%M')}.csv"
        )

    def parse(self):
        raise NotImplementedError


def delete_file(filename: str):
    if Path(filename).exists():
        Path(filename).unlink()


def write_to_csv(items: list[Item], filename: str):
    if not Path(filename).exists():
        with open(filename, "a") as f:
            f.write("src,category,name,price,url,status\n")

    with open(filename, "a") as f:
        for item in items:
            f.write(
                f"{item.src},{item.category},{item.name},{item.price},{item.url} ,{item.status}\n"
            )
