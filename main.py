import asyncio
import json
import os
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.templating import Jinja2Templates

DATA_FILE             = os.getenv("DATA_FILE", "data.json")
DATABASE_URL          = os.getenv("DATABASE_URL")
SEMESTER              = os.getenv("SEMESTER", "2026.1")
BACKUP_TOKEN          = os.getenv("BACKUP_TOKEN")
BACKUP_PATH           = os.getenv("BACKUP_PATH")           # caminho do Railway Volume montado
BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
BACKUP_MAX_FILES      = int(os.getenv("BACKUP_MAX_FILES", "7"))

# Limite de tamanho do campo link (fix 5)
LINK_MAX_LEN = 2048

# --- Backup em volume ---

def salvar_backup_volume() -> Path | None:
    """Salva um snapshot dos links no Railway Volume. Retorna o caminho do arquivo criado,
    ou None se BACKUP_PATH não estiver configurado ou o banco não estiver disponível."""
    if not BACKUP_PATH or not DATABASE_URL:
        return None

    pasta = Path(BACKUP_PATH)
    pasta.mkdir(parents=True, exist_ok=True)

    dados = export_links_from_db()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    arquivo = pasta / f"backup_links_{timestamp}.json"
    arquivo.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    # Remove arquivos antigos, mantendo apenas os últimos BACKUP_MAX_FILES
    arquivos = sorted(pasta.glob("backup_links_*.json"))
    for antigo in arquivos[:-BACKUP_MAX_FILES]:
        antigo.unlink(missing_ok=True)

    return arquivo


async def _loop_backup_automatico() -> None:
    """Task em background: executa backup periódico no Railway Volume."""
    while True:
        await asyncio.sleep(BACKUP_INTERVAL_HOURS * 3600)
        try:
            arquivo = salvar_backup_volume()
            if arquivo:
                print(f"[backup] Snapshot salvo em {arquivo}")
        except Exception as e:
            print(f"[backup] Erro ao salvar snapshot: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicia a task de backup automático ao subir o servidor."""
    if BACKUP_PATH and DATABASE_URL:
        asyncio.create_task(_loop_backup_automatico())
        print(f"[backup] Task de backup iniciada — intervalo: {BACKUP_INTERVAL_HOURS}h, destino: {BACKUP_PATH}")
    yield


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

templates = Jinja2Templates(directory="templates")


# --- Helpers ---

def detect_platform(link: str) -> str:
    """Detecta a plataforma a partir da URL do link."""
    l = link.lower()
    if "chat.whatsapp.com" in l:
        return "whatsapp"
    if "t.me" in l or "telegram.me" in l:
        return "telegram"
    if "meet.google.com" in l:
        return "meet"
    if "teams.microsoft.com" in l or "teams.live.com" in l:
        return "teams"
    if "discord.gg" in l or "discord.com" in l:
        return "discord"
    return "outro"


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


def export_links_from_db() -> list[dict]:
    """Exporta todos os links do banco como lista de dicionários ordenada."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT materia, turma, link FROM links ORDER BY materia, turma")
            return [{"materia": r[0], "turma": r[1], "link": r[2]} for r in cur.fetchall()]


# --- Autenticação de backup ---

def _verificar_token(request: Request) -> None:
    """Valida o token Bearer do cabeçalho Authorization para os endpoints de backup."""
    if not BACKUP_TOKEN:
        raise HTTPException(status_code=503, detail="Backup não configurado: defina BACKUP_TOKEN")
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer ") or auth[7:] != BACKUP_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")


# --- Dados ---

def load_items() -> list[dict]:
    """Carrega turmas do data.json e mescla links do banco (se disponível)."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)
    items.sort(key=lambda x: (x["materia"], x["turma"]))

    # compatibilidade com data.json gerado antes do campo unidade existir
    for item in items:
        item.setdefault("unidade", "")

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


@app.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    # Links cadastrados com info de plataforma
    links_cadastrados = [
        {**i, "plataforma": detect_platform(i["link"])}
        for i in items if i.get("link")
    ]

    # Top 10 professores por número de turmas (A DEFINIR DOCENTE vai ao fim)
    prof_cnt = Counter(i["professor"] for i in items if i.get("professor"))
    a_definir_cnt = prof_cnt.pop("A DEFINIR DOCENTE", 0)
    top_professores = [
        {"nome": prof, "total": cnt}
        for prof, cnt in prof_cnt.most_common(10)
    ]
    if a_definir_cnt:
        top_professores.append({"nome": "A DEFINIR DOCENTE", "total": a_definir_cnt, "a_definir": True})

    # Contagem por plataforma
    plataforma_info = {
        "whatsapp": {"label": "WhatsApp",  "cor": "#25D366"},
        "telegram":  {"label": "Telegram",  "cor": "#229ED9"},
        "meet":      {"label": "Google Meet","cor": "#00897B"},
        "teams":     {"label": "Teams",     "cor": "#6264A7"},
        "discord":   {"label": "Discord",   "cor": "#5865F2"},
        "outro":     {"label": "Outro",     "cor": "#94a3b8"},
    }
    plat_cnt = Counter(l["plataforma"] for l in links_cadastrados)
    plataformas = [
        {**plataforma_info[p], "slug": p, "total": plat_cnt.get(p, 0)}
        for p in plataforma_info
        if plat_cnt.get(p, 0) > 0
    ]
    plataformas.sort(key=lambda x: x["total"], reverse=True)

    return templates.TemplateResponse("status.html", {
        "request": request,
        "semester": SEMESTER,
        "total_turmas": len(items),
        "links_cadastrados": links_cadastrados,
        "top_professores": top_professores,
        "plataformas": plataformas,
    })


@app.get("/sobre", response_class=HTMLResponse)
async def sobre(request: Request):
    return templates.TemplateResponse("sobre.html", {"request": request, "semester": SEMESTER})


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


# --- Rotas de backup ---

@app.get("/backup/links.json")
async def backup_export(request: Request):
    """Exporta todos os links do banco como arquivo JSON para download."""
    _verificar_token(request)
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="Banco de dados não configurado")
    dados = export_links_from_db()
    conteudo = json.dumps(dados, ensure_ascii=False, indent=2)
    return Response(
        content=conteudo,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=links_backup.json"},
    )


@app.post("/backup/restore")
async def backup_restore(request: Request):
    """Restaura links a partir de um JSON de backup. Faz upsert de cada entrada."""
    global items
    _verificar_token(request)

    # Valida o payload antes de acessar o banco
    try:
        dados: list = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    if not isinstance(dados, list):
        raise HTTPException(status_code=400, detail="Esperado array de objetos")

    campos_obrigatorios = {"materia", "turma", "link"}
    for i, entrada in enumerate(dados):
        if not isinstance(entrada, dict) or not campos_obrigatorios.issubset(entrada):
            raise HTTPException(status_code=400, detail=f"Entrada {i} inválida: campos obrigatórios: materia, turma, link")

    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="Banco de dados não configurado")

    # Insere ou atualiza cada link no banco
    for entrada in dados:
        save_link_to_db(entrada["materia"], entrada["turma"], entrada["link"])

    # Recarrega em memória para refletir os dados restaurados
    items = load_items()

    return JSONResponse(content={"ok": True, "restaurados": len(dados)})
