from fastapi import FastAPI
from parser import parse_feed
from ai_search import ai_search

app=FastAPI(title="ZetZet AI Seller API")


@app.get("/")
def home():
    return {
        "status":"ok",
        "shop":"ZetZet.ru"
    }


@app.get("/update")
def update():
    return {
        "updated":True,
        "products":parse_feed()
    }


@app.get("/ai-search")
def search(query:str):
    return {
        "products":ai_search(query)
    }
