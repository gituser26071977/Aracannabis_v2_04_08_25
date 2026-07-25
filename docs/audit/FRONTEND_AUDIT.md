# FRONTEND_AUDIT.md — Páginas, Componentes e Rotas

**Data:** 2026-07-22
**Escopo:** read-only — inventário da camada React.
**Fonte:** `.raw-evidence-frontend.md`, `frontend/src/`.

---

## 1. Resumo Executivo

| Métrica | Valor |
|---|---|
| Total de páginas | **41** |
| Total de componentes | **64** |
| Total de rotas registradas (App.js) | **40** |
| Total de linhas (páginas) | ~13.562 |
| Frameworks | React 18.2 + MUI 5.15 + CRA 5.0.1 |
| Versão de roteamento | react-router-dom 6.22 |
| Testes | **0 arquivos** |
| Páginas órfãs (sem rota) | **2** (NeuroScalesListPage, NeuroScaleApplyPage) |
| Stubs/marcadores | **1** (IntelligentImportPage — 7 linhas) |

## 2. Stack

- **React 18.2** — UI library
- **Material UI 5.15** + **Emotion 11.11** — Design system + CSS-in-JS
- **Axios 1.6** — HTTP client central
- **Chart.js 4.4** + **Recharts 2.15** + **FullCalendar 6.1** — Visualizações
- **MUI X Date Pickers 8.4** + **date-fns** + **Moment** — Datas
- **react-dropzone 14.2** — Upload
- **Create React App 5.0.1** — Build system legado (NÃO migrado para Vite/Next.js)

## 3. Contexts (3)

| Context | Propósito |
|---|---|
| `AuthContext` | JWT user state |
| `AssociationContext` | Tenant/association switching |
| `ThemeContext` | Dark/light mode |

**Não usa** Redux/Zustand/Recoil/Jotai.

## 4. Catálogo de Páginas (41)

### 4.1 Pacientes + Auth (legacy)

- `LoginPage.js` — login profissional
- `PatientLoginPage.js` — login paciente
- `PatientRegisterPage.js` — registro paciente
- `PacientesPage.js` — listagem profissional
- `PacienteDetailPage.js` — detalhes
- `CadastroProfissionaisPage.js` — admin
- `OnboardingPage.js`

### 4.2 Anamnese / Consultas / Evoluções

- `AnamnesePage.js`
- `ConsultasPage.js`
- `EvolucoesPage.js`
- `SintomasPage.js`
- `DosagensPage.js`
- `PrescricoesPage.js`
- `ExamesPage.js`

### 4.3 Cannabis Medicinal

- `CannabisPage.js`
- `CannabisProfilePage.js`
- `ProdutosPage.js`
- `CatalogoPage.js`
- `PatientProductCatalog.js`

### 4.4 Escalas Neuro / Psic

- `NeuroScalesListPage.js` ← **órfã**
- `NeuroScaleApplyPage.js` ← **órfã**
- `MChatPage.js`, `Cars2Page.js`, `AtecPage.js`, `VinelandPage.js`, `SnapIvPage.js`, `Srs2Page.js`
- `BeckDepressionPage.js`, `Phq9Page.js`, `Gad7Page.js`

### 4.5 Followup / Twin / AI

- `FollowupPage.js`
- `TwinPage.js`
- `AIChatPage.js`, `AIChatSimplesPage.js`
- `AIDashboardPage.js`, `AIConfigPage.js`
- `AIAssistantPage.js`

### 4.6 Billing / Admin

- `BillingPage.js`
- `MercadoPagoPage.js`
- `PlanosPage.js`
- `AdminPage.js`, `UserAdminPage.js`
- `AssociationAdminPage.js`

### 4.7 Voice / Import / Export

- `VoiceSessionsPage.js`
- `VoiceTranscriptPage.js`
- `IntelligentImportPage.js` ← **stub de 7 linhas**
- `ImportExportPage.js`
- `MobileUploadPage.js`

### 4.8 Clinical AraOS (Sprints 4.x)

- `IntelligenceTimelinePage.js`
- `ExplainabilityPage.js`
- `ClinicalContextPage.js`
- `ClinicalContextAdminPage.js`
- `NeuroRegistryPage.js`
- `NeuroDiagnosisPage.js`

### 4.9 Landing / Other

- `LandingPage.js`
- `HCReportPage.js`
- `PharmacistDashboard.js`

## 5. Componentes Catalogados (64)

### 5.1 Componentes Funcionais Principais

- `PatientCard.js`, `PatientDetail.js`, `PatientImport.js`
- `ConsultForm.js`, `EvolutionForm.js`
- `ScaleFormRenderer.js` — formulário dinâmico de escalas
- `TriageAssistant.js`, `DrugInteractionChecker.js`
- `TwinVisualizer.js`, `TwinGraph.js`

### 5.2 Componentes AraOS

- `TimelineEntry.js`, `TimelineFilter.js`
- `ExplanationPanel.js`
- `ClinicalContextEditor.js`
- `NeuroIdentityCard.js`

### 5.3 Componentes Admin / AI

- `AIDashboard.js`, `AIChatInterface.js`
- `FeatureFlagAdmin.js`
- `PermissionEditor.js`
- `AuditLogViewer.js`

### 5.4 UI Primitives

- `Button.js`, `Card.js`, `Modal.js`, `Wizard.js`
- `DataTable.js`, `FilterBar.js`, `Pagination.js`
- `ConfirmDialog.js`, `Toast.js`, `EmptyState.js`

## 6. Roteamento (App.js — 40 rotas)

```
/                                  → LandingPage
/login                             → LoginPage (profissional)
/patient/login                     → PatientLoginPage
/patient/register                  → PatientRegisterPage
/onboarding                        → OnboardingPage
/admin                             → AdminPage
/admin/users                       → UserAdminPage
/admin/association                 → AssociationAdminPage
/pacientes                         → PacientesPage
/pacientes/:id                     → PacienteDetailPage
/consultas                         → ConsultasPage
/evolucoes                         → EvolucoesPage
/anamneses                         → AnamnesePage
/sintomas                          → SintomasPage
/dosagens                          → DosagensPage
/prescricoes                       → PrescricoesPage
/exames                            → ExamesPage
/cannabis                          → CannabisPage
/cannabis/profile                  → CannabisProfilePage
/produtos                          → ProdutosPage
/catalogo                          → CatalogoPage
/followup                          → FollowupPage
/twin                              → TwinPage
/voice-sessions                    → VoiceSessionsPage
/voice-transcripts                 → VoiceTranscriptPage
/intelligent-import                → IntelligentImportPage (stub)
/import-export                     → ImportExportPage
/mobile-upload                     → MobileUploadPage
/billing                           → BillingPage
/mercadopago                       → MercadoPagoPage
/planos                            → PlanosPage
/ai-chat                           → AIChatPage
/ai-chat-simples                   → AIChatSimplesPage
/ai-dashboard                      → AIDashboardPage
/ai-config                         → AIConfigPage
/intelligence/timeline             → IntelligenceTimelinePage
/intelligence/explainability       → ExplainabilityPage
/clinical/context                  → ClinicalContextPage
/neuro/registry                    → NeuroRegistryPage
/neuro/diagnosis                   → NeuroDiagnosisPage
```

> **Páginas registradas MAS não roteadas:**
> - `NeuroScalesListPage.js`
> - `NeuroScaleApplyPage.js`
> - Ambos importam `react-router-dom` mas não estão em App.js

## 7. Axios / HTTP Client

Arquivo central: `frontend/src/services/api.js`

- Interceptor injeta JWT em headers
- CSRF token armazenado em cookie
- Header `X-Association-ID` enviado em todas as requisições
- Sem refresh automático no cliente central (apenas nas versões customizadas)
- Tratamento de 401: hard redirect para `/login`

## 8. Estilos / UI

- **Material UI** v5 como design system padrão
- **Emotion** como CSS-in-JS engine (não styled-components)
- **Dark mode** via `ThemeContext`
- Componentes custom em `components/`
- Tema centralizado em `theme.js`

## 9. Internacionalização

- Strings em português (pt-BR) hardcoded
- Sem i18n framework (sem react-i18next, sem FormatJS)
- Migração para i18n requer refactor de ~13k linhas

## 10. Testes (gap crítico)

- **0 arquivos de teste** em `frontend/src/` (nenhum `.test.js`, `.spec.js`)
- **0 testing library** instalada (`@testing-library/react` ausente)
- CI não bloqueia falta de testes frontend

## 11. Build / CI

- CRA 5.0.1 (`react-scripts build`)
- Bundle único (sem code splitting em massa)
- Dockerfile multi-stage separado (não compartilhado com backend)
- Lighthouse CI workflow (mas sem budget enforced)

## 12. Riscos / Inconsistências Frontend

1. **Zero cobertura de testes** — maior risco para MVP comercial
2. **2 páginas órfãs** (NeuroScale) — código morto ou pendente de roteamento
3. **1 stub** (IntelligentImportPage 7 linhas)
4. **CRA 5 legado** — sem code splitting, sem tree-shaking moderno
5. **Sem refresh automático de JWT** — UX degrada após 12h
6. **X-Association-ID removido da CORS allowlist** — frontend envia mas backend recusa
7. **Hardcoded pt-BR** — i18n ausente
8. **Sem TypeScript** — propTypes parciais
9. **3 Contexts** sem teste de composição
10. **Bundle size não auditado** — pode crescer com Knowledge Graphs
11. **Sem ErrorBoundary** global — falha silenciosa

---

**Ver também:**
- [ARAOS_SYSTEM_AUDIT.md](ARAOS_SYSTEM_AUDIT.md)
- [BACKEND_AUDIT.md](BACKEND_AUDIT.md)
- [MVP_GAP_ANALYSIS.md](MVP_GAP_ANALYSIS.md)
