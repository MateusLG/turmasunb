# CLAUDE.md — TurmasUnB

## Regras de Trabalho

- **Sempre trabalhar na branch `dev`.** Nunca commitar direto na `main`. O usuário faz merge quando quiser.
- Comentários no código sempre em português (Brasil).
- Seguir as convenções de código descritas abaixo (Python tipado, FastAPI idiomático).
- Sempre analisar o prompt, ver o que é pedido e ao encontrar as alterações a serem feitas, mostrar resumo ao usuário e pedir permissão para fazer as alterações/implementações.
- **Toda alteração implementada deve ser registrada em `ALTERACOES.md`** imediatamente após a implementação, sem esperar solicitação do usuário.
- **Toda nova feature ou correção deve ter ao menos um teste** em `tests/test_main.py` cobrindo o comportamento implementado.
- **Sempre rodar todos os testes** (`venv/bin/python -m pytest tests/ -q`) após qualquer alteração e confirmar que passam antes de commitar.

---

## Visão Geral

Plataforma web para consulta e gerenciamento de links de turmas da Universidade de Brasília, com dados extraídos do SIGAA. Substitui o projeto original `gruposfga` do Guilherme Puida (que se formou), expandindo o escopo da FGA para toda a UnB.

**Site:** turmasunb.com (domínio na Cloudflare, deploy no Railway)

**Stack:** Python 3.12, FastAPI, Jinja2, Tailwind CSS + DaisyUI (via CDN), Playwright (scraper), PostgreSQL (links dos usuários), data.json (estrutura das turmas).

**Estrutura do Repositório:**
```
turmasunb/
├── main.py                  — servidor FastAPI (rotas, leitura e edição de links)
├── scripts/
│   ├── scraper.py           — coleta turmas do SIGAA para todas as unidades da UnB
│   └── extractor.js         — script legado de console para extração manual no SIGAA
├── data.json                — dados das turmas (versionado no git, ~1.3MB)
├── requirements.txt         — dependências do servidor web
├── requirements-dev.txt     — dependências de desenvolvimento (pytest, httpx)
├── requirements-scraper.txt — dependências do scraper (playwright, httpx, bs4, lxml)
├── Procfile                 — comando de start para o Railway (uvicorn)
├── .python-version          — Python 3.12
├── CLAUDE.md                — este arquivo
├── ALTERACOES.md            — histórico de alterações implementadas
└── templates/
    ├── index.html           — template principal (Jinja2 + Tailwind + DaisyUI)
    ├── sobre.html           — página sobre o projeto e créditos
    └── status.html          — página de estatísticas (links, plataformas, professores)
```

---

## Endpoints

### `GET /`
Retorna a página HTML principal. A busca é feita inteiramente no client-side: o frontend chama `/json` e filtra os resultados no browser.

---

### `POST /`
Atualiza o link de uma turma.

**Body:** `multipart/form-data`

| Campo    | Tipo   | Descrição                                      |
|----------|--------|------------------------------------------------|
| `materia`| string | Nome completo da matéria (chave de busca)      |
| `turma`  | string | Código da turma (chave de busca)               |
| `link`   | string | URL do grupo/sala a salvar                     |

**Resposta:** `{"ok": true}` — sempre, mesmo que `materia+turma` não exista (falha silenciosa).

**Comportamento:** atualiza `items` em memória, persiste no PostgreSQL (se `DATABASE_URL` configurado). Rate limit: 20 req/min por IP. Rejeita links vazios, sem protocolo http/https ou com mais de 2048 caracteres.

---

### `GET /json`
Retorna o array completo de turmas em JSON, ordenado por `materia + turma`.

**Resposta:** array de objetos:
```json
[
  {
    "materia": "ALGORITMOS E PROGRAMAÇÃO DE COMPUTADORES",
    "turma": "01",
    "professor": "NOME DO PROFESSOR",
    "horario": "246M34",
    "unidade": "DEPARTAMENTO DE CIÊNCIA DA COMPUTAÇÃO",
    "link": ""
  }
]
```

---

### `GET /status`
Página de estatísticas: links cadastrados, distribuição por plataforma, top professores por número de turmas.

---

### `GET /sobre`
Página sobre o projeto, história e créditos.

---

### `GET /backup/links.json`
Exporta todos os links do banco como arquivo JSON para download.

**Auth:** `Authorization: Bearer <BACKUP_TOKEN>`

**Resposta:** arquivo JSON com array de `{materia, turma, link}` — ou `401`/`503`.

---

### `POST /backup/restore`
Restaura links a partir de um JSON de backup (upsert no banco + recarrega memória).

**Auth:** `Authorization: Bearer <BACKUP_TOKEN>`

**Body:** `application/json` — array de `{materia, turma, link}`

**Resposta:** `{"ok": true, "restaurados": N}` — ou `400`/`401`/`503`.

---

## Dados

- **211 unidades** de ensino da UnB
- **6478 turmas** do semestre 2026.1
- Estrutura de cada turma: `{ materia, turma, professor, horario, unidade, link }`
- O campo `link` começa vazio e é editável pelo usuário na interface
- **Atualizar dados:** `python scripts/scraper.py --periodo 2026.1 --output data.json`
- O scraper preserva links já existentes ao re-executar (merge inteligente por `materia + turma`)
- O `data.json` gerado é commitado no repositório — o scraper roda só localmente

---

## Arquivos Principais — Notas Importantes

- **`main.py`** — Carrega `data.json` na inicialização, ordena por `materia + turma`. Links persistidos no PostgreSQL. Backup automático em volume via lifespan + task asyncio. Endpoints de export/restore protegidos por token.
- **`scripts/scraper.py`** — Usa Playwright (Chromium headless) para iterar sobre os 211 departamentos do SIGAA. Deduplica por `(materia, turma)`. Preserva links ao sobrescrever arquivo existente.
- **`templates/index.html`** — SPA leve: busca client-side com debounce de 200ms, normalização de diacríticos, filtro por matéria/turma/professor/horário. Salva links via `fetch` (POST).
- **`templates/status.html`** — Estatísticas: links cadastrados por plataforma (WhatsApp, Telegram, Meet, Teams, Discord), top 10 professores.
- **`scripts/extractor.js`** — Script de console para extração manual. Não é executado pelo servidor; apenas para uso pontual no navegador.

---

## Infraestrutura

- **Plano:** Railway Hobby
- **Deploy:** Railway (web service via Procfile: `uvicorn main:app --host 0.0.0.0 --port $PORT`)
- **Banco:** Railway PostgreSQL (tabela `links` com `materia + turma` como chave primária)
- **Backup:** Railway Volume montado em `BACKUP_PATH` — snapshots JSON automáticos a cada `BACKUP_INTERVAL_HOURS` horas
- **Domínio:** turmasunb.com (Cloudflare, ~$10/ano)

### Configurar Railway Volume para backup
1. No dashboard do Railway: **New** → **Volume**, montar no serviço web em `/data`
2. Setar as env vars abaixo no serviço web

---

## Variáveis de Ambiente

| Variável               | Padrão       | Descrição                                              |
|------------------------|--------------|--------------------------------------------------------|
| `DATA_FILE`            | `data.json`  | Caminho do arquivo de turmas                           |
| `DATABASE_URL`         | —            | URL de conexão PostgreSQL (Railway injeta automaticamente) |
| `SEMESTER`             | `2026.1`     | Semestre atual (exibido na UI)                         |
| `BACKUP_TOKEN`         | —            | Token Bearer para os endpoints `/backup/*`             |
| `BACKUP_PATH`          | —            | Caminho do Railway Volume para snapshots (ex: `/data/backups`) |
| `BACKUP_INTERVAL_HOURS`| `24`         | Intervalo entre snapshots automáticos (em horas)       |
| `BACKUP_MAX_FILES`     | `7`          | Quantidade máxima de arquivos de backup a manter       |

---

## Decisões Tomadas

- **Sem autenticação para edição** — qualquer um pode editar links (MVP intencional)
- **PostgreSQL para links** — tabela `links` no Railway; `data.json` guarda só a estrutura das turmas (versionado no git)
- **Backup em Volume** — snapshots JSON no Railway Volume evitam perda dos links por falha do banco
- **Scraper local** — não roda no Railway, só na máquina do desenvolvedor
- **Busca client-side** — os 6478 registros cabem em memória no browser sem paginação
- **Domínio `.com`** — comprado na Cloudflare (~$10/ano), mais adequado para escalar além da UnB

---

## Padrões de Código

**Python:**
- Type hints obrigatórios em funções (`def load_items() -> list[dict]`)
- `async/await` para rotas FastAPI e para o scraper (Playwright async API)
- Comentários em português
- Sem dependências desnecessárias — manter `requirements.txt` enxuto

**HTML/CSS/JS:**
- Tailwind + DaisyUI via CDN (sem build step)
- JavaScript vanilla — sem frameworks no frontend
- Busca e interações via `fetch` e manipulação direta do DOM

**Convenção de commits** (conventional commits em português):
- `feat(escopo): descrição`
- `fix(escopo): descrição`
- `docs(escopo): descrição`
- `refactor(escopo): descrição`
- `chore(escopo): descrição`

---

## Workflow de Alterações

Toda alteração vai para `ALTERACOES.md` no formato:

```
## [AAAA-MM-DD] Título curto
Descrição em 2–4 linhas do que mudou e por quê.
Pendências apenas quando há ação externa necessária (ex: configuração no Railway).
```

---

## Lições Aprendidas

- O scraper pode falhar silenciosamente em departamentos com tabela vazia — o `try/except` por unidade evita interrupção total.
- `data.json` é carregado uma única vez na inicialização do FastAPI (`items` é variável global). Links vêm do PostgreSQL e são mesclados em memória na inicialização.
- A busca client-side usa normalização de diacríticos (`normalize('NFD')`) — sempre aplicar nos dois lados (query e dado) para evitar falsos negativos com acentos.
- O Railway não tem acesso ao Playwright/Chromium — o scraper deve rodar localmente e o `data.json` resultante deve ser commitado.
- O filesystem do Railway é efêmero entre redeploys — usar Railway Volume para qualquer dado que precise persistir além do banco.
- O `lifespan` do FastAPI é o lugar correto para iniciar tasks `asyncio` em background (substituiu `@app.on_event("startup")`, que foi depreciado).

---

## Roadmap (futuro, pós-MVP)

- Autenticação para edição de links
- Expandir para outras universidades que usam SIGAA
- Potencial produto comercial para JRs de engenharia e outras instituições
