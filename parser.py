import requests, json
from lxml import etree
from datetime import datetime

FEED_URL="https://zetzet.ru/yandexmarket/26adc4f2-5a1f-417b-b3a0-8f37e0be1b79.xml"

def parse_feed():
    r=requests.get(FEED_URL,timeout=60)
    root=etree.fromstring(r.content)
    cats={x.attrib["id"]:x.text for x in root.xpath("//category")}
    products=[]
    for o in root.xpath("//offer"):
        p={
        "id":o.attrib.get("id"),
        "name":o.findtext("name") or "",
        "brand":o.findtext("vendor") or "",
        "price":float(o.findtext("price") or 0),
        "url":o.findtext("url") or "",
        "category":cats.get(o.findtext("categoryId"),""),
        "description":o.findtext("description") or ""
        }
        p["search_text"]=(p["name"]+" "+p["brand"]+" "+p["category"]+" "+p["description"]).lower()
        products.append(p)
    json.dump({"shop":"ZetZet.ru","updated":datetime.now().isoformat(),"products":products},
              open("zetzet_knowledge.json","w",encoding="utf-8"),ensure_ascii=False)
    return len(products)
