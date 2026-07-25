import json

def search_products(q,max_price=None):
    data=json.load(open("zetzet_knowledge.json",encoding="utf-8"))
    res=[]
    for p in data["products"]:
        if q.lower() in p["search_text"]:
            if max_price and p["price"]>max_price:
                continue
            res.append({k:p[k] for k in ["name","brand","category","price","url"]})
        if len(res)>=10:
            break
    return res
