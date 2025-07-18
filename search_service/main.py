import os

from fastapi import Body, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from search_service.parsers.base import Item
from search_service.parsers.pipline import start_pipline

app = FastAPI()

templates = Jinja2Templates(directory="/app/templates")


@app.get("/", response_class=HTMLResponse, name="index")
def redirect(request: Request):
    return RedirectResponse(url="/search")


@app.get("/search", response_class=HTMLResponse, name="search")
def search(request: Request, query: str = ""):
    context = {"request": request, "query": query, "item_list": []}
    if query:
        print(f"Started query: {query}")
        filename = start_pipline(query)
        with open(filename, "r") as f:
            items = [Item(*line.strip().split(",")) for line in f.readlines()]
        context = {
            "request": request,
            "query": query,
            "item_list": items,
            "total_items": len(items),
        }
    return templates.TemplateResponse(
        request=request, name="search_list.html", context=context
    )
