import json
from datetime import datetime

import requests
from lxml import etree

FEED_URL = "https://zetzet.ru/yandexmarket/26adc4f2-5a1f-417b-b3a0-8f37e0be1b79.xml"
JSON_PATH = "zetzet_knowledge.json"
TEXT_PATH = "zetzet_knowledge.txt"


def clean_text(value: str) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def parse_feed() -> int:
    response = requests.get(
        FEED_URL,
        timeout=120,
        headers={"User-Agent": "ZetZet-Knowledge-Bot/1.0"},
    )
    response.raise_for_status()

    root = etree.fromstring(response.content)
    categories = {
        category.attrib["id"]: clean_text(category.text or "")
        for category in root.xpath("//category")
    }

    products = []
    text_blocks = []

    for offer in root.xpath("//offer"):
        category_id = offer.findtext("categoryId") or ""
        pictures = [
            clean_text(picture.text or "")
            for picture in offer.findall("picture")
            if clean_text(picture.text or "")
        ]

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
            "pictures": pictures,
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

        availability = "В наличии" if product["available"] else "Нет в наличии"
        text_blocks.append(
            "\n".join(
                [
                    f"ТОВАР: {product['name']}",
                    f"БРЕНД: {product['brand'] or 'Не указан'}",
                    f"КАТЕГОРИЯ: {product['category'] or 'Не указана'}",
                    f"ЦЕНА: {product['price']:.0f} {product['currency']}",
                    f"НАЛИЧИЕ: {availability}",
                    f"ССЫЛКА: {product['url']}",
                    f"ОПИСАНИЕ: {product['description'] or 'Описание отсутствует'}",
                ]
            )
        )

    payload = {
        "shop": "ZetZet.ru",
        "updated": datetime.now().isoformat(),
        "products_count": len(products),
        "products": products,
    }

    with open(JSON_PATH, "w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, ensure_ascii=False)

    header = "\n".join(
        [
            "БАЗА ТОВАРОВ ИНТЕРНЕТ-МАГАЗИНА ZETZET.RU",
            f"Обновлено: {payload['updated']}",
            f"Количество товаров: {len(products)}",
            "",
            "Используй только указанные в базе цены, характеристики, наличие и ссылки.",
            "Если точного товара нет, предложи близкие варианты и уточни потребность клиента.",
            "",
        ]
    )

    with open(TEXT_PATH, "w", encoding="utf-8") as text_file:
        text_file.write(header)
        text_file.write("\n\n---\n\n".join(text_blocks))

    return len(products)
