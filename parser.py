import requests
from lxml import etree
import json
from datetime import datetime

FEED_URL="https://zetzet.ru/yandexmarket/26adc4f2-5a1f-417b-b3a0-8f37e0be1b79.xml"

def parse_feed():
    r=requests.get(FEED_URL,timeout=60)
    root=etree.fromstring(r.content)

    categories={c.attrib["id"]:c.text for c in root.xpath("//category")}

    products=[]

    for offer in root.xpath("//offer"):
        p={
            "name": offer.findtext("name") or "",
            "brand": offer.findtext("vendor") or "",
            "price": float(offer.findtext("price") or 0),
            "url": offer.findtext("url") or "",
            "category": categories.get(offer.findtext("categoryId"), ""),
            "description": offer.findtext("description") or ""
        }

        p["search_text"]=(p["name"]+" "+p["brand"]+" "+p["category"]+" "+p["description"]).lower()
        products.append(p)

    with open("zetzet_knowledge.json","w",encoding="utf-8") as f:
        json.dump({
            "shop":"ZetZet.ru",
            "updated":datetime.now().isoformat(),
            "products":products
        },f,ensure_ascii=False)

    return len(products)
