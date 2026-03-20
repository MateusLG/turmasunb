# TurmasUnB — Contexto para o Claude

## O projeto

Plataforma web para consulta e gerenciamento de links de turmas da UnB (Universidade de Brasília), com dados extraídos do SIGAA. Substitui o projeto original `gruposfga` do Guilherme Puida (que se formou), expandindo o escopo de FGA para toda a UnB.

Site: **turmasunb.com** (domínio na Cloudflare, deploy no Railway)

## Stack

- **Backend:** Python 3.12 + FastAPI + Jinja2
- **Frontend:** Tailwind CSS + DaisyUI (via CDN)
- **Scraper:** Playwright (Chromium headless) — coleta dados do SIGAA
- **Armazenamento:** `data.json` local (sem banco de dados por enquanto)
- **Deploy:** Railway (`Procfile` com uvicorn)

## Estrutura

```
turmasunb/
├── main.py                  — servidor FastAPI (rotas, busca, edição de links)
├── scraper.py               — coleta turmas do SIGAA para todas as unidades da UnB
├── extractor.js             — script alternativo de console para o SIGAA (legado)
├── data.json                — dados das turmas (versionado no git)
├── requirements.txt         — deps do servidor web
├── requirements-scraper.txt — deps do scraper (playwright, httpx, bs4, lxml)
├── Procfile                 — comando de start para o Railway
├── .python-version          — Python 3.12
└── templates/
    └── index.html           — template Jinja2 com Tailwind + DaisyUI
```

## Endpoints

| Método | Rota     | Descrição                          |
|--------|----------|------------------------------------|
| GET    | `/?q=`   | Página principal com busca         |
| POST   | `/`      | Atualiza link de uma turma         |
| GET    | `/json`  | Retorna todos os dados em JSON     |

## Dados

- **211 unidades** de ensino da UnB
- **6478 turmas** do semestre 2026.1
- Scraper roda localmente e o `data.json` gerado é commitado no repositório
- Atualizar dados: `python scraper.py --periodo 2026.1 --output data.json`

## Decisões tomadas

- **Sem autenticação** — qualquer um pode editar links (MVP)
- **Sem banco de dados** — `data.json` é suficiente para o MVP
- **Scraper local** — não roda no Railway, só localmente
- **Railway para deploy** — gratuito para o tráfego esperado
- **domínio `.com`** — comprado na Cloudflare (~$10/ano), mais adequado para escalar além da UnB

## Convenção de commits

Usar o padrão conventional commits em português:
- `feat(escopo): descrição`
- `fix(escopo): descrição`
- `docs(escopo): descrição`
- `refactor(escopo): descrição`
- `chore(escopo): descrição`

## Roadmap (futuro, pós-MVP)

- Deploy completo no Railway com domínio apontado
- Expandir para outras universidades que usam SIGAA
- Potencial produto comercial para JRs de engenharia e outras universidades
