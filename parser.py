import json
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path

import requests
from lxml import etree

FEED_URL = os.getenv(
    "FEED_URL",
    "https://zetzet.ru/yandexmarket/26adc4f2-5a1f-417b-b3a0-8f37e0be1b79.xml",
)
JSON_PATH = Path(os.getenv("JSON_PATH", "zetzet_knowledge.json"))
# Через сколько часов данные считаются устаревшими и выгрузка перечитывается сама.
# 0 — отключить автообновление (тогда только через /update).
REFRESH_HOURS = float(os.getenv("REFRESH_HOURS", "6"))

COMPAT_PARAM = "Выбрать смартфон"
COLOR_PARAMS = {"Цвет", "Цвет."}
SKIP_PARAMS = {"Артикул id", COMPAT_PARAM} | COLOR_PARAMS

DEVICE_RE = re.compile(
    r"\b(?:"
    r"iPhone\s+(?:\d{1,2}e?|Air|SE)(?:\s+(?:Pro\s+Max|Pro|Plus|Max|mini|Air))?"
    r"|iPad(?:\s+(?:Pro|Air|mini))?(?:\s+\d{1,2}(?:[.,]\d)?)?"
    r"|MacBook\s+(?:Air|Pro)(?:\s+\d{2})?"
    r"|Apple\s+Watch(?:\s+(?:Ultra|Series|SE))?(?:\s+\d{1,2})?"
    r"|AirPods(?:\s+(?:Pro|Max))?(?:\s+\d)?"
    r"|Samsung\s+(?:Galaxy\s+)?[SA]\d{1,2}(?:\s+(?:Ultra|Plus|FE))?"
    r"|(?:Samsung\s+)?(?:Galaxy\s+)?Z\s+(?:Fold|Flip)\s*\d"
    r")",
    re.IGNORECASE,
)

# Как клиенты пишут в директе: транслит, сленг, опечатки.
SYNONYMS = [
    (r"iphone", "айфон"),
    (r"ipad", "айпад"),
    (r"macbook", "макбук"),
    (r"airpods", "аирподс, эирподс, наушники"),
    (r"apple watch", "эпл вотч, часы"),
    (r"samsung|galaxy", "самсунг, галакси"),
    (r"xiaomi|redmi", "сяоми, ксиаоми, редми"),
    (r"pro max", "про макс"),
    (r"кевлар|kevlar|aramid|арамид", "кевлар, кивлар, арамид, kevlar"),
    (r"magsafe", "магсейф, магнитный"),
    (r"чехол|case", "чехол, кейс"),
    (r"стекло|glass", "защитное стекло, бронестекло"),
    (r"пл[её]нк", "плёнка, пленка"),
    (r"аккумулятор|power ?bank|пауэрбанк", "пауэрбанк, повербанк, внешний аккумулятор"),
    (r"type-c|usb-c", "тайп си, type-c, usb-c"),
    (r"lightning", "лайтнинг"),
    (r"наушник|earbuds|headphones", "наушники"),
    (r"зарядн|charger", "зарядка, зарядное устройство"),
    (r"кабел|cable", "кабель, провод, шнур"),
    (r"кондиционер|сплит", "кондиционер, сплит-система"),
    (r"пылесос", "пылесос"),
    (r"картхолдер|кардхолдер|cardholder|wallet", "картхолдер, кардхолдер, кошелек"),
]

TRANSLIT = [
    ("iphone", "айфон"),
    ("ipad", "айпад"),
    ("macbook", "макбук"),
    ("airpods", "аирподс"),
    ("apple watch", "эпл вотч"),
    ("samsung", "самсунг"),
    ("galaxy", "галакси"),
    ("pro max", "про макс"),
    ("pro", "про"),
    ("max", "макс"),
    ("ultra", "ультра"),
    ("plus", "плюс"),
    ("mini", "мини"),
    ("air", "эйр"),
    ("fold", "фолд"),
    ("flip", "флип"),
]

_lock = threading.Lock()
_cache = {"mtime": None, "data": None, "by_id": {}}


def clean_text(value: str) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def _category_path(category_id, categories):
    names = []
    seen = set()
    while category_id and category_id in categories and category_id not in seen:
        seen.add(category_id)
        parent_id, name = categories[category_id]
        if name:
            names.append(name)
        category_id = parent_id
    return " → ".join(reversed(names))


def _devices(name, compat_params):
    found = []
    seen = set()
    for value in list(compat_params) + DEVICE_RE.findall(name):
        device = clean_text(value)
        key = device.lower()
        if device and key not in seen:
            seen.add(key)
            found.append(device)
    return found


def _translit(device):
    result = device.lower()
    for latin, cyrillic in TRANSLIT:
        result = re.sub(r"\b" + latin + r"\b", cyrillic, result)
    return result


def _keywords(name, category_path, devices):
    text = " ".join([name, category_path] + devices).lower()
    words = []
    for pattern, synonyms in SYNONYMS:
        if re.search(pattern, text):
            words.extend(word.strip() for word in synonyms.split(","))
    words.extend(_translit(device) for device in devices)
    unique = []
    for word in words:
        if word not in unique:
            unique.append(word)
    return ", ".join(unique)


def parse_feed() -> int:
    response = requests.get(
        FEED_URL,
        timeout=180,
        headers={"User-Agent": "ZetZet-FastBots/2.0"},
    )
    response.raise_for_status()

    root = etree.fromstring(response.content)
    categories = {
        category.attrib["id"]: (
            category.attrib.get("parentId"),
            clean_text(category.text or ""),
        )
        for category in root.xpath("//category")
    }

    products = []

    for offer in root.xpath("//offer"):
        category_id = offer.findtext("categoryId") or ""
        name = clean_text(offer.findtext("name") or "")

        compat_params = []
        colors = []
        params = []
        for param in offer.findall("param"):
            param_name = clean_text(param.attrib.get("name", ""))
            param_value = clean_text(param.text or "")
            if not param_name or not param_value:
                continue
            if param_name == COMPAT_PARAM:
                compat_params.append(param_value)
            elif param_name in COLOR_PARAMS:
                colors.append(param_value)
            elif param_name not in SKIP_PARAMS:
                params.append([param_name, param_value])

        category_path = _category_path(category_id, categories)
        devices = _devices(name, compat_params)

        product = {
            "id": offer.attrib.get("id", ""),
            "available": offer.attrib.get("available", "false") == "true",
            "name": name,
            "brand": clean_text(offer.findtext("vendor") or ""),
            "vendor_code": clean_text(offer.findtext("vendorCode") or ""),
            "price": float(offer.findtext("price") or 0),
            "currency": clean_text(offer.findtext("currencyId") or "RUB"),
            "category": categories.get(category_id, (None, ""))[1],
            "category_path": category_path,
            "compatible": devices,
            "colors": colors,
            "params": params,
            "keywords": _keywords(name, category_path, devices),
            "description": clean_text(offer.findtext("description") or ""),
            "url": clean_text(offer.findtext("url") or ""),
        }

        product["search_text"] = " ".join(
            [
                product["name"],
                product["brand"],
                product["category_path"],
                product["keywords"],
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

    tmp_path = JSON_PATH.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False)
    tmp_path.replace(JSON_PATH)

    return len(products)


def _is_stale():
    if not JSON_PATH.exists():
        return True
    if REFRESH_HOURS <= 0:
        return False
    age_hours = (time.time() - JSON_PATH.stat().st_mtime) / 3600
    return age_hours > REFRESH_HOURS


def load_data():
    with _lock:
        if _is_stale():
            try:
                parse_feed()
            except Exception as error:  # сайт недоступен — отдаём последние данные
                if not JSON_PATH.exists():
                    raise
                print(f"Feed refresh failed, serving cached data: {error}")

        mtime = JSON_PATH.stat().st_mtime
        if _cache["mtime"] != mtime:
            with JSON_PATH.open(encoding="utf-8") as file:
                data = json.load(file)
            _cache["data"] = data
            _cache["by_id"] = {
                str(product.get("id")): product
                for product in data.get("products", [])
            }
            _cache["mtime"] = mtime

        return _cache["data"]


def get_product(product_id):
    load_data()
    return _cache["by_id"].get(str(product_id))
