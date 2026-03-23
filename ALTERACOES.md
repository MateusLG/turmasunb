# Histórico de Alterações

## [2026-03-23] Redesign completo da página /sobre
Página simplificada: seção "Como surgiu" reescrita em 2 frases diretas; seção "Como funciona e quem fez" removida. Três cards interativos lado a lado (foto, nome, descrição, botões de link) com animação de elevação no hover substituem os antigos cartões de crédito inline.

## [2026-03-23] Redesign dos cartões de crédito na página /sobre
Cartões de Mateus, Pedro e Guilherme atualizados com foto real (GitHub Avatars), nome, descrição e botão de link individual (Mateus → LinkedIn, Pedro → GitHub, Guilherme → GitHub). Removidas as iniciais e os links inline de texto.

## [2026-03-23] Renomear aba Stats para Status
Rota `/stats` renomeada para `/status` em todo o projeto: `main.py` (rota e função), `templates/status.html` (renomeado de `stats.html`), links na navbar de `index.html`, `sobre.html` e `status.html`, e testes em `test_main.py`. Arquivo `stats.html` removido.

## [2026-03-23] Correção de responsividade (issue #1)
Corrigidos dois problemas reportados em viewport mobile: (1) texto de matéria/professor não quebrava linha corretamente em cards — adicionado `min-width: 0; flex: 1` no `.card-info` e `overflow-wrap: break-word` nos campos de texto; (2) navbar com `height` fixo de 56px extravasava em telas estreitas — trocado por `min-height` com `flex-wrap: wrap` para acomodar os links em múltiplas linhas. Adicionado também `flex-wrap: wrap` nas ações do card.

## [2026-03-20] Redesign de /stats e nova rota /sobre
/stats reformulado com 3 cards: links cadastrados com ícone por plataforma (WhatsApp, Telegram, Meet, Teams, Discord), top 10 professores com mais turmas e distribuição por plataforma. Nova rota /sobre com história do projeto (origem no gruposfga do Guilherme Puida), stack técnico, créditos e CTA para contribuição. Link /sobre adicionado no footer de todas as páginas. conftest.py adicionado para isolar testes do banco de dados local.

## [2026-03-20] Página de stats (/stats)
Nova rota GET /stats com template próprio. Exibe: cards de resumo (total de turmas, com link, sem link, % cobertura), barra de progresso geral, top 10 unidades por total de turmas (com indicador de links preenchidos em verde — ativado após re-run do scraper), top 10 matérias com mais turmas e gráfico de barras por dia da semana (parseado do campo horario). Link "Stats" adicionado no footer de index.html. 4 testes adicionados.

## [2026-03-20] Campo unidade no scraper e backend
O scraper agora salva o nome da unidade/departamento em cada turma (`"unidade": "DEPARTAMENTO DE MATEMÁTICA"`). `parse_turmas` e `scrape_unidade` recebem o `label` do departamento já disponível no loop principal. `load_items` no backend adiciona `setdefault("unidade", "")` para compatibilidade com o `data.json` atual (gerado antes dessa mudança). A busca no frontend também passa a filtrar por `unidade`. Requer re-execução do scraper para popular o campo nos dados.

## [2026-03-20] Reorganização da estrutura de arquivos
Movido `scraper.py` e `extractor.js` para `scripts/`. Removidos `attached_assets/` e `replit.md` (lixo do Replit). Adicionado `.replit` ao `.gitignore`. Atualizado `CLAUDE.md` com os novos caminhos.

## [2026-03-20] Melhorias de UX, segurança e manutenção
1. **Confirmação ao substituir link existente**: frontend exibe `confirm()` antes de sobrescrever.
2. **Tratamento de erro no fetch**: frontend agora verifica `res.ok` e exibe mensagem de erro do backend em vez de mostrar "✓ Salvo!" incondicionalmente.
3. **Paginação de resultados**: busca renderiza no máximo 30 cards por vez; botão "Ver mais N turmas" carrega o próximo lote.
4. **Contador dinâmico de turmas**: total exibido no estado vazio é calculado do `/json` em vez de hardcoded.
5. **Semestre configurável**: variável de ambiente `SEMESTER` (padrão `2026.1`) controla o título da página e a navbar. Sem mais hardcode.
6. **Meta tags Open Graph**: adicionadas tags `og:title`, `og:description`, `og:type` e `og:url` para preview no WhatsApp/Telegram.

## [2026-03-20] Bloquear envio de link vazio
POST / agora rejeita link vazio em qualquer situação (400). Frontend também bloqueia o botão Salvar se o campo estiver vazio. Evita registros sem link no banco e cliques acidentais.

## [2026-03-20] Proteção contra sobrescrita de link com string vazia
POST / agora retorna 400 se o usuário tentar salvar um link vazio em uma turma que já possui link cadastrado. Evita que cliques acidentais no botão de salvar apaguem links existentes.

## [2026-03-20] Testes automatizados
Adicionados 15 testes com pytest cobrindo GET /, GET /json e POST /. Inclui testes de validação de URL (javascript:, ftp:, sem protocolo, tamanho), ordenação dos dados, estrutura dos itens e persistência em memória. Dependências de dev em requirements-dev.txt.

## [2026-03-20] Correções de segurança (5 brechas)
1. XSS: validação no frontend bloqueia esquemas javascript: antes de setar href.
2. Tab-napping: adicionado rel="noopener noreferrer" no botão Entrar.
3. Validação de URL no backend: POST / rejeita links que não começam com http/https.
4. Rate limiting: slowapi limita POST / a 20 requisições/minuto por IP.
5. Limite de tamanho: campo link limitado a 2048 caracteres no frontend (maxlength) e backend.

## [2026-03-20] Persistência de links no PostgreSQL
Links salvos pelos usuários agora são armazenados no PostgreSQL (Railway) em vez do data.json. O banco é inicializado automaticamente na subida da aplicação. Sem DATABASE_URL definida, o comportamento cai de volta para o arquivo (desenvolvimento local). O data.json continua no git apenas com os dados de turmas (sem links).

## [2026-03-20] Criação do Visual.md com identidade visual da UnB
Pesquisado e documentado o sistema de identidade visual oficial da UnB: cores institucionais (Azul #003366 e Verde #006633), símbolo criado por Aloísio Magalhães em 1963, tipografias UnB Pro e UnB Office, história da instituição e diretrizes para aplicação no frontend do TurmasUnB.

## [2026-03-20] Símbolo da UnB e crédito do autor no frontend
Adicionado SVG do símbolo da UnB (dois elementos curvos cruzados representando o Eixo Monumental e o Eixo Rodoviário) na navbar ao lado do nome do site. Adicionada menção "Desenvolvido por LG_Mateus" no rodapé.

## [2026-03-20] Redesign do frontend com identidade visual da UnB
Substituído o tema padrão DaisyUI por design próprio com cores oficiais da UnB (Azul #003366, Verde #006633) e fonte Inter. Navbar, cards e inputs redesenhados com Tailwind puro. Adicionado feedback visual "Salvo!" ao salvar links, botão "Entrar →" em verde UnB, rodapé institucional e seletor `[data-card]` para evitar conflito com classes DaisyUI. Funcionalidade preservada integralmente (formatHorario, busca, debounce).

## [2026-03-20] Tradução de horários SIGAA para formato legível
Adicionada função `formatHorario()` no frontend que converte o código de horário do SIGAA (ex: `246M12`) para texto legível (ex: `Seg, Qua, Sex 08:00–10:00`). Suporta múltiplos blocos separados por `·`, intervalos de datas opcionais e todos os turnos (M/T/N). O valor original é mantido como tooltip no badge. A busca continua funcionando contra o valor bruto.

## [2026-03-20] Documentação detalhada dos endpoints
Expandida a seção de endpoints do CLAUDE.md com body/resposta do POST /, estrutura JSON do GET /json, comportamento de falha silenciosa e variável de ambiente DATA_FILE.

## [2026-03-20] Criação do CLAUDE.md adaptado
Reescrita do CLAUDE.md para incorporar regras de trabalho (branch dev, workflow de alterações, workflow de sugestões, padrões de código), mantendo o conteúdo técnico existente e adicionando lições aprendidas do projeto.
