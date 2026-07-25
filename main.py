import html
import math
from urllib.parse import urljoin

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from ai_search import ai_search
from parser import load_data, parse_feed

app = FastAPI(title="ZetZet FastBots Knowledge API v6")

PRODUCTS_PER_PAGE = 50


@app.get("/")
def home(request: Request):
    base = str(request.base_url)
    return {
        "status": "ok",
        "shop": "ZetZet.ru",
        "fastbots_source": urljoin(base, "fastbots/"),
        "sitemap": urljoin(base, "sitemap.xml"),
        "update": urljoin(base, "update"),
    }


@app.get("/update")
def update():
    return {"updated": True, "products": parse_feed()}


@app.get("/ai-search")
def search(
    query: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=20),
):
    return {"query": query, "products": ai_search(query, limit)}


@app.get("/fastbots/", response_class=HTMLResponse)
def fastbots_index(request: Request):
    data = load_data()
    count = len(data.get("products", []))
    pages = math.ceil(count / PRODUCTS_PER_PAGE)
    base = str(request.base_url)

    links = "\n".join(
        f'<li><a href="{html.escape(urljoin(base, f"fastbots/page/{page}"))}">'
        f'Каталог ZetZet — страница {page} из {pages}</a></li>'
        for page in range(1, pages + 1)
    )

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>База товаров ZetZet.ru</title>
  <meta name="description" content="Актуальная база товаров интернет-магазина ZetZet.ru">
</head>
<body>
  <main>
    <h1>База товаров интернет-магазина ZetZet.ru</h1>
    <p>Обновлено: {html.escape(data.get("updated", ""))}</p>
    <p>Количество товаров: {count}</p>
    <p>Используйте цены, наличие, характеристики и ссылки только из этой базы.</p>
    <ul>{links}</ul>
  </main>
</body>
</html>"""


@app.get("/fastbots/page/{page}", response_class=HTMLResponse)
def fastbots_page(page: int, request: Request):
    data = load_data()
    products = data.get("products", [])
    pages = max(1, math.ceil(len(products) / PRODUCTS_PER_PAGE))

    if page < 1 or page > pages:
        return HTMLResponse("<h1>Страница не найдена</h1>", status_code=404)

    start = (page - 1) * PRODUCTS_PER_PAGE
    end = start + PRODUCTS_PER_PAGE
    selected = products[start:end]
    base = str(request.base_url)

    articles = []

    for product in selected:
        availability = "В наличии" if product.get("available") else "Нет в наличии"
        articles.append(
            f"""
<article>
  <h2>{html.escape(product.get("name", ""))}</h2>
  <p><strong>Бренд:</strong> {html.escape(product.get("brand") or "Не указан")}</p>
  <p><strong>Категория:</strong> {html.escape(product.get("category") or "Не указана")}</p>
  <p><strong>Цена:</strong> {product.get("price", 0):.0f} {html.escape(product.get("currency", "RUB"))}</p>
  <p><strong>Наличие:</strong> {availability}</p>
  <p><strong>Ссылка:</strong> <a href="{html.escape(product.get("url", ""))}">{html.escape(product.get("url", ""))}</a></p>
  <p><strong>Описание:</strong> {html.escape(product.get("description") or "Описание отсутствует")}</p>
</article>
<hr>
"""
        )

    previous_link = (
        f'<a href="{html.escape(urljoin(base, f"fastbots/page/{page - 1}"))}">Предыдущая</a>'
        if page > 1 else ""
    )
    next_link = (
        f'<a href="{html.escape(urljoin(base, f"fastbots/page/{page + 1}"))}">Следующая</a>'
        if page < pages else ""
    )

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <title>Каталог ZetZet — страница {page}</title>
</head>
<body>
  <main>
    <nav>
      <a href="{html.escape(urljoin(base, "fastbots/"))}">Оглавление</a>
      {previous_link} {next_link}
    </nav>
    <h1>Товары ZetZet.ru — страница {page} из {pages}</h1>
    {''.join(articles)}
  </main>
</body>
</html>"""


@app.get("/sitemap.xml")
def sitemap(request: Request):
    data = load_data()
    pages = math.ceil(len(data.get("products", [])) / PRODUCTS_PER_PAGE)
    base = str(request.base_url)

    urls = [urljoin(base, "fastbots/")]
    urls.extend(
        urljoin(base, f"fastbots/page/{page}")
        for page in range(1, pages + 1)
    )

    xml_urls = "".join(
        f"<url><loc>{html.escape(url)}</loc></url>"
        for url in urls
    )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{xml_urls}</urlset>"
    )

    return Response(content=xml, media_type="application/xml")


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots(request: Request):
    return (
        "User-agent: *\n"
        "Allow: /fastbots/\n"
        f"Sitemap: {urljoin(str(request.base_url), 'sitemap.xml')}\n"
    )
