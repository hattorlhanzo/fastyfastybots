import json

def ai_search(query):
    with open("zetzet_knowledge.json",encoding="utf-8") as f:
        data=json.load(f)

    q=query.lower()
    result=[]

    for p in data["products"]:
        if any(word in p["search_text"] for word in q.split()):
            result.append({
                "name":p["name"],
                "brand":p["brand"],
                "category":p["category"],
                "price":p["price"],
                "url":p["url"]
            })

        if len(result)>=5:
            break

    return result
