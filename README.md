# TurmasUnB

Acesse em: **[turmasunb.com](https://turmasunb.com)**

Plataforma para consulta e gerenciamento de links de turmas da Universidade de Brasília (UnB), com dados extraídos diretamente do SIGAA.

## O que é

Alunos da UnB precisam todo semestre reunir links de aula (Google Meet, Teams, etc.) espalhados em grupos de WhatsApp e e-mails. O TurmasUnB centraliza isso: qualquer aluno pode buscar sua turma e adicionar ou atualizar o link.

## Dados

- **211 unidades** de ensino da UnB
- **6478 turmas** do semestre 2026.1
- Atualizado via scraper no SIGAA público

## Funcionalidades

- Busca por matéria, professor, horário ou código da turma
- Adição e edição de links de reunião por qualquer aluno
- API pública em `/json` com todos os dados

## Stack

- **Backend:** Python + FastAPI
- **Frontend:** Tailwind CSS + DaisyUI
- **Scraper:** Playwright (coleta dados do SIGAA)

## Rodando localmente

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Para atualizar os dados:

```bash
pip install -r requirements-scraper.txt
playwright install chromium
python scraper.py --periodo 2026.1
```

## Licença

MIT
