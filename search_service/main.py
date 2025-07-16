from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

app = FastAPI()

templates = Jinja2Templates(directory="/app/templates")
print(f"Current dir {os.getcwd()}")

@app.get("/", response_class=HTMLResponse)
def search(request: Request, query: str = ""):
    return templates.TemplateResponse(request=request, name="search_list.html", context={"request": request, "query": query})
