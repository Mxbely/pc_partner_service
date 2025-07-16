from dataclasses import dataclass


base_context = {
    "user_agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0",
    "viewport": {"width": 1280, "height": 720},
    "java_script_enabled": True,
    "locale": "uk-UA",
    "geolocation": {"longitude": 30.5238, "latitude": 50.4547},  # Київ
    "device_scale_factor": 1,
    "is_mobile": False,
    "has_touch": False,
    "timezone_id": "Europe/Kyiv",
    "permissions": ["geolocation", "notifications"],
    "reduced_motion": "no-preference",  # або "reduce"
    "extra_http_headers": {
        "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7"
    },
}

@dataclass
class Item:
    src: str
    name: str
    price: str
    url: str
    status: str


class BaseParser:
    def __init__(self, query: str) -> None:
        self.query = query

    def parse(self):
        raise NotImplementedError