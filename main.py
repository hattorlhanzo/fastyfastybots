from fastapi import FastAPI
from parser import parse_feed
from search import search_products

app=FastAPI(title="ZetZet AI API")

@app.get("/")
def home():
    return {"status":"ok","shop":"ZetZet.ru"}

@app.get("/update")
def update():
    return {"updated":True,"products":parse_feed()}

@app.get("/search")
def search(q:str,max_price:float=None):
    return search_products(q,max_price)
