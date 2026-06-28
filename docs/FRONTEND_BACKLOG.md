# FRONTEND BACKLOG — Sequência Priorizada P0 → P1 → P2

**Data:** 2026-06-24
**Método:** backlog derivado de `FRONTEND_AUDIT.md` + `UX_PRODUCTION_REPORT.md` + `DEAD_COMPONENTS.md` + `UI_INCONSISTENCIES.md`
**Estimativas:** baseadas em desenvolvedor React/MUI sênior (~8h/dia útil)

---

## 1. VISÃO GERAL

| Onda | Itens | Esforço | Sprints | Bloqueio release |
|---|---|---|---|---|
| **P0** | 47 | ~80h | 1 sprint (10 dias) | SIM |
| **P1** | 59 | ~240h | 2 sprints | NÃO, mas recomendado antes do GA |
| **P2** | 24 | ~120h | 2 sprints | NÃO |
| **TOTAL** | 130 | ~440h | ~5 sprints | — |

---

## 2. ONDA P0 — BLOQUEIA RELEASE (1 sprint)

### 2.1 Segurança / LGPD (8h)

| # | Item | Arquivo | Esforço | Verificação |
|---|---|---|---|---|
| 1 | Remover `console.log('DEFINE_PASSWORD: Token:', token, ...)` — **vaza PII** | `pages/DefinePasswordPage.js:22` | 0.5h | Grep `console.log` + token |
| 2 | Remover URLs `localhost:5173` hardcoded | `components/SimpleLogin.js:19,30` | 1h | Variável de ambiente |
| 3 | Remover credenciais `admin/AraOS@2025` hardcoded | `components/SimpleLogin.js:81,91` | 1h | Grep `AraOS@` |
| 4 | Trocar `JSON.stringify(error.response.data)` por mensagem user-friendly | `services/api.js:119` | 1h | E2E: simular erro |
| 5 | Adicionar ErrorBoundary global | novo `components/ErrorBoundary.js` + `App.js` | 2h | Throw erro em teste |
| 6 | Adicionar rota catch-all `<NotFound />` | `App.js` + novo `pages/NotFoundPage.js` | 1h | Navegar para `/xyz-inexistente` |
| 7 | Corrigir WebSocket hardcoded `ws://localhost:8765` | `pages/AIChatPage.js:171` | 1h | Variável de ambiente |
| 8 | Corrigir inconsistência payload AI Chat (`message` vs `mensagem`) | `pages/AIChatPage.js:339` | 0.5h | E2E: enviar mensagem |

### 2.2 UX bloqueante — botões quebrados (12h)

| # | Item | Arquivo | Esforço |
|---|---|---|---|
| 9 | Implementar onClick em 4 botões Edit do AIDashboard | `pages/AIDashboard.js:818,899,988,1062` | 4h |
| 10 | Substituir `md={2.4}` por valores inteiros (md={2} ou md={3}) | `pages/AIDashboard.js:511,525,539,553,567` | 2h |
| 11 | Remover `{/* TODO: abrir modal de cadastro manual */}` placeholder | `pages/CatalogoPage.js:111` | 1h |
| 12 | Implementar retry em Planos quando API falha | `pages/PlanosPage.js:130-131` | 2h |
| 13 | Remover `Loading infinito` se API `/planos/` falha | `pages/LandingPage.js:700` | 1h |
| 14 | Remover chave duplicada `has_xai_key: false` | `pages/AIConfigPage.js:116-117` | 0.5h |
| 15 | Substituir 20+ `alert()` por Snackbar (componentes críticos primeiro) | `pages/AdminPage.js`, `MobileUploadPage.js`, `EvolutionManager.js`, `SymptomsManager.js`, `ProductForm.js`, `CalendarioConsultas.js`, `ProdutoList.js`, `PatientRegister.js` | 4h |

### 2.3 Acessibilidade (8h)

| # | Item | Arquivo | Esforço |
|---|---|---|---|
| 16 | Adicionar `aria-label` em 167 IconButtons (script automatizado + revisão) | global | 3h |
| 17 | Adicionar `<NotFound>` (rota catch-all) | `App.js` (já em #6) | — |
| 18 | Adicionar página `403 — Sem Permissão` (substitui redirect silencioso) | nova `pages/ForbiddenPage.js` + uso em `OnboardingPage.js:114` | 3h |
| 19 | Adicionar `alt` em `<Avatar>` e imagens decorativas | `components/PatientList.js:367-371`, `ImageViewer.js` | 2h |

### 2.4 Design System P0 — dark mode (12h)

| # | Item | Esforço |
|---|---|---|
| 20 | Substituir 30+ ocorrências de `color: '#fff'` por `color: 'primary.contrastText'` ou similar | 4h |
| 21 | Substituir `App.js:171,172` background gradient hardcoded por theme | 1h |
| 22 | Substituir cores hardcoded em `LandingPage.js:312-869` (15 ocorrências) | 3h |
| 23 | Substituir cores hardcoded em `AIChatPage.js:504-753` (chat inteiro) | 3h |
| 24 | Adicionar `timeout: 30000` em chamadas axios sem timeout | 1h |

### 2.5 Conteúdo P0 — PT-BR sem acento (10h)

| # | Item | Esforço |
|---|---|---|
| 25 | Corrigir 23 strings P0 sem acento (ver `UI_INCONSISTENCIES.md` §4.1) | 4h |
| 26 | Corrigir 3 `console.error` em inglês | 0.5h |
| 27 | Remover `"(mock)"` e `R$ 99` hardcoded do Billing | 1h |
| 28 | Corrigir typo `"acess ar todo seu histórico"` | 0.5h |
| 29 | Corrigir `pages/PagamentoPage.js:149` `"Nao foi possivel"` | 0.5h |
| 30 | Corrigir `pages/BillingPage.js:57,67` `"Nao definido"` | 0.5h |
| 31 | Corrigir `pages/DefinePasswordPage.js:31,44` (senhas) | 0.5h |
| 32 | Corrigir `pages/PasswordSetupRequestPage.js:20` | 0.5h |

**Subtotal P0: ~50h** (ajustado para incluir dependências e testes)

---

## 3. ONDA P1 — PRÉ-GA (2 sprints)

### 3.1 Remover código morto (8h)

| # | Item | Esforço |
|---|---|---|
| 33 | Confirmar zero imports de 15 componentes órfãos (grep) | 1h |
| 34 | Mover para `_deprecated/` | 0.5h |
| 35 | Validar por 1 sprint em produção | (tempo) |
| 36 | Deletar `_deprecated/` | 0.5h |
| 37 | Verificar `SugestaoPrescricao.js` (caminho dinâmico?) antes de deletar | 1h |
| 38 | Remover `AdBanner.js` (398 linhas, importado mas não renderizado) | 0.5h |
| 39 | Remover 2 serviços órfãos (`aiClinicalService.js`, `voiceService.js`) | 0.5h |
| 40 | Decidir destino da rota `/billing` morta | 0.5h |
| 41 | Corrigir dead link `LandingPage.js:700` `to="/security"` → `/seguranca` | 0.5h |

### 3.2 Console.log / alert / error.message (16h)

| # | Item | Esforço |
|---|---|---|
| 42 | Remover 209 `console.log` em produção (deixar só os gateados por `NODE_ENV === 'development'`) | 8h |
| 43 | Substituir 23 `alert()` restantes por Snackbar | 4h |
| 44 | Mapear `error.message` para mensagens PT-BR user-friendly | 4h |

### 3.3 Design System P1 — padronização (40h)

| # | Item | Esforço |
|---|---|---|
| 45 | Substituir `#667eea`/`#764ba2` (off-theme) por cores theme | 2h |
| 46 | Substituir 12+ bordas hardcoded por `borderColor: 'divider'` | 2h |
| 47 | Substituir backgrounds `#fafafa`/`#f5f5f5` por theme | 2h |
| 48 | Substituir 11 cores semânticas hex por `theme.palette.X.main` | 3h |
| 49 | Padronizar 5 elevations em 3 (`flat: 0, low: 1, medium: 2, high: 3`) | 4h |
| 50 | Padronizar 4 paddings em 3 (`p: 2/3/4`) | 4h |
| 51 | Consolidar borderRadius (15+ valores → 5: `4, 8, 12, 16, 24`) | 6h |
| 52 | Remover `fontSize` hardcoded, usar variantes do theme | 4h |
| 53 | Padronizar `fontWeight` (string vs number) | 2h |
| 54 | Remover keyframes duplicados (5 redefinições) | 4h |
| 55 | Padronizar durações de animação (3 níveis) | 3h |
| 56 | Substituir 30+ cores hardcoded em bordas/bg (lote) | 4h |

### 3.4 Breadcrumbs e navegação (8h)

| # | Item | Esforço |
|---|---|---|
| 57 | Criar `<PageBreadcrumbs trail={[...]} />` reutilizável | 2h |
| 58 | Adicionar em `PatientDetailPage` | 1h |
| 59 | Adicionar em `ConfiguracaoIAPage`, `AIConfigPage`, `AIDashboard` | 2h |
| 60 | Adicionar em `AdminPage` (5 tabs) | 1h |
| 61 | Adicionar em `MedicalEvolution`, `PrescriptionPanel`, `ExamManager` | 2h |

### 3.5 Loading states (8h)

| # | Item | Esforço |
|---|---|---|
| 62 | Padronizar `timeout` em chamadas axios (helper `withTimeout(ms)`) | 2h |
| 63 | Substituir `timeout: 0` em `crewAIService.chat` | 0.5h |
| 64 | Loading button com texto (não só spinner) — 12+ botões | 4h |
| 65 | Loading skeleton para listas longas | 1.5h |

### 3.6 Tabelas responsivas (8h)

| # | Item | Esforço |
|---|---|---|
| 66 | Adicionar `overflowX: 'auto'` em TableContainers | 2h |
| 67 | Padronizar paginação (TablePagination vs Pagination) | 4h |
| 68 | Reduzir `fontSize: '1.1rem'` em `PatientList.js` (mobile quebra) | 2h |

### 3.7 Conteúdo P1 (16h)

| # | Item | Esforço |
|---|---|---|
| 69 | Corrigir 26 strings P1 sem acento (ver `UI_INCONSISTENCIES.md` §4.1) | 6h |
| 70 | Padronizar Email/E-mail | 2h |
| 71 | Padronizar "Prescrição" vs "Receita" | 1h |
| 72 | Padronizar "Salvar" (sempre 1 palavra) | 2h |
| 73 | Limpar `response.message` exposto em alert/Snackbar | 3h |
| 74 | Mapear erros backend → PT-BR (errorCodes.js) | 2h |

### 3.8 Validações pendentes (4h)

| # | Item | Esforço |
|---|---|---|
| 75 | Verificar `BatchImportPage.js:32-69` `setInterval` sem cleanup | 2h |
| 76 | Validar responsividade de gráficos (altura fixa) | 2h |

**Subtotal P1: ~108h**

---

## 4. ONDA P2 — POLISH (2 sprints)

### 4.1 Emojis → Material-UI Icons (12h)

| # | Item | Esforço |
|---|---|---|
| 77 | Substituir 133 emojis por Material-UI Icons (script + revisão) | 12h |

### 4.2 Empty States padronizados (12h)

| # | Item | Esforço |
|---|---|---|
| 78 | Criar componente `<EmptyState icon title description action />` | 3h |
| 79 | Migrar 16 empty states | 8h |
| 80 | Adicionar ilustrações (SVG inline ou set MUI) | 1h |

### 4.3 Conteúdo P2 (16h)

| # | Item | Esforço |
|---|---|---|
| 81 | Padronizar 7 inconsistências terminológicas (glossário) | 4h |
| 82 | Capitalização em Chip (`MAIS POPULAR` → `Popular`) | 1h |
| 83 | Padronizar 30+ emojis em labels (substituir por Icons) | 4h |
| 84 | Email hardcoded `arapath.com.br` → variável de ambiente | 2h |
| 85 | Remover testimonials hardcoded (LGPD risk) | 2h |
| 86 | Corrigir `placeholder="EXCLUIR"` → instrução clara | 1h |
| 87 | Trocar `aria-label="editar"` → `aria-label="Editar evolução"` | 0.5h |
| 88 | Mover lógica de error.message para hook `useErrorMessage()` | 1.5h |

### 4.4 UX polish (16h)

| # | Item | Esforço |
|---|---|---|
| 89 | Adicionar Toast/Snackbar consistentes (substituir Alert estático em alguns casos) | 4h |
| 90 | Adicionar feedback de hover em todos botões (verificar consistência) | 2h |
| 91 | Loading skeleton para dashboard | 4h |
| 92 | Validação visual de formulários (não só submit-time) | 4h |
| 93 | Refatorar ícones que não renderizam (InternalDashboard.js) | 2h |

### 4.5 Verificação final (8h)

| # | Item | Esforço |
|---|---|---|
| 94 | Rodar E2E (Playwright) em todas as 20 telas | 4h |
| 95 | Auditoria de contraste WCAG AA | 2h |
| 96 | Lighthouse score (>90 em Performance, Accessibility, Best Practices, SEO) | 2h |

**Subtotal P2: ~64h**

---

## 5. SEQUÊNCIA EXATA DE CORREÇÕES (maximiza percepção de qualidade)

Esta sequência foi escolhida para que **cada commit entregue valor visível ao usuário** (em vez de internals).

### Sprint 1 (P0 — bloqueia release)

**Semana 1:**
1. **Dia 1 manhã:** Remover 4 vazamentos de PII (token no console, credenciais hardcoded, URLs localhost, JSON.stringify). Commit: `fix(security): remove PII leaks`.
2. **Dia 1 tarde:** Adicionar ErrorBoundary + 404 + 403. Commit: `fix(routing): error boundaries and 404/403 pages`.
3. **Dia 2 manhã:** Corrigir 23 strings P0 sem acento + typo histórico. Commit: `fix(i18n): critical PT-BR strings without accents`.
4. **Dia 2 tarde:** Corrigir 4 botões Edit sem onClick + Grid quebrado + TODO placeholder. Commit: `fix(ui): broken buttons and grid layout`.
5. **Dia 3 manhã:** Adicionar aria-labels em 167 IconButtons + alt em Avatares. Commit: `fix(a11y): aria-labels and alt texts`.
6. **Dia 3 tarde:** Substituir 20+ `alert()` por Snackbar (componentes críticos primeiro). Commit: `refactor(ux): replace alert() with snackbars`.
7. **Dia 4 manhã:** Corrigir dark mode quebrado (30+ `#fff` hardcoded + gradient login + landing + AI chat). Commit: `fix(theme): dark mode coverage`.
8. **Dia 4 tarde:** Remover `"(mock)"` + `R$ 99` hardcoded do Billing. Commit: `fix(billing): remove mocks from production`.
9. **Dia 5 manhã:** Corrigir WebSocket AI Chat + payload inconsistency. Commit: `fix(ai-chat): env-based websocket and payload`.
10. **Dia 5 tarde:** Testes E2E + validação. Commit: `test(e2e): P0 coverage`.

### Sprint 2 (P1 — parte 1)

**Semana 2-3:**
1. Mover código morto para `_deprecated/` (não deletar ainda)
2. Padronizar cores (12+ hex → theme.palette)
3. Padronizar elevations (5 → 3)
4. Padronizar paddings (4 → 3)
5. Padronizar borderRadius (15+ → 5)

### Sprint 3 (P1 — parte 2)

**Semana 4-5:**
1. Criar componente `<PageBreadcrumbs>`
2. Adicionar em 6 telas
3. Padronizar Loading states
4. Tabelas responsivas
5. Console.log cleanup (gatear por NODE_ENV)
6. Mapear error.message → PT-BR

### Sprint 4-5 (P2 — polish)

**Semana 6-9:**
1. Emojis → Material Icons
2. Empty States padronizados
3. Conteúdo P2
4. Verificação final (E2E, Lighthouse, contraste WCAG)

---

## 6. CRITÉRIOS DE DONE (Definition of Done)

Para cada item:
- [ ] Código compila sem warnings
- [ ] Lint passa (ESLint)
- [ ] TypeScript-like check (PropTypes) passa
- [ ] Testes E2E cobrem o caminho feliz
- [ ] Testes E2E cobrem caminho de erro
- [ ] Dark mode verificado (se aplicável)
- [ ] Acessibilidade verificada (axe-core)
- [ ] Documentação atualizada (se aplicável)

Para cada onda:
- [ ] 100% dos P0 corrigidos
- [ ] Lighthouse score > 90 em todas as métricas
- [ ] Nenhum `console.log` em produção
- [ ] Nenhum `alert()` em produção
- [ ] Nenhum `TODO` placeholder visível
- [ ] Dark mode funcional em 100% das telas

---

## 7. RISCOS E DEPENDÊNCIAS

| Risco | Mitigação |
|---|---|
| Designer não disponível para revisar cores | Usar MUI palette padrão como fallback |
| QA não disponível para validar 167 IconButtons | Script automatizado + amostragem |
| Tempo de execução dos P0 estoura para 2 sprints | Cortar `dark mode` de telas secundárias (manter só Login/Dashboard/AI Chat) |
| Código morto deletado é usado em feature flag | Validar `.env.example` e `featureFlagService.js` antes |

---

## 8. MÉTRICAS DE SUCESSO

Antes (estado atual):
- Lighthouse Performance: ~60
- Lighthouse Accessibility: ~50 (167 IconButtons sem aria)
- Lighthouse Best Practices: ~70 (console.log, erros expostos)
- Lighthouse SEO: ~80
- Bundle size: ~2.5 MB (gzipped)
- Bugs visuais conhecidos: 47 P0

Depois (P0+P1+P2 completos):
- Lighthouse Performance: >90
- Lighthouse Accessibility: >95
- Lighthouse Best Practices: >95
- Lighthouse SEO: >90
- Bundle size: ~2.0 MB (gzipped) — redução de 20%
- Bugs visuais conhecidos: 0 P0, < 5 P1

---

> **Próxima ação:** após aprovação humana, executar Sprint 1 (P0). Estimativa: **10 dias úteis** para desbloquear release.
