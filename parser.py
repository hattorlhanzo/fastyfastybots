import json
from datetime import datetime
from pathlib import Path

import requests
from lxml import etree

FEED_URL = "https://zetzet.ru/yandexmarket/26adc4f2-5a1f-417b-b3a0-8f37e0be1b79.xml"
JSON_PATH = Path("zetzet_knowledge.json")


def clean_text(value: str) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def parse_feed() -> int:
    response = requests.get(
        FEED_URL,
        timeout=180,
        headers={"User-Agent": "ZetZet-FastBots/2.0"},
    )
    response.raise_for_status()

    root = etree.fromstring(response.content)
    categories = {
        category.attrib["id"]: clean_text(category.text or "")
        for category in root.xpath("//category")
    }

    products = []

    for offer in root.xpath("//offer"):
        category_id = offer.findtext("categoryId") or ""

        product = {
            "id": offer.attrib.get("id", ""),
            "available": offer.attrib.get("available", "false") == "true",
            "name": clean_text(offer.findtext("name") or ""),
            "brand": clean_text(offer.findtext("vendor") or ""),
            "price": float(offer.findtext("price") or 0),
            "currency": clean_text(offer.findtext("currencyId") or "RUB"),
            "category": categories.get(category_id, ""),
            "description": clean_text(offer.findtext("description") or ""),
            "url": clean_text(offer.findtext("url") or ""),
        }

        product["search_text"] = " ".join(
            [
                product["name"],
                product["brand"],
                product["category"],
                product["description"],
            ]
        ).lower()

        products.append(product)

    payload = {
        "shop": "ZetZet.ru",
        "updated": datetime.now().isoformat(),
        "products_count": len(products),
        "products": products,
    }

    with JSON_PATH.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False)

    return len(products)


def load_data():
    if not JSON_PATH.exists():
        parse_feed()

    with JSON_PATH.open(encoding="utf-8") as file:
        return json.load(file)
