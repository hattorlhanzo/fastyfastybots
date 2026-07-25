import requests
from lxml import etree
import json
from datetime import datetime

FEED_URL = "https://zetzet.ru/yandexmarket/26adc4f2-5a1f-417b-b3a0-8f37e0be1b79.xml"

def parse_feed():
    response = requests.get(FEED_URL, timeout=60)
    response.encoding = "utf-8"

    root = etree.fromstring(response.content)

    categories = {}
    for cat in root.xpath("//category"):
        categories[cat.attrib["id"]] = cat.text

    products = []

    for offer in root.xpath("//offer"):
        item = {
            "id": offer.attrib.get("id"),
            "available": offer.attrib.get("available"),
            "name": offer.findtext("name"),
            "brand": offer.findtext("vendor"),
            "price": offer.findtext("price"),
            "url": offer.findtext("url"),
            "category": categories.get(offer.findtext("categoryId"), ""),
            "description": offer.findtext("description") or ""
        }

        item["search_text"] = f"""
Товар: {item['name']}
Бренд: {item['brand']}
Категория: {item['category']}
Цена: {item['price']} рублей
Описание: {item['description']}
"""
        products.append(item)

    result = {
        "shop": "ZetZet.ru",
        "updated": datetime.now().isoformat(),
        "products": products
    }

    with open("zetzet_knowledge.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return len(products)

if __name__ == "__main__":
    print("Обработано товаров:", parse_feed())
