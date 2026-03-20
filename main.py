import json
import os

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
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


@app.get("/favicon.svg", include_in_schema=False)
async def favicon():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="7 -152 634 634">
  <rect x="7" y="-152" width="634" height="634" fill="#003F72"/>
  <path fill="white" opacity="0.95" d="m 543.63956,122.52025 c -31.99939,23.06828 -66.98325,43.06013 -104.68075,59.36796 -18.62882,8.05762 -38.70764,13.629 -59.85377,16.27428 -15.03676,1.87867 -30.34934,2.82421 -45.88061,2.82421 l 0,123.26981 308.17389,0 0,-272.32649 -97.75007,70.60017 -0.009,-0.01"/>
  <path fill="white" opacity="0.95" d="m 105.18666,122.52025 c 32.00957,23.06828 66.98846,43.06013 104.69093,59.36796 18.63255,8.05762 38.70143,13.629 59.8575,16.27428 15.02681,1.87867 30.3394,2.82421 45.88061,2.82421 l 0,123.26981 -308.1838357,0 0,-272.32649 97.7499457,70.60017 0.005,-0.01"/>
  <path fill="white" opacity="0.65" d="m 333.22443,7.27328 0,176.09972 c 14.78825,0 29.37894,-0.912 43.69132,-2.6838 l 0,0 c 19.4526,-2.43655 37.9112,-7.5569 55.04405,-14.96345 36.51712,-15.79343 70.37528,-35.14415 101.36575,-57.48929 l 0,0.005 108.07277,-78.05021 0,-22.91794 -308.17389,0"/>
  <path fill="white" opacity="0.65" d="m 315.6157,7.27328 0,176.09972 c -14.80316,0 -29.3777,-0.912 -43.69132,-2.6838 l -0.005,0 c -19.45757,-2.43655 -37.9199,-7.5569 -55.05275,-14.96345 -36.50842,-15.79343 -70.36658,-35.14415 -101.36625,-57.48929 l 0,0.005 -108.0685457,-78.05021 0,-22.91794 308.1838357,0"/>
</svg>"""
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/json")
async def get_json():
    return JSONResponse(content=items)
