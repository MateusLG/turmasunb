import json
import os
from typing import Optional

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

DATA_FILE = os.getenv("DATA_FILE", "data.json")

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def load_items() -> list[dict]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)
    items.sort(key=lambda x: (x["materia"], x["turma"]))
    return items


def save_items(items: list[dict]):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


items: list[dict] = load_items()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, q: Optional[str] = None):
    filtered = items
    if q:
        query = q.lower()
        filtered = [
            item for item in items
            if query in item["materia"].lower()
            or query in item["turma"].lower()
            or query in item["professor"].lower()
            or query in item["horario"].lower()
            or query in item["link"].lower()
        ]
    return templates.TemplateResponse("index.html", {"request": request, "items": filtered, "q": q or ""})


@app.post("/")
async def update_link(
    materia: str = Form(...),
    turma: str = Form(...),
    link: str = Form(...),
):
    for item in items:
        if item["materia"] == materia and item["turma"] == turma:
            item["link"] = link
            save_items(items)
            break
    return RedirectResponse(url="/", status_code=302)


@app.get("/json")
async def get_json():
    return JSONResponse(content=items)
