from fastapi import FastAPI
from parser import parse_feed

app = FastAPI(title="ZetZet AI Knowledge")

@app.get("/")
def home():
    return {"status": "ok", "shop": "ZetZet.ru"}

@app.get("/update")
def update():
    count = parse_feed()
    return {"updated": True, "products": count}
