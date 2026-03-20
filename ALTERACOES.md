# Histórico de Alterações

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
