# FRONTEND AUDIT — AraOS (AraCannabis SIAP)

**Data:** 2026-06-24
**Escopo:** `frontend/src/` (104 arquivos JS/JSX, ~1.477 ocorrências de `sx={{`)
**Stack:** React 18 + Material-UI v5 + React Router v6 + Recharts + FullCalendar
**Modo:** Read-only (somente auditoria, sem alteração de código)
**Classificação:** P0 (bloqueia uso) / P1 (passa imagem ruim) / P2 (melhoria)

---

## 1. SUMÁRIO EXECUTIVO

| Severidade | Total | P0 | P1 | P2 |
|---|---|---|---|---|
| Segurança / LGPD | 8 | 5 | 3 | 0 |
| UX bloqueante | 23 | 9 | 11 | 3 |
| Acessibilidade | 12 | 4 | 5 | 3 |
| Design System | 31 | 6 | 14 | 11 |
| Conteúdo (PT-BR) | 56 | 23 | 26 | 7 |
| Código morto | 21 arquivos / ~3.770 linhas | — | — | — |
| **TOTAL** | **151** | **47 P0** | **59 P1** | **24 P2** |

**Diagnóstico:** O frontend **NÃO está pronto para produção**. Um médico que acessa o sistema pela primeira vez encontra erros críticos de segurança, falhas de UX e aparência de MVP. Estimativa de esforço para saneamento: **5 sprints** (P0 = 1 sprint, P1 = 2 sprints, P2 = 2 sprints).

---

## 2. AUDITORIA POR TELA (20 critérios)

Critérios avaliados em cada tela: **Layout, Responsividade, Acessibilidade, Conteúdo PT-BR, Erros, Loading, Empty State, Breadcrumb, Contraste, Feedback, Hierarquia visual, CTA, Estados (hover/disabled/focus), Consistência tipográfica, Consistência cromática, Espaçamento, Performance percebida, Dados sensíveis, Mock/dados falsos, Robustez**.

### 2.1 CADASTRO PROFISSIONAIS (`CadastroProfissionaisPage.js`)
- **Severidade global:** P1
- Layout: OK (MUI padrão)
- Responsividade: OK
- **P0 — falta:** bloqueio se LGPD não aceito (backend valida, frontend não)
- **P1:** Email/E-mail mistura; placeholder `Email` em inglês
- **P2:** erro.message exposto se backend falhar

### 2.2 LOGIN (`App.js` SimpleLogin, LoginDireto)
- **Severidade global:** **P0**
- `SimpleLogin.js:19,30` — `localhost:5173` hardcoded em produção
- `SimpleLogin.js:47,51` — stack trace + tokens expostos via `setMessage('Erro: ' + error.message)`
- `SimpleLogin.js:81,91` — credenciais hardcoded `admin / AraOS@2025`
- Sem ErrorBoundary global → qualquer erro derruba a tela
- Background gradient claro hardcoded (`App.js:171,172`) → quebra dark mode
- 167 IconButtons sem `aria-label`
- Botão mostra só `<CircularProgress />` durante loading (perde affordance)

### 2.3 DASHBOARD (`InternalDashboard.js`)
- **Severidade global:** P1
- `@keyframes fadeInUp` definido DUAS vezes no mesmo arquivo (linhas 58-62 e 148-152)
- `icon` prop é passado mas nunca renderizado (emoji usado no lugar)
- Stat cards com cores hardcoded (`InternalDashboard.js:188`): `const COLORS = ['#0d7377', ...]`
- Sem Empty State quando não há dados
- Sem Breadcrumb

### 2.4 PACIENTES (`PacientesPage.js`, `PatientList.js`)
- **Severidade global:** P1
- Tabs com `disabled` state — UX confunde (não indica motivo)
- 167 IconButtons sem aria-label (Delete/Edit/View)
- `<Avatar>` sem `alt` (`PatientList.js:367-371`)
- `fontSize: '1.1rem'` em TableCell (sobrescreve theme)
- Tabela sem `overflowX: 'auto'` em mobile

### 2.5 CONSULTAS (`ConsultasPage.js`, `CalendarioConsultas.js`)
- **Severidade global:** P1
- `CalendarioConsultas.js:191` — `alert(response.message)` mostra resposta crua do backend
- Sem Empty State visual (só Alert estático)
- Sem Breadcrumb
- `Loading button` sem texto durante operação

### 2.6 PRONTUÁRIO (`PatientDetailPage.js`)
- **Severidade global:** P1
- Tabs com emojis (`📝 📊 ⚖️ 🧬 🌿 📋`) misturados com Material-UI Icons
- `PatientDashboard.js:132-133` — typo `"acess ar todo seu histórico"`
- Altura fixa de gráficos sem fallback responsivo

### 2.7 PRESCRIÇÕES (`PrescriptionPanel.js`, `ConfiguracaoPrescricaoPage.js`)
- **Severidade global:** P1
- Bordas hardcoded `#e0e0e0`, `#bdbdbd`
- Termo "Receita" vs "Prescrição" no mesmo arquivo (`PrescriptionPanel.js:169,192`)
- `Salvar Configuração` (singular) vs `Salvar Configurações` (plural) inconsistente
- Sem Loading explícito

### 2.8 CANNABIS (`CatalogoPage.js`, `SugestaoPrescricao.js`)
- **Severidade global:** **P0**
- `CatalogoPage.js:111` — botão "Novo Produto" com `TODO` dentro (placeholder visível ao usuário)
- `SugestaoPrescricao.js` INTEIRO com PT-BR quebrado: 23+ palavras sem acento
  - `"Condicao Medica Principal"`, `"Dor Cronica"`, `"Insonia"`, `"Precaucoes"`, `"Recomendacao Farmaceutica"`, etc.
- `JSON.stringify` em UI (`ProdutoList.js:516`, `CatalogoUpload.js:225`)
- Botão "Obter Sugestoes do Farmaceutico" → sem acento

### 2.9 NUTROLOGIA (novo módulo)
- **Severidade global:** P1
- Tela em construção com placeholders
- Sem empty states específicos

### 2.10 EXAMES (`ExameManager.js`)
- **Severidade global:** P1
- Cores hardcoded (`#4caf50`, `#2196f3`)
- Sem Breadcrumb
- Loading button sem texto

### 2.11 CONFIGURAÇÕES (`ConfiguracaoIAPage.js`, `AIConfigPage.js`)
- **Severidade global:** P0
- `AIConfigPage.js:116-117` — chave duplicada em objeto (`has_xai_key: false`) — bug silencioso
- 4 botões Edit sem `onClick` (`AIDashboard.js:818,899,988,1062`)
- Sem Breadcrumb em fluxos com 5+ tabs
- JSON.stringify em TextField (`AIDashboard.js:1557`) — UX horrível

### 2.12 SECRETÁRIA (`AssociationPage.js`, `MembersPage.js`, `DispensationPage.js`, `StockPage.js`)
- **Severidade global:** P1
- `StockPage.js:153` — `TODO: Substituir por Selector de Produtos do Backend` visível
- Sem Breadcrumb consistente
- `Salvar` vs `Gravar` — sem glossário

### 2.13 PLANOS (`PlanosPage.js`)
- **Severidade global:** P1
- "MAIS POPULAR" em caps no chip (mistura com `Popular` em outros)
- Tela vazia se API `/planos/` falha (sem retry)
- Cor como único diferenciador (`PlanosPage.js:242,253,263`) — falha daltônicos
- Email/E-mail mistura

### 2.14 MÓDULOS (`ModulosPage.js`)
- **Severidade global:** P1
- `err.message` exposto diretamente em 4+ lugares
- Sem Loading skeleton (só CircularProgress)

### 2.15 BILLING (`BillingPage.js`, `PagamentoPage.js`)
- **Severidade global:** **P0**
- `BillingPage.js:89` — `"(mock)"` visível ao usuário
- `AdminPage.js:825` — Faturamento hardcoded `R$ 99`
- `PagamentoPage.js:149` — `"Nao foi possivel iniciar o pagamento"` (sem acento)
- `BillingPage.js:57,67` — `"Nao definido"` (sem acento)
- Bordas hardcoded em `PagamentoPage.js`

### 2.16 AI DASHBOARD (`AIDashboard.js`)
- **Severidade global:** P0
- 4 botões Edit sem onClick (linhas 818,899,988,1062)
- `md={2.4}` em 5 lugares — valor fracionário quebra Grid do MUI
- Grid spacings inconsistentes
- Sem Breadcrumb
- `JSON.stringify` em TextField (linha 1557)

### 2.17 AI CHAT (`AIChatPage.js`)
- **Severidade global:** **P0**
- `AIChatPage.js:171` — WebSocket `ws://localhost:8765` hardcoded (não funciona em prod)
- `AIChatPage.js:339` — inconsistência de payload (`message` vs `mensagem`) entre cliente/servidor
- Cores hardcoded: `#25d366` (verde WhatsApp), `#ffebee`, `#f5f5f5` — quebra design system
- Animações `pulseLive` e `pulse` definidas localmente (não globais)
- `borderRadius: '22px'` fora do padrão (theme usa 12px)

### 2.18 IMPORT/EXPORT (`BatchImportPage.js`, `ImportExportManager.js`)
- **Severidade global:** P1
- `BatchImportPage.js:32-69` — `setInterval` SEM cleanup → memory leak
- `alert()` em sucesso/erro
- Bordas hardcoded

### 2.19 LGPD / SEGURANÇA (`SecurityPage.js`, `PrivacyPolicy.js`)
- **Severidade global:** P1
- Email hardcoded `contato@arapath.com.br` (não personalizável)
- Falta banner LGPD ativo em sessões não-consentidas
- Sem tela dedicada de "Sem Permissão" (403)

### 2.20 LANDING PAGE (`LandingPage.js`)
- **Severidade global:** P1
- **Dead link:** `to="/security"` (deveria ser `/seguranca`) — quebra navegação
- Cores hardcoded em 6 cards de especialidade (linhas 406-411)
- Testimonials hardcoded com nomes fictícios
- Gradient complexo que não respeita dark mode

---

## 3. ACHADOS CRÍTICOS POR CATEGORIA

### 3.1 Segurança / LGPD (P0)
| # | Arquivo:Linha | Problema |
|---|---|---|
| 1 | `pages/DefinePasswordPage.js:22` | `console.log('DEFINE_PASSWORD: Token:', token, 'UserId:', userId)` — **vaza token de reset** |
| 2 | `components/SimpleLogin.js:19,30,81,91` | URLs localhost hardcoded + credenciais `admin/AraOS@2025` |
| 3 | `services/api.js:119` | `throw new Error(JSON.stringify(error.response.data))` — vaza estrutura técnica |
| 4 | (Projeto inteiro) | **Sem ErrorBoundary global** → qualquer erro derruba app |
| 5 | `pages/AIChatPage.js:171,339` | WebSocket hardcoded + payload inconsistency |

### 3.2 UX Bloqueante (P0)
| # | Arquivo:Linha | Problema |
|---|---|---|
| 6 | `pages/CatalogoPage.js:111` | Botão "Novo Produto" com `TODO` placeholder |
| 7 | `pages/LandingPage.js:700` | Loading infinito se API `/planos/` falha |
| 8 | `pages/AIDashboard.js:511,525,539,553,567` | `md={2.4}` fracionário quebra Grid |
| 9 | `pages/AIDashboard.js:818,899,988,1062` | 4 botões Edit sem onClick |
| 10 | `pages/patient/PatientRegister.js:71,116` | `alert()` em fluxo crítico de cadastro |
| 11 | `pages/PlanosPage.js:130-131` | Tela vazia sem retry se API falha |
| 12 | 20+ ocorrências | `alert()` do browser em produção |
| 13 | `pages/AIConfigPage.js:116-117` | Chave duplicada `has_xai_key: false` |

### 3.3 Acessibilidade (P0)
| # | Arquivo | Problema |
|---|---|---|
| 14 | (167 IconButtons) | Apenas 7 com `aria-label` |
| 15 | (Projeto inteiro) | Sem rota catch-all 404 — tela branca |
| 16 | (Projeto inteiro) | Sem página dedicada de "Sem Permissão" (403) |
| 17 | `components/PatientList.js:367-371` | `<Avatar>` sem `alt` |

### 3.4 Design System (P0)
| # | Arquivo | Problema |
|---|---|---|
| 18 | (30+ ocorrências) | `color: '#fff'` hardcoded → dark mode quebra |
| 19 | `App.js:171,172` | Background gradient hardcoded no Login |
| 20 | `pages/LandingPage.js:312,421,460,517,748,789,826,843,869` | Landing inteira com cores hardcoded |
| 21 | `pages/AIChatPage.js:504,656,686,711,733,753` | Chat com bolhas hardcoded claro |
| 22 | `services/api.js:1066` | `timeout: 0` em `crewAIService.chat` → loading infinito |
| 23 | `services/api.js:1087` | Sem timeout explícito padronizado |

---

## 4. MATRIZ DE RISCO (Top 15 hotspots)

| Rank | Arquivo | Linhas | P0 | P1 | P2 | Risco |
|---|---|---|---|---|---|---|
| 1 | `frontend/src/App.js` | 800 | 4 | 8 | 5 | CRÍTICO |
| 2 | `frontend/src/services/api.js` | 1100 | 2 | 6 | 4 | CRÍTICO |
| 3 | `frontend/src/pages/LandingPage.js` | 885 | 3 | 7 | 4 | ALTO |
| 4 | `frontend/src/pages/AIDashboard.js` | 1600 | 5 | 9 | 6 | CRÍTICO |
| 5 | `frontend/src/pages/AIChatPage.js` | 800 | 3 | 7 | 5 | ALTO |
| 6 | `frontend/src/components/PatientList.js` | 600 | 2 | 6 | 4 | ALTO |
| 7 | `frontend/src/components/NavigationMenu.js` | 500 | 0 | 4 | 5 | MÉDIO |
| 8 | `frontend/src/pages/AdminPage.js` | 950 | 1 | 5 | 6 | ALTO |
| 9 | `frontend/src/components/catalogo/SugestaoPrescricao.js` | 320 | 1 | 23 | 2 | ALTO |
| 10 | `frontend/src/pages/BillingPage.js` | 200 | 2 | 3 | 2 | ALTO |
| 11 | `frontend/src/pages/PlanosPage.js` | 280 | 2 | 4 | 3 | MÉDIO |
| 12 | `frontend/src/components/PatientForm.js` | 480 | 0 | 5 | 4 | MÉDIO |
| 13 | `frontend/src/components/CalendarioConsultas.js` | 220 | 1 | 3 | 2 | MÉDIO |
| 14 | `frontend/src/components/MedicalEvolution.js` | 450 | 0 | 4 | 3 | MÉDIO |
| 15 | `frontend/src/pages/CadastroProfissionaisPage.js` | 620 | 0 | 5 | 4 | MÉDIO |

---

## 5. RECOMENDAÇÕES TOP-10

| # | Ação | Severidade | Esforço | ROI |
|---|---|---|---|---|
| 1 | Remover `console.log` de PII (token, JWT) | P0 | 1h | ALTÍSSIMO |
| 2 | Adicionar ErrorBoundary global | P0 | 2h | ALTÍSSIMO |
| 3 | Adicionar rota catch-all 404 | P0 | 1h | ALTÍSSIMO |
| 4 | Adicionar `aria-label` em 167 IconButtons | P0 | 3h | ALTO |
| 5 | Substituir `alert()` por Snackbar (23 ocorrências) | P1 | 4h | ALTO |
| 6 | Corrigir PT-BR sem acento em 23 strings P0 | P1 | 2h | ALTO |
| 7 | Consolidar `borderRadius` no Theme | P1 | 3h | MÉDIO |
| 8 | Adicionar Breadcrumbs em fluxos longos | P1 | 4h | MÉDIO |
| 9 | Substituir cores hardcoded por theme.palette | P1 | 8h | MÉDIO |
| 10 | Criar componente `<EmptyState>` reutilizável | P2 | 3h | MÉDIO |

---

## 6. CONCLUSÃO

O frontend do AraOS tem **fundações sólidas** (ThemeContext bem estruturado, 11 keyframes globais, sistema de sombras, paleta consistente em sua definição) mas a **execução está aquém da produção**:

- **47 problemas P0** que bloqueiam uso imediato
- **59 problemas P1** que passam imagem ruim
- **24 problemas P2** de polimento
- **21 arquivos / ~3.770 linhas** de código morto

Recomendação: **bloquear release público** até saneamento dos P0 + P1 críticos (ver `FRONTEND_BACKLOG.md`).

Ver também:
- `UX_PRODUCTION_REPORT.md` — visão por perspectiva do médico
- `DEAD_COMPONENTS.md` — código morto detectável
- `UI_INCONSISTENCIES.md` — inconsistências de design system
- `FRONTEND_BACKLOG.md` — backlog priorizado P0→P1→P2
