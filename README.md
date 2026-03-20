# TurmasUnB

Acesse em: **[turmasunb.com](https://turmasunb.com)**

Plataforma para consulta e gerenciamento de links de turmas da Universidade de Brasília (UnB), com dados extraídos diretamente do SIGAA.

Inspirado no antigo **Turmas FGA** (que atendia apenas a Faculdade do Gama), o TurmasUnB expande o conceito para todos os campi e cursos da UnB.

## O que é

Todo semestre, alunos da UnB precisam reunir links de aula (Google Meet, Teams, WhatsApp etc.) espalhados em grupos e e-mails. O TurmasUnB centraliza isso: qualquer aluno pode buscar sua turma e adicionar ou atualizar o link — que fica salvo para todos.

## Funcionalidades

- Busca em tempo real por matéria, professor, horário ou código da turma
- Horários exibidos em formato legível (ex: `Seg, Qua, Sex 08:00–10:00`)
- Adição e edição de links por qualquer aluno, sem cadastro
- Links persistidos em banco de dados (sobrevivem a atualizações do site)
- API pública em `/json` com todos os dados

## Dados

- **211 unidades** de ensino da UnB
- **6478 turmas** do semestre 2026.1
- Coletados via scraper no SIGAA público

## Stack

- **Backend:** Python 3.12 + FastAPI
- **Frontend:** HTML + CSS + JavaScript vanilla
- **Banco de dados:** PostgreSQL (Railway)
- **Scraper:** Playwright (coleta dados do SIGAA localmente)
- **Deploy:** Railway + Cloudflare

## Rodando localmente

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

> Sem a variável `DATABASE_URL`, o app funciona normalmente usando `data.json` para armazenar links.

Para atualizar os dados do SIGAA:

```bash
pip install -r requirements-scraper.txt
playwright install chromium
python scraper.py --periodo 2026.1
```

## Licença

MIT
