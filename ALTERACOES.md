# Histórico de Alterações

## [2026-03-20] Criação do Visual.md com identidade visual da UnB
Pesquisado e documentado o sistema de identidade visual oficial da UnB: cores institucionais (Azul #003366 e Verde #006633), símbolo criado por Aloísio Magalhães em 1963, tipografias UnB Pro e UnB Office, história da instituição e diretrizes para aplicação no frontend do TurmasUnB.

## [2026-03-20] Tradução de horários SIGAA para formato legível
Adicionada função `formatHorario()` no frontend que converte o código de horário do SIGAA (ex: `246M12`) para texto legível (ex: `Seg, Qua, Sex 08:00–10:00`). Suporta múltiplos blocos separados por `·`, intervalos de datas opcionais e todos os turnos (M/T/N). O valor original é mantido como tooltip no badge. A busca continua funcionando contra o valor bruto.

## [2026-03-20] Documentação detalhada dos endpoints
Expandida a seção de endpoints do CLAUDE.md com body/resposta do POST /, estrutura JSON do GET /json, comportamento de falha silenciosa e variável de ambiente DATA_FILE.

## [2026-03-20] Criação do CLAUDE.md adaptado
Reescrita do CLAUDE.md para incorporar regras de trabalho (branch dev, workflow de alterações, workflow de sugestões, padrões de código), mantendo o conteúdo técnico existente e adicionando lições aprendidas do projeto.
