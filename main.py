from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse

from ai_search import ai_search
from parser import JSON_PATH, TEXT_PATH, parse_feed

app = FastAPI(title="ZetZet FastBots Knowledge API")


@app.get("/")
def home():
    return {
        "status": "ok",
        "shop": "ZetZet.ru",
        "endpoints": {
            "update": "/update",
            "knowledge_text": "/knowledge.txt",
            "knowledge_json": "/knowledge",
            "search": "/ai-search?query=Roborock",
        },
    }


@app.get("/update")
def update():
    count = parse_feed()
    return {"updated": True, "products": count}


@app.get("/knowledge.txt", response_class=PlainTextResponse)
def knowledge_text():
    path = Path(TEXT_PATH)
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="База еще не создана. Сначала откройте /update.",
        )
    return path.read_text(encoding="utf-8")


@app.get("/knowledge")
def knowledge_json():
    path = Path(JSON_PATH)
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="База еще не создана. Сначала откройте /update.",
        )
    return FileResponse(
        path,
        media_type="application/json",
        filename="zetzet_knowledge.json",
    )


@app.get("/download/knowledge.txt")
def download_knowledge_text():
    path = Path(TEXT_PATH)
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="База еще не создана. Сначала откройте /update.",
        )
    return FileResponse(
        path,
        media_type="text/plain; charset=utf-8",
        filename="zetzet_knowledge.txt",
    )


@app.get("/ai-search")
def search(
    query: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=20),
):
    return {
        "query": query,
        "products": ai_search(query=query, limit=limit),
    }
