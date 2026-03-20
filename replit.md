# TurmasUnB

Plataforma web para estudantes da UnB encontrarem e compartilharem links de reuniões online de turmas.

## Stack

- **Backend**: FastAPI + uvicorn (porta 5000)
- **Banco de dados**: PostgreSQL via `psycopg2` (persistência de links)
- **Rate limiting**: `slowapi` (proteção contra abuso)
- **Frontend**: HTML/CSS vanilla + Inter font (Google Fonts)
- **Templates**: Jinja2
- **Testes**: pytest (15 testes em `tests/test_main.py`)

## Estrutura

```
main.py               # App FastAPI principal (PostgreSQL + rate limiting)
data.json             # Dados das turmas (6.478 turmas)
templates/index.html  # UI principal (CSS vanilla, logo UnB SVG inline)
tests/                # Suite de testes pytest
requirements.txt      # Dependências de produção
requirements-dev.txt  # Dependências de desenvolvimento (pytest, httpx)
scraper.py            # Scraper para atualizar data.json
extractor.js          # Extrator auxiliar
```

## Paleta de cores

- Azul UnB: `#003F72`
- Azul médio: `#005299`
- Verde UnB: `#00A859`

## Configuração

- `DATABASE_URL`: string de conexão PostgreSQL (obrigatório em produção)
- `DATA_FILE`: caminho para o arquivo de dados (padrão: `data.json`)

## Rotas

- `GET /` — Interface principal (busca de turmas)
- `POST /` — Salvar link de uma turma
- `GET /json` — API JSON com todas as turmas

## Notas

- Logo UnB como SVG inline (paths reais do símbolo — Wikimedia Commons, domínio público)
- Links persistidos no PostgreSQL, com fallback para `data.json` quando sem banco
- Rate limiting aplicado ao POST `/` para evitar spam
- Campo `link` limitado a 2048 caracteres (segurança)
- Links existentes não são sobrescritos por string vazia (fix de segurança)
