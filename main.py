import json
import os

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

DATA_FILE = os.getenv("DATA_FILE", "data.json")

app = FastAPI()
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
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
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


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
    return JSONResponse(content={"ok": True})


@app.get("/json")
async def get_json():
    return JSONResponse(content=items)
