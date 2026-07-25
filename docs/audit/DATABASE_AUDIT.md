# DATABASE_AUDIT.md — Estrutura Atual do Banco

**Data:** 2026-07-22
**Escopo:** read-only — inventário de tabelas, migrations, índices, isolamentos.
**Fonte:** `.raw-evidence-database.md`, `migrations/versions/`, `models.py`, `models_*.py`.

---

## 1. Resumo Executivo

| Métrica | Valor |
|---|---|
| Total de tabelas (estimado) | ~64 |
| Total de migrations Alembic | 24 |
| Heads Alembic | 1 (após merge G2) |
| Bancos | PostgreSQL 13 (dev) / 16 (prod/staging) |
| Tenant strategies distintas | **3** (legacy `associacao_id`, AraOS `tenant_id`, Sprint 4.5 composite PK) |
| Tabelas com FK NO ACTION | 7 (todas Sprint 4.5) |
| Soft delete | Parcial (Sprint 4.x completo; legado usa flag `ativo`) |
| Auditoria automática | Nenhuma — logAtividade manual |

## 2. Inventário de Tabelas (4 grupos)

### 2.1 Domain Core Legacy (Flask-SQLAlchemy / models.py)

Estimado 30+ tabelas:
- `pacientes`, `profissionais`, `associacoes`, `usuarios`
- `anamneses`, `consultas`, `evolucoes`, `exames`
- `sintomas`, `dosagens`, `prescricoes`, `produtos`
- `planos`, `faturas`, `mercadopago_*`
- `escalas_respostas` + tabelas por escala (M-CHAT, CARS2, ATEC, Vineland, SNAP-IV, SRS-2, Beck, PHQ-9, GAD-7)
- `ai_*` (chat, config, dashboard)
- `voice_sessions`, `voice_transcripts`, `voice_entities`, `voice_actions`, `voice_audit_logs`
- `log_atividade` (auditoria manual)
- `twin_profile`, `cannabis_profile`, `followup_*`
- `intelligent_import_*`
- `patient_portal_*`, `patient_*`

### 2.2 AraOS Platform (Sprint 7)

- `araos_organizations` — tenant raiz
- `araos_clinics` — clínicas por org
- `araos_professionals` — profissionais por org
- `araos_users` — usuários finais (pode ser profissional OU service account)
- `araos_service_accounts` — service accounts
- `araos_feature_flags` — per-tenant feature flags

### 2.3 AraOS Clinical (Sprints 3-4)

**Sprint 3.1 (Clinical Event Engine):**
- `clinical_events` — eventos append-only, hash chain SHA-256
- `clinical_event_sequences` — tracker per-tenant BIGINT sequence

**Sprint 3.2 (Neurodevelopmental Registry):**
- `neuro_registry_identities` — ClinicalIdentity AR
- `neuro_registry_diagnoses` — state machine 6 estados
- `neuro_registry_phenotypes`, `neuro_registry_assessments`, `neuro_registry_interventions`, `neuro_registry_outcomes`
- `neuro_scale_responses` — respostas brutas por escala
- `neuro_scale_interpretations` — interpretação clínica

**Sprint 4.1 (Timeline + Explainability):**
- `intelligence_timeline_entries` — bitemporal (valid_time + transaction_time)
- `intelligence_explanations` — registry de explicações

**Sprint 4.2 (Clinical Context):**
- `clinical_contexts` — AR state machine 7 estados
- `clinical_context_relationships` — 6 tipos de edge
- `clinical_context_active` — projection read-side
- `clinical_context_rules` — 6 default rules
- `clinical_context_suggestions`

**Sprint 4.3 (Clinical Genome):**
- `clinical_genes` — Registry v1.0
- `clinical_gene_versions` — versionamento seed

**Sprint 4.5 (Clinical Knowledge — migration `REDACTED`):**

> **SQL ainda não executado:** a migration existe mas `SQLKnowledgeRepository` (classe) não está implementado.

| Tabela | PK | FKs | Campos principais |
|---|---|---|---|
| `clinical_genes` | `(tenant_id, patient_id, gene_id)` | tenant_id → araos_organizations (NO ACTION) | trajectory, history, metadata (JSON) |
| `clinical_genomes` | `(tenant_id, genome_id)` | tenant_id → orgs | genes, correlations, hypotheses (JSON); state_hash, window |
| `knowledge_correlations` | `(tenant_id, correlation_id)` | tenant_id → orgs | coefficient DOUBLE PRECISION, confidence, JSON |
| `knowledge_hypotheses` | `(tenant_id, hypothesis_id)` | tenant_id → orgs | claim, rule_id, confidence, JSON |
| `knowledge_cohorts` | `(tenant_id, cohort_id)` | tenant_id → orgs | name, criteria (JSON), matched_patient_ids |
| `knowledge_research_sessions` | `(tenant_id, session_id)` | tenant_id → orgs | result_json TEXT, state_hash |
| `knowledge_graphs` | `(tenant_id, graph_id)` | tenant_id → orgs | graph_json JSONB (ADR-0008 Opção A) |

### 2.4 Voice (Sprint 7 do legado)

- `voice_sessions` — sessão por paciente
- `voice_transcripts` — transcripts raw
- `voice_entities` — entidades extraídas (NER)
- `voice_actions` — ações clínicas
- `voice_audit_logs` — trilha local

## 3. Migrations Alembic (24 arquivos)

| # | Hash | Descrição | Status |
|---|---|---|---|
| 1 | iniciais | tabelas base | ✅ |
| 2-5 | feature flags, araos_users | plataforma | ✅ |
| 6-10 | clinical, anamneses, twin | legado evolução | ✅ |
| 11-14 | escalas Beck/PHQ/GAD/SNAP/SRS/M-CHAT/CARS/ATEC/Vineland | escalas neuro | ✅ |
| 15-18 | intelligent_import, voice, AI | features | ✅ |
| 19-21 | clinical_events, neuro_registry_* | Sprint 3 | ✅ |
| 22 | `2026_07_18_clinical_context_s42` | Sprint 4.2 | ✅ |
| 23 | merge head | unificação pré-Sprint 4.5 | ✅ (G2 entregue) |
| 24 | `REDACTED` | Sprint 4.5 tabelas | ✅ (migration criada) |

### 3.1 Migration "morta" detectada

`0331305d2b3c` nomeada `add_reminder_settings_table.py` mas modifica `pacientes` (sem tabela reminder_settings) — candidata a renomeação em sprint de housekeeping.

## 4. Estratégias de Tenant Isolation

### 4.1 Legado SIAP — `associacao_id` (integer FK)

- `models.py`/`models_extra.py` — `associacao_id` INT NOT NULL FK → `associacoes.id`
- Funções `_helpers.py` recebem `associacao_id` explícito em cada query
- Filter manual em services (sem SQLAlchemy event listener)

### 4.2 AraOS Platform — `tenant_id` (string UUID)

- `araos_organizations` com `id` UUID
- Platform resolver deriva tenant do JWT
- Event listener `do_orm_execute` em `tenant_lib.py` aplica filtro automático (bypass com `execution_options(skip_tenant=True)`)

### 4.3 Sprint 4.5 — Composite PK (tenant_id + entity_id)

- 7 tabelas knowledge_* com `tenant_id` como **primeira coluna** de PK
- FKs `NO ACTION` para `araos_organizations.id` (cross-tenant safety)
- Sem CASCADE — clinical data não pode cascadear

### 4.4 Coexistência — Problema Documentado

3 mecanismos paralelos:
- `tenant_middleware.py` (Flask) — tenant EXCLUSIVO do JWT
- `_helpers.py` (Sprint 4) — aceita X-Association-ID > X-Tenant-ID > JWT
- Platform resolver — JWT/API key/service account

Risco: tenant via header contradiz o middleware Flask.

## 5. Índices e Performance

### 5.1 Índices catalogados (Sprint 4.5)

- `ix_<table>_tenant_state_hash (tenant_id, state_hash)` — replay verification
- `ix_<table>_tenant_patient (tenant_id, patient_id)` — cohort/graph queries
- `ix_<table>_tenant_built_at (tenant_id, built_at DESC)` — list ordering

### 5.2 Problemas de indexação observáveis

- `clinical_events`: index simples em `tenant_id, aggregate_id` — projection rebuild pode ser lento
- `clinical_event_sequences`: BIGINT per-tenant — sem índice composto em `(tenant_id, sequence)`
- `neuro_scale_responses`: filtro típico `(patient_id, scale_id)` sem composite

## 6. Soft Delete

| Camada | Padrão |
|---|---|
| Legacy SIAP | flag `ativo` boolean (sem timestamp) |
| AraOS Platform | `deleted_at TIMESTAMPTZ NULL` (não aplicado) |
| Clinical Sprint 4.x | `deleted_at TIMESTAMPTZ NULL` aplicado consistentemente |
| Knowledge Sprint 4.5 | `deleted_at TIMESTAMPTZ NULL` (default behavior: `WHERE deleted_at IS NULL`) |

LGPD: `clinical_event_store` + `neuro_registry` têm trilha de audit associada; plataformas SIAP legacy têm apenas `log_atividade` manual.

## 7. Compatibilidade PostgreSQL/SQLite

- Alembic aponta `postgresql+psycopg2` em prod, `sqlite:///` em test/dev
- Testes unitários rodam SQLite (sem time zone aware)
- Testes integração Sprint 4.5 planejados PostgreSQL 16 (gate)
- JSONB somente PostgreSQL (SQLite JSON funciona mas sem performance)

## 8. Auditoria (Audit Log)

| Sistema | Tabela | Padrão | Status |
|---|---|---|---|
| Legacy SIAP | `log_atividade` | INSERT manual em rotas | 🟠 funcionando |
| AraOS Platform | `araos_audit_ledger` (esperado) | hash chain SHA-256 | 🔴 implementado em código mas NÃO conectado a rotas |
| Clinical | `clinical_events` (event sourcing) | hash chain | 🟢 ativo |
| Voice | `voice_audit_logs` | INSERT manual | 🟠 ativo |

## 9. Constraints e Integridade

### 9.1 Foreign Keys

- Legacy: CASCADE padrão
- Sprint 4.5: **NO ACTION** explícito (LGPD/audit)
- Composite PKs garantem unicidade tenant-scoped

### 9.2 Check Constraints

- Coefficient correlation: `coefficient ∈ [-1, 1]` (validação Python, sem CHECK SQL)
- Confidence: `[0, 1]`
- Hypothesis claim: NOT NULL

### 9.3 Unique Constraints

- IDs content-derived via SHA-256 de payload canônico
- Composite PKs garantem (tenant, entity_id) únicos

## 10. Riscos Estruturais

1. **3 tenant isolation strategies** sem adapter unificado
2. **Migration 0331305d2b3c dead** (filename vs conteúdo divergente)
3. **NO ACTION FKs** podem quebrar deleção de organização se LGPD exigir
4. **JSONB vs TEXT** decision (research_session usa TEXT para bit-identical — ADR-0008 não aplicável aqui)
5. **SQLite vs PostgreSQL** drift em timestamps e JSON
6. **Zero audit automático** nas rotas Flask

---

**Ver também:**
- [ARAOS_SYSTEM_AUDIT.md](ARAOS_SYSTEM_AUDIT.md)
- [SECURITY_AUDIT.md](SECURITY_AUDIT.md)
- [MODULE_DEPENDENCY_REPORT.md](MODULE_DEPENDENCY_REPORT.md)
