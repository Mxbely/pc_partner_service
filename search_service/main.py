import os
from search_service.parsers.pipline import filters

from fastapi import Body, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dataclasses import asdict
from search_service.parsers.base import Item
from search_service.parsers.pipline import start_pipline

app = FastAPI()

templates = Jinja2Templates(directory="/app/templates")


@app.get("/", response_class=HTMLResponse, name="index")
def redirect(request: Request):
    return RedirectResponse(url="/search")


@app.get("/search", response_class=HTMLResponse, name="search_get")
def search_get(request: Request):
    context = {"request": request, "filter_list": [filter for filter in filters.keys()]}
    return templates.TemplateResponse(
        request=request, name="search_list.html", 
        context=context
    )

class SearchData(BaseModel):
    query: str
    filters: list[str] = []
    

@app.post("/search", response_class=HTMLResponse, name="search_post")
def search_post(request: Request, data: SearchData = Body(...)):
    if data.query:
        print(f"Started query: {data.query}")
        parsers = []
        for filter_name in data.filters:
            if filter_name in filters:
                parsers.append(filters[filter_name](data.query))
        filename = start_pipline(data.query, parsers)
        with open(filename, "r") as f:
            items = []
            for line in f.readlines():
                lines = line.strip().split(",")
                item = Item(
                    src=lines[0],
                    category=lines[1],
                    name=lines[2],
                    price=float(lines[3]),
                    url=",".join(lines[4:-1]),
                    status=lines[-1],
                )
                items.append(item)
        context = {
            "request": request,
            "query": data.query,
            "items": items,
            "total_items": len(items),
        }

    return JSONResponse(
        status_code=200,
        content={
            "query": data.query,
            "items": [asdict(item) for item in context["items"]],
            "total_items": len(context["items"]),
        }
    )
