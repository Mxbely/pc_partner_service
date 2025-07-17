from fastapi import Body, FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os
from search_service.parsers.base import Item
from search_service.parsers.pipline import start_pipline

app = FastAPI()

templates = Jinja2Templates(directory="/app/templates")
# print(f"Current dir {os.getcwd()}")

@app.get("/search", response_class=HTMLResponse, name="search")
def search(request: Request, query: str = ""):
    context = {"request": request, "query": query, "item_list": []}
    if query:
        print(f"Started query: {query}")
        filename = start_pipline(query)
        with open(filename, "r") as f:
            items = [Item(*line.strip().split(",")) for line in f.readlines()]
        context = {"request": request, "query": query, "item_list": items}
    return templates.TemplateResponse(request=request, name="search_list.html", context=context)
