import json
import os

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.templating import Jinja2Templates

DATA_FILE    = os.getenv("DATA_FILE", "data.json")
DATABASE_URL = os.getenv("DATABASE_URL")
SEMESTER     = os.getenv("SEMESTER", "2026.1")

# Limite de tamanho do campo link (fix 5)
LINK_MAX_LEN = 2048

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

templates = Jinja2Templates(directory="templates")


# --- Banco de dados ---

def get_conn():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """Cria a tabela de links se não existir."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    materia TEXT,
                    turma   TEXT,
                    link    TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (materia, turma)
                )
            """)
        conn.commit()


def load_links_from_db() -> dict[tuple, str]:
    """Retorna todos os links salvos como {(materia, turma): link}."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT materia, turma, link FROM links")
            return {(row[0], row[1]): row[2] for row in cur.fetchall()}


def save_link_to_db(materia: str, turma: str, link: str):
    """Insere ou atualiza o link de uma turma."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO links (materia, turma, link)
                VALUES (%s, %s, %s)
                ON CONFLICT (materia, turma) DO UPDATE SET link = EXCLUDED.link
            """, (materia, turma, link))
        conn.commit()


# --- Dados ---

def load_items() -> list[dict]:
    """Carrega turmas do data.json e mescla links do banco (se disponível)."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)
    items.sort(key=lambda x: (x["materia"], x["turma"]))

    if DATABASE_URL:
        links = load_links_from_db()
        for item in items:
            item["link"] = links.get((item["materia"], item["turma"]), "")

    return items


# --- Inicialização ---

if DATABASE_URL:
    init_db()

items: list[dict] = load_items()


# --- Rotas ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "semester": SEMESTER})


@app.post("/")
@limiter.limit("20/minute")  # fix 4: rate limiting por IP
async def update_link(
    request: Request,
    materia: str = Form(...),
    turma: str = Form(...),
    link: str = Form(...),
):
    # fix 5: limite de tamanho
    if len(link) > LINK_MAX_LEN:
        return JSONResponse(status_code=400, content={"ok": False, "erro": "Link muito longo"})

    # Rejeita link vazio ou sem protocolo http/https
    if not link or not (link.startswith("http://") or link.startswith("https://")):
        return JSONResponse(status_code=400, content={"ok": False, "erro": "Link inválido"})

    for item in items:
        if item["materia"] == materia and item["turma"] == turma:
            item["link"] = link
            if DATABASE_URL:
                save_link_to_db(materia, turma, link)
            break
    return JSONResponse(content={"ok": True})


@app.get("/json")
async def get_json():
    return JSONResponse(content=items)
