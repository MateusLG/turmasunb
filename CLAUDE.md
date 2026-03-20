# CLAUDE.md — TurmasUnB

## Regras de Trabalho

- **Sempre trabalhar na branch `dev`.** Nunca commitar direto na `main`. O usuário faz merge quando quiser.
- Ao identificar bugs ou melhorias, adicionar ao `sugestoes.md` e aguardar comando explícito para implementar.
- Comentários no código sempre em português (Brasil).
- Seguir as convenções de código descritas abaixo (Python tipado, FastAPI idiomático).
- Sempre analisar o prompt, ver o que é pedido e ao encontrar as alterações a serem feitas, mostrar resumo ao usuário e pedir permissão para fazer as alterações/implementações.
- **Toda alteração implementada deve ser registrada em `ALTERACOES.md`** imediatamente após a implementação, sem esperar solicitação do usuário.
- **Toda nova feature ou correção deve ter ao menos um teste** em `tests/test_main.py` cobrindo o comportamento implementado.
- **Sempre rodar todos os testes** (`python3 -m pytest tests/ -q` no venv) após qualquer alteração e confirmar que passam antes de commitar.

---

## Visão Geral

Plataforma web para consulta e gerenciamento de links de turmas da Universidade de Brasília, com dados extraídos do SIGAA. Substitui o projeto original `gruposfga` do Guilherme Puida (que se formou), expandindo o escopo da FGA para toda a UnB.

**Site:** turmasunb.com (domínio na Cloudflare, deploy no Railway)

**Stack:** Python 3.12, FastAPI, Jinja2, Tailwind CSS + DaisyUI (via CDN), Playwright (scraper), data.json (sem banco de dados).

**Estrutura do Repositório:**
```
turmasunb/
├── main.py                  — servidor FastAPI (rotas, leitura e edição de links)
├── scripts/
│   ├── scraper.py           — coleta turmas do SIGAA para todas as unidades da UnB
│   └── extractor.js         — script legado de console para extração manual no SIGAA
├── data.json                — dados das turmas (versionado no git, ~1.3MB)
├── requirements.txt         — dependências do servidor web
├── requirements-scraper.txt — dependências do scraper (playwright, httpx, bs4, lxml)
├── Procfile                 — comando de start para o Railway (uvicorn)
├── .python-version          — Python 3.12
├── CLAUDE.md                — este arquivo
├── ALTERACOES.md            — histórico de alterações implementadas
├── sugestoes.md             — sugestões e melhorias pendentes
└── templates/
    └── index.html           — template Jinja2 com Tailwind + DaisyUI
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

**Comportamento:** atualiza `items` em memória e persiste imediatamente em `data.json`. Não requer restart do servidor.

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
    "link": ""
  }
]
```

**Variável de ambiente:** `DATA_FILE` define o caminho do arquivo de dados (padrão: `"data.json"`).

---

## Dados

- **211 unidades** de ensino da UnB
- **6478 turmas** do semestre 2026.1
- Estrutura de cada turma: `{ materia, turma, professor, horario, link }`
- O campo `link` começa vazio e é editável pelo usuário na interface
- **Atualizar dados:** `python scripts/scraper.py --periodo 2026.1 --output data.json`
- O scraper preserva links já existentes ao re-executar (merge inteligente por `materia + turma`)
- O `data.json` gerado é commitado no repositório — o scraper roda só localmente

---

## Arquivos Principais — Notas Importantes

- **`main.py`** — Carrega `data.json` na inicialização, ordena por `materia + turma`. Rota POST atualiza link em memória e persiste em disco. Sem autenticação (MVP).
- **`scripts/scraper.py`** — Usa Playwright (Chromium headless) para iterar sobre os 211 departamentos do SIGAA. Deduplica por `(materia, turma)`. Preserva links ao sobrescrever arquivo existente.
- **`templates/index.html`** — SPA leve: busca client-side com debounce de 200ms, normalização de diacríticos, filtro por matéria/turma/professor/horário. Salva links via `fetch` (POST).
- **`scripts/extractor.js`** — Script de console para extração manual. Não é executado pelo servidor; apenas para uso pontual no navegador.

---

## Decisões Tomadas

- **Sem autenticação** — qualquer um pode editar links (MVP intencional)
- **Sem banco de dados** — `data.json` é suficiente para o volume atual
- **Scraper local** — não roda no Railway, só na máquina do desenvolvedor
- **Busca client-side** — os 6478 registros cabem em memória no browser sem paginação
- **Railway para deploy** — gratuito para o tráfego esperado
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

## Workflow de Sugestões

Ao identificar erros, bugs ou melhorias:

1. Adicionar ao `sugestoes.md` com: título, descrição, impacto, solução proposta, arquivos afetados.
2. Avisar o usuário.
3. Aguardar comando explícito para implementar.
4. Após implementar: remover do `sugestoes.md` e registrar em `ALTERACOES.md`.

---

## Lições Aprendidas

- O scraper pode falhar silenciosamente em departamentos com tabela vazia — o `try/except` por unidade evita interrupção total.
- `data.json` é carregado uma única vez na inicialização do FastAPI (`items` é variável global). Alterações via POST atualizam em memória e persistem em disco, mas um restart do servidor recarrega do disco.
- A busca client-side usa normalização de diacríticos (`normalize('NFD')`) — sempre aplicar nos dois lados (query e dado) para evitar falsos negativos com acentos.
- O Railway não tem acesso ao Playwright/Chromium — o scraper deve rodar localmente e o `data.json` resultante deve ser commitado.

---

## Roadmap (futuro, pós-MVP)

- Deploy estável no Railway com domínio apontado
- Autenticação para edição de links
- Expandir para outras universidades que usam SIGAA
- Potencial produto comercial para JRs de engenharia e outras instituições
