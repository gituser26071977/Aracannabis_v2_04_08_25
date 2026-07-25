# FEATURE_INVENTORY.md — Inventário Funcional Detalhado por Feature Area

**Data:** 2026-07-22
**Escopo:** read-only — inventário de features em três categorias (✅ Produção, 🟡 Parcial, 🔴 Ausente).
**Fonte:** cruzamento de `.raw-evidence-*.md` com `routes/`, `frontend/src/pages/`, `araos/clinical/`.

---

## 1. Legado SIAP — Cannabis Medicinal (Funcional)

### 1.1 Pacientes ✅

- **Backend:** 31 endpoints em `pacientes.py`, `Paciente` model
- **Frontend:** `PacientesPage` + `PacienteDetailPage`
- **Auth:** JWT profissional
- **Status:** funcional em produção desde 2025

### 1.2 Anamnese + Consultas + Evoluções ✅

- **Anamnese:** CRUD via `anamneses` table
- **Consultas:** agenda + status (agendada/realizada/cancelada)
- **Evoluções:** SOAP (subjetivo/objetivo/avaliação/plano) com criptografia opcional
- **Sintomas:** por consulta com intensidade
- **Exames:** upload PDF + OCR opcional
- **Frontend:** todas as páginas registradas
- **Status:** funcional, encrypt at rest configurável por tenant

### 1.3 Cannabis + Prescrições ✅

- **Cannabis medicinal:**
  - Produtos cannabis catalogados
  - `CannabisProfilePage` por paciente
  - `CannabisPage` geral
- **Prescrições:** tipos CBD/THC balance/full spectrum
- **Dosagens:** mg/dose, frequência, via
- **Status:** funcional em produção

### 1.4 Catálogo de Produtos + Intelligent Import ✅

- `CatalogoPage`: listagem geral
- `ProdutosPage`: CRUD
- `IntelligentImportPage`: **stub de 7 linhas** (sem rota visível)
- `patient_import_agent.py`: agente de importação

### 1.5 Escalas Neuropsicológicas (Parcial → Funcional)

| Escala | Faixa Etária | Status |
|---|---|---|
| M-CHAT-R/F | 16-30m | ✅ |
| CARS2 | ≥2a | ✅ |
| ATEC | 2-12a | ✅ |
| Vineland-3 | 0-90a | ✅ |
| SNAP-IV | 6-17a | ✅ |
| SRS-2 | ≥2,5a | ✅ |
| Beck Depression | adultos | ✅ |
| PHQ-9 | adultos | ✅ |
| GAD-7 | adultos | ✅ |

**Faltam:** ABC (Aberrant Behavior), PSQI (sono), AQ (Quociente Autista), Conners (TDAH) — **Sprint 3.6 pendente** (task #41)

### 1.6 Follow-up Adaptativo ✅

- `FollowupPage` + `followup.py` (522 linhas)
- Tracking longitudinal automático
- Insights de progressão

### 1.7 Digital Twin ✅

- `TwinPage` + `twin.py` (462 linhas)
- TwinVisualizer + TwinGraph
- Cache: InMemory + Redis
- Status: funcional, evolution tracking

### 1.8 AI Integration (Funcional, parcialmente integrada)

- **AI Chat:** `AIChatPage` + `ai_chat.py`
- **AI Dashboard:** `AIDashboardPage` (`ai_management.py` 1262 linhas)
- **AI Config:** `AIConfigPage` (`ai_config.py` 541 linhas) — feature flags por tenant
- **AI Clinical:** `ai_clinical.py` (119 linhas) — resumos
- **Voice Sessions:** `voice.py` + 5 tabelas de suporte
- **Status:** funcional em produção

### 1.9 Billing + MercadoPago ✅

- `BillingPage`, `MercadoPagoPage`, `PlanosPage`
- Subscription + faturas + webhooks
- Status: funcional em produção

### 1.10 Patient Portal (Auth separada)

- `patient_auth.py` — token próprio
- `patient_portal.py` — CRUD restrito
- Páginas: `PatientLoginPage`, `PatientRegisterPage`, `PatientProductCatalog`
- Status: funcional, **isolado do JWT profissional**

## 2. AraOS Platform — Multi-tenant (Parcial)

### 2.1 Tenant Management 🟡

- `araos_organizations`, `araos_clinics`, `araos_professionals`, `araos_users`, `araos_service_accounts`
- **3 mecanismos de resolução** paralelos (Flask middleware + helpers + Platform)
- Tenant resolver Platform implementado mas não integrado
- Status: schema presente, runtime Flask **NÃO** usa

### 2.2 Identity Provider 🟡

- **Provider AraOS próprio** com claims ricos (tenant_id, roles, permissions, etc.)
- **Paraleo:** Flask-JWT-Extended ativo sem tenant_id
- Refresh token 30d apenas no AraOS provider
- Revogação em memória (não persistido)
- Status: **parcial** — código pronto, integração ausente

### 2.3 Permissions + Roles 🟡

- 106 permissions catalogadas em `permissions.py`
- 12 roles catalogados
- **ZERO aplicação em endpoints produção** (gap crítico)
- Status: catálogo pronto, aplicação ausente

### 2.4 Audit Ledger 🟡

- `araos/platform/audit/ledger.py` — hash chain SHA-256, append-only
- `AuditService.log()` disponível
- **Rotas Flask NÃO chamam** — paralelismo com LogAtividade legacy
- Status: código pronto, integração ausente

### 2.5 Event Bus 🟡

- `platform/event_bus` com publishers + consumers
- 9 contratos em `platform/contracts/`
- Integração parcial nos BCs clínicos
- Status: presente mas não aplicado cross-cutting

### 2.6 Feature Flags 🟡

- `araos_feature_flags` table
- Per-tenant scope
- `ai_config.py` flags UI
- Status: schema presente, usage parcial

## 3. AraOS Clinical (Sprints 4.x)

### 3.1 Clinical Event Engine 🟢

- **Status:** FROZEN (Sprint 3.1)
- ADR-0001 Accepted
- 189 testes
- Hash chain SHA-256
- InMemory + SQLAlchemy stores
- Domain: append/query/replay
- Application: ClinicalEventService

### 3.2 Neurodevelopmental Registry 🟢

- **Status:** FROZEN (Sprint 3.2)
- ADR-0002 Accepted
- 156 testes
- 8 entidades DDD + 6 app services
- Frontend: `NeuroRegistryPage` + `NeuroIdentityCard`

### 3.3 Conditions Catalog 🟡

- **Status:** Aceito (Sprint 3.3)
- Catálogo mais amplo de condições clínicas
- Catalog semantic IDs

### 3.4 Timeline Read Model 🟢

- **Status:** FROZEN (Sprint 4.1)
- 117 testes
- `intelligence_timeline_entries` (bitemporal)
- Frontend: `IntelligenceTimelinePage`

### 3.5 Longitudinal Phenotypes 🟡

- **Status:** Aceito (Sprint 3.5)
- Snapshot materializado

### 3.6 Clinical Context Engine 🟡

- **Status:** ADR-0003 Proposto (Sprint 4.2)
- 253 testes
- 7 states + 5 origins + 10 subtypes
- Frontend: `ClinicalContextPage` + `ClinicalContextAdminPage`
- 6 default rules + 3 projections
- 18 endpoints REST

### 3.7 Clinical Genome Engine 🟢

- **Status:** ACCEPTED (ADR-0005, Sprint 4.3)
- 88 testes
- Registry v1.0 + GeneService + ReplayEngine
- 8 endpoints REST

### 3.8 Clinical Knowledge Engine 🟡

- **Status:** Foundation Frozen (Sprint 4.4), Infrastructure Pendente (Sprint 4.5)
- **Domain congelado:** 7 módulos (ClinicalGenome + Correlation + Hypothesis + Cohort + Research + Graph + Explainability) — 313 testes Sprint 4.4.5
- **Application:** KnowledgeService + 5 services
- **Infraestrutura:**
  - ✅ `InMemoryKnowledgeRepository` (com ressalva tenant_id)
  - ✅ Mappers (lossless com ressalva em ClinicalGene)
  - ✅ Migration SQL `REDACTED` (criada)
  - ❌ `SQLKnowledgeRepository` (não implementado)
  - ❌ `KnowledgeUnitOfWork` (não implementado)
  - ❌ Zero endpoints REST `/api/knowledge/*`
  - ❌ Zero dashboard frontend
- **Gap crítico:** backend Infrastructure incompleta

### 3.9 Architecture Hardening 🟢

- **Status:** Concluído (Sprint 4.4.5)
- 313 testes finais
- AS-004 Draft 0.1 publicado
- Fix cross-tenant correlation_id leak (correlation_id inclui tenant_id agora)
- 25 invariantes catalogadas (I-01..I-25)

### 3.10 Architecture Freeze v1.0 🟢

- **Status:** FROZEN 2026-07-21
- 5 deliverables
- 7 BCs + 2 auxiliares
- 24 edges DAG
- V1/V2 deferidas

## 4. Sub-produto AraFlow (Independente, em produção)

### 4.1 AraFlow Mobile (React Native)

- Protocolos: Diaphragmatic, Box 4-4-4-4, Physiological Sigh
- 3 fases: select → session → feedback
- Clinical MVP Sprint 11 entregue
- 32 testes (100%)
- **Status:** RC1.2 DEPLOY live (https://flow.arapath.com.br) 2026-07-13

### 4.2 AraFlow Backend API (Node + shared-contracts)

- @core/runtime 1.0.0
- @core/execution-session 1.0.0
- @core/session-orchestrator 1.0.0
- @core/animation-engine 1.0.0
- @core/audio-engine 1.0.0
- @core/session-persistence 1.0.0
- @presentation/animation-renderer 1.0.0
- Status: production-ready

### 4.3 AraFlow Core (TypeScript packages)

- 9 packages NPM versionados
- 581 testes cumulativos (Sprints 0-11)
- Domain purity 100%
- Status: production-ready

## 5. Standalone Voice Service (Parcial)

### 5.1 Backend

- `voice.py` rotas
- `voice_sessions`, `voice_transcripts`, `voice_entities`, `voice_actions`, `voice_audit_logs`
- Integracao com AI
- Status: funcional

### 5.2 Frontend

- `VoiceSessionsPage` + `VoiceTranscriptPage`
- Status: visualização básica presente

## 6. Standalone Anonymization Service (Parcial)

- Container `read_only` com tmpfs
- Interface específica
- LGPD compliance
- Status: implementado mas não integrando fluxo principal

## 7. Standalone LLM Gateway

- `intelligence/` package
- CrewAI, Zhipu, Unified LLM
- Cost tracking + trust score
- Status: funcional mas parcialmente integrado

## 8. Dashboards (Parcial)

- `DashboardPage` — básico (drug interactions, top sintomas)
- `AIDashboardPage` — métricas de uso IA
- `PharmacistDashboard` — dispensação
- `AIAssistantPage`
- **Ausentes:** Knowledge Dashboard, Cohort Dashboard, Research Dashboard, Explainability Dashboard
- Status: ❌ Dashboards Knowledge (Wave 4 não entregue)

## 9. Internacionalização

- pt-BR hardcoded em frontend e backend
- **Sem i18n framework**
- Status: ❌ Bloqueador para mercados não-lusófonos

## 10. Features Onboarding + Self-service

- `OnboardingPage`
- Tour guiado de configuração
- **MFA onboarding** — modelo existe, UX ausente
- Status: funcional básico

## 11. Features Communication

- Email via SendGrid
- SMS — não implementado
- Push — React Native (AraFlow)
- Status: email funcional, SMS/push ausentes

## 12. Relatórios (Parcial)

- `HCReportPage` — relatório clínico PDF
- `ImportExportPage` — CSV/JSON
- **Ausentes:** relatórios Knowledge, correlação, cohort
- Status: cobertos parcialmente

## 13. Anonymization + LGPD

- `lgpd.py` — endpoints LGPD
- Direito de eliminação parcial
- **Anonymization service standalone** com tmpfs
- Status: tooling presente, cobertura de dados não validada

## 14. Mobile Upload

- `mobile_upload` blueprint
- `MobileUploadPage`
- Upload de fotos de receita
- Status: funcional

## 15. Resumo Quantitativo

| Categoria | Total | ✅ | 🟡 | 🔴 | 🟢 Fora Escopo |
|---|:---:|:---:|:---:|:---:|:---:|
| Legado SIAP features | ~25 | ~18 | ~5 | ~2 | — |
| AraOS Platform | 6 | 0 | 6 | 0 | — |
| AraOS Clinical BCs | 10 | 3 | 5 | 2 | — |
| Sub-produtos | 3 | 1 (AraFlow) | 2 (Voice, Anonymization) | 0 | — |
| Frontend features | 41 pages | ~30 | ~8 | ~3 | — |
| Dashboards | 4 | 1 | 1 | 2 | — |

---

**Ver também:**
- [ARAOS_SYSTEM_AUDIT.md](ARAOS_SYSTEM_AUDIT.md)
- [MODULE_DEPENDENCY_REPORT.md](MODULE_DEPENDENCY_REPORT.md)
- [MVP_GAP_ANALYSIS.md](MVP_GAP_ANALYSIS.md)
- [DEAD_CODE_REPORT.md](DEAD_CODE_REPORT.md)
