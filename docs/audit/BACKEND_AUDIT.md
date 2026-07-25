# BACKEND_AUDIT.md — Endpoints, Services, DTOs e Integração

**Data:** 2026-07-22
**Escopo:** read-only — inventário da camada de aplicação Python.
**Fonte:** `.raw-evidence-backend.md`, `routes/*`, `araos/clinical/*`, `app_cors_livre.py`.

---

## 1. Resumo Executivo

| Métrica | Valor |
|---|---|
| Total blueprints Flask | **57** (registrados em `app_cors_livre.py`) |
| Total arquivos de rota | **62** (20.574 linhas) |
| Total services (legado) | **77** |
| Total arquivos Python em `araos/` | **330** (53.005 linhas) |
| Total classes em `araos/` | **549** |
| Total ABCs | **44** |
| Permission decorators aplicados em produção | **0** endpoints |
| Tenant required central | Não existe (3 mecanismos divergentes) |

## 2. Top Maiores Blueprints (top 20 por linhas)

| Blueprint | Linhas | Função |
|---|---:|---|
| ai_management.py | 1262 | Gestão de IA por tenant |
| pacientes.py | 910 | CRUD pacientes |
| neuro_registry.py | 786 | Registry neuro (Sprint 3.2) |
| clinical_context.py | 744 | Contexto clínico (Sprint 4.2) |
| import_export.py | 659 | Import/export CSV/JSON |
| admin.py | 626 | Painel admin |
| catalogo_routes.py | 621 | Catálogo produtos cannabis |
| sdr.py | 617 | SDR agent |
| exames.py | 607 | Exames clínicos |
| evolucoes.py | 585 | Evoluções SOAP |
| intelligent_import.py | 573 | Import inteligente (IA) |
| sintomas.py | 572 | Sintomas por paciente |
| cannabis.py | 548 | Módulo cannabis medicinal |
| ai_config.py | 541 | Config IA por tenant |
| followup.py | 522 | Follow-up automático |
| modulos.py | 483 | Módulos clinic (legacy) |
| auth_decorators.py | 468 | Decoration de auth (RBAC, MFA) |
| patient_import_agent.py | 468 | Import agente paciente |
| crew_ai.py | 465 | CrewAI orchestration |
| twin.py | 462 | Digital Twin |

## 3. Application Services AraOS Clinical

### 3.1 Sprint 3.2 — Neurodevelopmental

- `ClinicalIdentityService` (registry + lookup)
- `AssessmentService`
- `DiagnosisService`
- `PhenotypeService`
- `InterventionService`
- `OutcomeService`

### 3.2 Sprint 4.1 — Timeline + Explainability

- `TimelineQuery.for_patient(tenant_id, patient_id, window) → TimelineEntry[]`
- `TimelineQuery.for_aggregate(tenant_id, aggregate_type, aggregate_id)`
- `ExplanationRegistry.register(explanation)` + `get(explanation_id)`

### 3.3 Sprint 4.2 — Context Engine

- `ClinicalContextService.create / activate / close / reopen / reject / confirm_suggestion / update / link / unlink`
- `ClinicalContextQuery.for_patient, get, active_at, co_occurred, influenced_outcome, preceded_improvement, active_during`
- `RuleEngine.register, rules, evaluate`
- `ContextSuggester.suggest`
- 6 BuiltinRules: `MedicationStart`, `SchoolTransition`, `FamilyEngagement`, `CrisisEpisode`, `BehavioralCrisis`, `SleepPattern`

### 3.4 Sprint 4.3 — Genome Engine

- `GeneService` — Registry v1.0 (seed versionado)
- `GeneRegistryService`
- `ReplayEngine.replay / replay_from_snapshot / _apply_event`

### 3.5 Sprint 4.4 — Knowledge Engine

- `KnowledgeService.build_genome_from_genes`
- `KnowledgeService.build_genome_from_events`
- `KnowledgeService.compute_correlations / compute_all_correlations`
- `KnowledgeService.generate_hypotheses`
- `KnowledgeService.build_graph`
- `KnowledgeService.run_pipeline`
- `CohortService` (11-22), `CorrelationService` (12-31), `HypothesisService` (13-19), `GraphService` (14-24), `ResearchService` (19-59)
- `KnowledgePipelineResult` DTO

## 4. Authorization (RBAC)

### 4.1 Permissions Catalogadas

- **106 permissions** em `araos/platform/identity/permissions.py`
- **27 prefixos**: `ai`, `allergy`, `billing`, `clinic`, `communication`, `consultation`, `dashboard`, `diagnosis`, `document`, `evolution`, `exam`, `explainability`, `feature_flag`, `intelligence`, `lgpd`, `medication`, `ml`, `neurodevelopmental`, `patient`, `platform`, `prescription`, `professional`, `research`, `smart_flow`, `subscription`, `user`, `voice`

### 4.2 Roles Catalogados

**12 roles** (constantes): `admin`, `physician`, `secretary`, `manager`, `patient`, `agent`, `service_account`, `viewer`, `neuro_physician`, `health_secretary`, `scientific_producer`, `intelligence_curator`

### 4.3 Decorators Disponíveis

- `@require_permission(Permission.X)` em `routes/auth_decorators.py`
- `@require_staff_role`
- `@require_roles(*roles)`
- `@require_tenant` em `tenant/middleware.py`

### 4.4 Aplicação Real (gap crítico)

**ZERO** endpoints produção usam `@require_permission` — confirmando por busca textual:
- Presente apenas em exemplos dentro do docstring de `auth_decorators.py`
- Existe em `tests/security/test_p0_remediation_m18.py`

Endpoints usam só `@jwt_required()` + verificações manuais.

## 5. Tenant Handling

### 5.1 Middleware Flask (`tenant_middleware.py`)

- Tenant derivado EXCLUSIVO do vínculo do usuário autenticado
- Engole exceções (registrado em `.raw-evidence-security.md`)

### 5.2 Helpers Sprint 4 (`_helpers.py`)

- Prioridade: `X-Association-ID` > `X-Tenant-ID` > `tenant_id` na identity JWT
- Conflita com middleware Flask (segundo mecanismo)

### 5.3 Platform Resolver (`platform/tenant/*`)

- JWT/API key/service account/X-Tenant-ID

### 5.4 Filtro SQLAlchemy Automático

- `tenant_lib.py` via `do_orm_execute` + `before_flush`
- Bypass: `execution_options(skip_tenant=True)` ou `g.is_superadmin`

### 5.5 Filtragem Explícita

- Presente em admin.py, pharmacy.py, followup.py, cannabis.py, twin.py, audit/ledger.py

**Inconsistência central:** middleware engole exceções + helpers aceitam header contradizendo o middleware + login Flask não emite tenant_id.

## 6. Auth Decorators (`auth_decorators.py`)

468 linhas. Implementa:
- `@require_staff_role`
- `@require_roles(*roles)`
- `@require_permission`
- `@require_patient_role`
- `@validate_json`
- `@log_endpoint`
- `@tenant_required` (NÃO existe como decorador dedicado; existe em middleware)

**Documentação interna** menciona o uso correto de `@require_permission`, mas a auditoria confirma que nenhum endpoint o aplica em produção.

## 7. AI Integration Routes

### 7.1 `ai_management.py` (1262 linhas)

- CRUD modelos IA por tenant
- Logging de chamadas
- Config de fallback (openai → zhipuai)

### 7.2 `ai_config.py` (541 linhas)

- `config_ia_tenant` — feature flags de IA por tenant

### 7.3 `ai_chat_simples.py` (296 linhas)

- Chat contextual simples

### 7.4 `ai_clinical.py` (119 linhas)

- Resumos clínicos (clinical/summary legacy)

### 7.5 `intelligence_timeline.py` (224 linhas)

- Timeline Sprint 4.1 REST endpoints

## 8. Voice Endpoints (`routes/voice.py`)

- 126 linhas
- Gerencia sessões, transcripts, entities, actions
- Audit via `voice_audit_logs` (manual)

## 9. Explainability Endpoints

- `routes/explainability.py` (173 linhas)
- 7 endpoints Sprint 4.1
- Composição de explicações cross-cutting

## 10. Clinical Context Endpoints

- `routes/clinical_context.py` (744 linhas)
- Implementa CRUD + state transitions
- Permission check via JWT, sem `@require_permission`

## 11. Inconsistências / Riscos Backend

1. **@require_permission nunca aplicado** — brecha de segurança confirmada
2. **3 tenant mechanisms** paralelos
3. **Audit central AraOS NÃO conectado** — rotas Flask gravam LogAtividade manual
4. **CSRF @csrf_protect nunca aplicado** — helper existe
5. **rate_limit aplicado em IA** mas não em endpoints Knowledge
6. **AraOS providers não usados em produção Flask** — paralelismo
7. **JWT Flask emite SEM tenant_id** — Platform provider AraOS emite com claims ricos mas não é o caminho ativo
8. **MFA apenas modelo, sem OTP/TOTP/recovery** operacional
9. **V1/V2 violações** registradas — ADR-0007 pendente
10. **Migration 0331305d2b3c dead** confirmada
11. **Knowledge REST = 0 endpoints** — Wave 3 não entregue

---

**Ver também:**
- [ARAOS_SYSTEM_AUDIT.md](ARAOS_SYSTEM_AUDIT.md)
- [SECURITY_AUDIT.md](SECURITY_AUDIT.md)
- [MODULE_DEPENDENCY_REPORT.md](MODULE_DEPENDENCY_REPORT.md)
- [FRONTEND_AUDIT.md](FRONTEND_AUDIT.md)
