import json
import re

def ai_search(query, limit=5):

    with open("zetzet_knowledge.json",encoding="utf-8") as f:
        data=json.load(f)

    q=query.lower()

    price=None
    numbers=re.findall(r'\d+',q)

    for n in numbers:
        if int(n)>10000:
            price=int(n)

    results=[]

    for p in data["products"]:

        score=0

        if q in p["search_text"]:
            score+=10

        for word in q.split():
            if word in p["search_text"]:
                score+=1

        if score>0:

            if price and p["price"]>price:
                continue

            results.append({
                "name":p["name"],
                "brand":p["brand"],
                "category":p["category"],
                "price":p["price"],
                "url":p["url"],
                "score":score
            })

    results.sort(key=lambda x:x["score"], reverse=True)

    return results[:limit]
