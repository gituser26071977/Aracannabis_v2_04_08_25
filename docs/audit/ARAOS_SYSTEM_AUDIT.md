# ARAOS_SYSTEM_AUDIT.md — Visão Geral Completa do Sistema

**Data:** 2026-07-22
**Escopo:** inventário read-only, sem modificação de código.

---

## 1. Identidade do Sistema

- **Nome:** AraOS (Aracannabis Operating System)
- **Versão:** v0.8.0-alpha (araos/__init__.py)
- **Versão SIAP legado:** v1.0.0-rc.1 (RELEASE_MANIFEST.md, 2026-06-28)
- **Versão SIAP em produção:** v2.1.0 (CHANGELOG.md, set/2025)
- **Sub-produto AraFlow:** módulo de neuroregulação digital (64 documentos em docs/AraFlow/)

## 2. Stack Tecnológico

### Backend
- **Python 3.12-3.14** (venv múltiplos)
- **Flask + Flask-SQLAlchemy** (legado SIAP)
- **SQLAlchemy 2.0 declarative** (AraOS Platform)
- **Alembic** (24 migrations)
- **flask-jwt-extended** (auth Flask)
- **PyJWT** (provider AraOS próprio)
- **Flask-Limiter** (rate limit)
- **bcrypt ausente** — usa PBKDF2-SHA256 100k via Werkzeug
- **Locust** (load test)
- **Hypothesis** (property-based testing)

### Frontend
- **React 18.2** + React Router DOM 6.22
- **Material UI 5.15** + Emotion 11.11
- **Axios 1.6**
- **Chart.js 4.4**, Recharts 2.15, FullCalendar 6.1
- **MUI X Date Pickers 8.4**, date-fns, Moment
- **react-dropzone 14.2**
- **Create React App 5.0.1** (NÃO Vite/Next.js)

### Banco de Dados
- **PostgreSQL 13** (dev compose) / **PostgreSQL 16** (prod/staging)
- **Redis 7** (prod/staging)
- **~64 tabelas** físicas totais

### Infraestrutura
- **Docker** (9 Dockerfiles, 7 docker-compose files)
- **Traefik** (proxy prod)
- **Prometheus + Alertmanager** (monitoring)
- **GitHub Actions** (6 workflows)
- **ARAOS Systemd unit** (araos.service)
- **Nginx** (nginx.conf + nginx_arapath_cf.conf)

## 3. Estrutura Geral

```
/home/holzwarth/Projetos/Aracannabis_SO/Aracannabis_SIAP/
├── araos/                    # Nova plataforma (330 .py, 53k linhas, 549 classes, 44 ABCs)
│   ├── agents/               # Runtime de agentes (registry, executor, workflows)
│   ├── clinical/             # Inteligência clínica (Sprints 3-4)
│   ├── demo/                 # Flows de demo
│   ├── followup/             # Acompanhamento longitudinal
│   ├── integration/          # Adapters cross-system
│   ├── intelligence/         # LLM, embeddings, vector stores
│   ├── knowledge/            # Knowledge base retrieval
│   ├── platform/             # Multi-tenant, identity, audit, contracts, event_bus
│   └── specialties/          # Framework de especialidades (cannabis, neuro, core)
├── association/              # Multi-tenant legado
├── frontend/                 # React app (41 pages, 64 components, 0 tests)
├── migrations/               # 24 Alembic migrations
├── models.py                 # Legacy Flask-SQLAlchemy (1791 linhas, 31 classes)
├── models_*.py               # Legacy extensions (extra, modulos, produto, ai, ai_compliance)
├── routes/                   # 62 Flask blueprints (20.574 linhas)
├── services/                 # 77 serviços de aplicação legados
├── scripts/                  # 30 scripts deploy/backup/smoke
├── tests/                    # 119 test files, 1684 def test_*
├── tools/araflow-cli/        # CLI AraFlow
├── docs/                     # Documentação (ADR, AS, ASM, sprints, AraFlow)
└── backend/                  # AraFlow API + Web Dockerfile
```

## 4. Domínios Funcionais (Bounded Contexts)

### 4.1 Legado SIAP (em produção desde 2025)
- **Auth profissionais + pacientes** (Flask-JWT-Extended)
- **Pacientes, Consultas, Evoluções, Sintomas, Dosagens, Prescrições, Exames**
- **Anamnese, Acompanhamento (Followup), Twin (Digital Twin), Cannabis Profile**
- **Escalas neuro (M-CHAT-R/F, CARS2, ATEC, Vineland-3, SNAP-IV, SRS-2, Beck, PHQ-9, GAD-7)**
- **Produtos, Catálogo, Billing MercadoPago**
- **AI Integration (chat, dashboard, config)**
- **Voice Sessions + Transcription**
- **Associação + Members + Stock + Dispensation**

### 4.2 AraOS Clinical (Sprints 3.x, 4.x)
- **Clinical Event Engine** (Sprint 3.1 — ADR-0001 ✅) — Event Sourcing + CQRS
- **Neurodevelopmental Registry** (Sprint 3.2 — ADR-0002 ✅) — 8 entidades DDD
- **Conditions Catalog** (Sprint 3.3) — broader clinical catalog
- **Timeline Read Model** (Sprint 3.4) — consume Event Store
- **Longitudinal Phenotypes** (Sprint 3.5) — snapshot materializado
- **Timeline + Explainability Foundations** (Sprint 4.1) — 117 testes
- **Clinical Context Engine** (Sprint 4.2 — ADR-0003 Em progresso) — 253 testes
- **Clinical Genome Engine** (Sprint 4.3 — ADR-0005 ACCEPTED) — 88 testes
- **Clinical Knowledge Engine** (Sprint 4.4 — Foundation Freeze) — 75% cobertura, 313 testes (Sprint 4.4.5)
- **Infrastructure Layer** (Sprint 4.5 — em curso) — Pre-Wave Gates + Migration + Mappers

### 4.3 AraOS Platform
- **Tenant (araos_organizations, araos_clinics, araos_professionals, araos_users, araos_service_accounts)**
- **Identity (JWT provider AraOS próprio com claims ricos, roles, permissions, refresh)**
- **Audit Ledger** (hash chain SHA-256, append-only)
- **Event Bus** (publishers, consumers)
- **Feature Flags** (per-tenant)
- **Contracts** (ABCs para 9 providers + 4 APIs)

### 4.4 Sub-produtos
- **AraFlow** (neuroregulação digital — React Native + Node + shared-contracts)
- **Voice Service** (voice_sessions + transcripts + entities + actions + audit)
- **Anonymization Service** (read_only container)
- **LLM Gateway** (CrewAI, Zhipu, Unified LLM)

## 5. Métricas de Maturidade

| Componente | Maturidade | Evidência |
|---|---|---|
| Architecture Freeze v1.0 | 🟢 FROZEN (2026-07-21) | 5 deliverables publicados |
| Foundation Freeze (AS-000/001/002, ASM-001, ADR-0001..0006) | 🟢 Ativo | Declaração em ADR-0006 |
| Clinical Event Engine | 🟢 Aceito | ADR-0001, 189 testes |
| Neurodevelopmental Registry | 🟢 Aceito | ADR-0002, 156 testes |
| Clinical Genome Engine | 🟢 Aceito | ADR-0005, 88 testes |
| Clinical Context Engine | 🟡 Em progresso | ADR-0003, 253 testes |
| Clinical Knowledge Engine (Sprint 4.4) | 🟡 Domain frozen, infra parcial | 313 testes Sprint 4.4.5 |
| Architecture Hardening (Sprint 4.4.5) | 🟢 Concluído | AS-004 Draft 0.1, fix cross-tenant |
| Infrastructure Layer (Sprint 4.5) | 🟡 W1.1 + G1-G5 done, W1.3+ pending | mappers.py + migration + ABC prontos; SQL repo + UoW + REST ausentes |
| Tenant Isolation | 🟠 Divergente | 3 estratégias simultâneas |
| RBAC | 🟠 Defasado | 106 permissions, 0 aplicadas |
| Frontend tests | 🔴 Ausente | 0 arquivos de teste |

## 6. Banco de Dados

- **64 tabelas** em 4 categorias:
  - **Domain Core Legacy** (models.py): pacientes, profissionais, anamneses, sintomas, dosagens, prescricoes, evolucoes, consultas, exames, produtos, planos, etc.
  - **AraOS Platform** (Sprint 7): araos_organizations, araos_clinics, araos_professionals, araos_users, araos_service_accounts, araos_feature_flags
  - **AraOS Clinical** (Sprint 4.x): clinical_events, clinical_event_sequences, neuro_scale_responses, neuro_registry_*, intelligence_*, clinical_context*, clinical_genes, clinical_genomes, knowledge_*
  - **Voice** (Sprint 7): voice_sessions, voice_transcripts, voice_entities, voice_actions, voice_audit_logs
- **3 estratégias de tenant isolation**:
  - `associacao_id` (legacy SIAP, integer FK)
  - `tenant_id` (AraOS, string UUID)
  - Composite PK com tenant_id (Sprint 4.5 — NO ACTION FK)
- **24 migrations** com 2 merge heads resolvidos
- **NO ACTION FKs**: apenas nas 7 tabelas Sprint 4.5 (cross-tenant safety)
- **Soft delete** completo apenas em tabelas Sprint 4.x (clinical_events, neuro_registry, knowledge_*); legado usa flag `ativo`

## 7. Frontend

- **React 18.2** SPA com 41 páginas e 64 componentes (13.562 linhas de páginas)
- **CRA 5.0.1** (legado) — não migrado para Vite/Next.js
- **3 Contexts** (Auth, Association, Theme) — sem Redux
- **40 rotas registradas** em App.js (algumas páginas órfãs: NeuroScaleList/Apply)
- **Axios central** com JWT injetado + CSRF + tenant header (X-Association-ID)
- **SEM refresh automático** no cliente central
- **SEM testes frontend** (0 arquivos)

## 8. Segurança (resumo)

- **PBKDF2-SHA256 100k** (Werkzeug) — bcrypt ausente
- **JWT**: Flask emite apenas access 12h SEM tenant_id; provider AraOS emite access + refresh com claims ricos (mas não integrado)
- **RBAC**: 106 permissions catalogadas, 12 roles, ZERO aplicação em endpoints (só exemplos no decorator docstring)
- **Tenant isolation**: 3 mecanismos divergentes (middleware engole exceções, helpers aceitam header)
- **CSRF**: helper existe, ZERO aplicação em produção
- **Audit**: ledger central AraOS existe mas LogAtividade legado prevalece
- **Rate limit**: Flask-Limiter aplicado em auth
- **CORS**: 14 origens allowlist (sem wildcard)

## 9. Documentação

- **Foundation Freeze**: AS-000/001/002, ASM-001, ADR-0001..0006
- **ADRs Aceitos**: 0001 (Event Engine), 0002 (Identity), 0005 (Genome)
- **ADRs Propostos**: 0003 (Context), 0004 (Outcome — histórico), 0006 (Normative Conflict Resolution), 0008 (Materialized Graph)
- **ADRs Draft**: AS-000, AS-002, ASM-001
- **Standards Published**: AS-001 (Clinical Gene)
- **Architecture Freeze**: 5 documentos (Baseline, DependencyMap, PublicAPI, BoundaryValidation, Report)
- **Sprint Reports**: 3.x, 4.1, 4.2, 4.3, 4.4, 4.4.5 completos
- **AraFlow docs**: 64 documentos (sub-produto independente)

## 10. CI/CD

- **6 GitHub Actions**: ci.yml, cd-production.yml, cd-staging.yml, cd-araflow.yml, lighthouse.yml, make-public.yml
- **Pipelines**: lint+typecheck+test, build GHCR, deploy com auto-rollback
- **SEM Makefile**, SEM pyproject.toml, SEM setup.py, SEM .gitlab-ci.yml

## 11. Cobertura de Testes

- **119 test files, 1.684 funções def test_***
- **Distribution**:
  - clinical_event_store: 189
  - intel_sprint_4_2: 253
  - sprint_4_4_5: 176
  - neurodev_sprint_3_2: 156
  - neuro_sprint1: 128
  - intel_sprint_4_1: 117
  - sprint_4_4: 94
  - intel_sprint_4_3: 88
  - neuro_sprint2: 60
  - genome_sprint_4_3_phase_2/conformance: 43
  - security: 31
  - raiz: 332 (mixed debug+active)
  - e2e: 16 (Playwright)
- **Coverage artifacts zerados**: coverage/coverage-final.json = {}
- **Target declarado**: ≥90% conformance, ≥95% novos
- **Reportado**: Sprint 4.4 = 75%, Sprint 4.4.5 = 87%
- **SEM tests frontend**

## 12. Estado de Produção

- **AraFlow RC1** deploy ativo em https://flow.arapath.com.br (2026-07-13)
- **SIAP produção** ativo (v2.1.0, set/2025)
- **AraOS** em desenvolvimento (não production-ready)

---

**Ver também:**
- [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
- [FEATURE_INVENTORY.md](FEATURE_INVENTORY.md)
- [MODULE_DEPENDENCY_REPORT.md](MODULE_DEPENDENCY_REPORT.md)
- [BACKEND_AUDIT.md](BACKEND_AUDIT.md)
- [FRONTEND_AUDIT.md](FRONTEND_AUDIT.md)
- [DATABASE_AUDIT.md](DATABASE_AUDIT.md)
- [SECURITY_AUDIT.md](SECURITY_AUDIT.md)
- [KNOWLEDGE_ENGINE_AUDIT.md](KNOWLEDGE_ENGINE_AUDIT.md)
- [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md)
- [DEAD_CODE_REPORT.md](DEAD_CODE_REPORT.md)
- [MVP_GAP_ANALYSIS.md](MVP_GAP_ANALYSIS.md)
