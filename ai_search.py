import json
import re
from pathlib import Path

JSON_PATH = Path("zetzet_knowledge.json")


def ai_search(query: str, limit: int = 5):
    if not JSON_PATH.exists():
        return []

    with JSON_PATH.open(encoding="utf-8") as source:
        data = json.load(source)

    normalized_query = query.lower().strip()
    words = [word for word in re.findall(r"[a-zа-яё0-9\-]+", normalized_query) if len(word) > 1]

    max_price = None
    price_match = re.search(r"(?:до|не дороже|максимум)\s*(\d[\d\s]*)", normalized_query)
    if price_match:
        max_price = float(price_match.group(1).replace(" ", ""))

    results = []

    for product in data.get("products", []):
        if not product.get("available", False):
            continue

        search_text = product.get("search_text", "")
        score = sum(1 for word in words if word in search_text)

        if normalized_query and normalized_query in search_text:
            score += 10

        if max_price is not None and float(product.get("price", 0)) > max_price:
            continue

        if score <= 0:
            continue

        results.append(
            {
                "name": product.get("name", ""),
                "brand": product.get("brand", ""),
                "category": product.get("category", ""),
                "price": product.get("price", 0),
                "currency": product.get("currency", "RUB"),
                "available": product.get("available", False),
                "url": product.get("url", ""),
                "score": score,
            }
        )

    results.sort(key=lambda item: (-item["score"], item["price"]))
    return results[: max(1, min(limit, 20))]
