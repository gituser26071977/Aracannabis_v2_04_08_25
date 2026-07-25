# ARAOS — Executive Summary (Auditoria Pré-MVP)

**Data da auditoria:** 2026-07-22
**Diretório:** `/home/holzwarth/Projetos/Aracannabis_SO/Aracannabis_SIAP`
**Escopo:** inventário read-only do estado real do código, banco, testes, segurança, Knowledge Engine, frontend, docs e arquitetura.

---

## 1. Contexto

O AraOS é uma plataforma de inteligência clínica multi-tenant que combina um legado Flask/SIAP (cannabis medicinal, prescrições, escalas) com uma nova camada `araos/` (clinical, platform, intelligence, knowledge) sob Architecture Freeze v1.0 declarada 🟢 em 2026-07-21.

Esta auditoria foi conduzida **sem modificar código** com o objetivo de produzir 11 documentos de referência para o planejamento das próximas sprints e a tomada de decisão sobre o MVP comercial.

---

## 2. Resposta direta às perguntas do briefing

### Qual é o percentual aproximado de conclusão do AraOS?

| Dimensão | Conclusão aproximada | Evidência |
|---|---:|---|
| Legado SIAP (cannabis, pacientes, prescrições, escalas, billing) | **~75%** | 64 tabelas, 62 blueprints registrados, 41 páginas frontend, módulos funcionais em produção |
| Plataforma AraOS (tenant, identity, audit, contracts) | **~60%** | Tabelas + providers + decorators, mas baixo acoplamento ao runtime Flask |
| Clinical Event Engine (Sprint 3.1) | **100%** (frozen) | ADR-0001 Accepted, 189 testes, hash chain SHA-256, InMemory + SQLAlchemy |
| Neurodevelopmental Registry (Sprint 3.2) | **100%** (frozen) | ADR-0002 Accepted, 156 testes, 8 entidades DDD |
| Clinical Intelligence Foundations (Sprint 4.1) | **95%** | Timeline + Explainability, 117 testes |
| Clinical Context Engine (Sprint 4.2) | **90%** | ADR-0003 Em progresso, 253 testes |
| Clinical Genome Engine (Sprint 4.3) | **85%** | ADR-0005 ACCEPTED, Phase 1+2 entregues, 88 testes |
| Clinical Knowledge Engine (Sprint 4.4) | **75%** | Domain + Application + InMemory + Mappers + Migration, mas sem SQL, sem UoW, sem REST |
| Architecture Hardening (Sprint 4.4.5) | **100%** | 313 testes, AS-004 Draft, fix cross-tenant correlation |
| Architecture Freeze v1.0 | **100%** | 5 documentos, 🟢 FROZEN 2026-07-21 |
| Infrastructure Layer (Sprint 4.5) | **~25%** | Apenas Pre-Wave Gates + Migration + Mappers + ABC; falta SQLKnowledgeRepository, UoW, REST, Dashboard |

**Conclusão global aproximada: ~65%** do AraOS consolidado + ~25% de Sprint 4.5 em curso.

### O que já está pronto para uso em produção?

- ✅ **SIAP legacy** (Flask app completo, 57 blueprints, billing MercadoPago, AI integration, escalas neuro)
- ✅ **Clinical Event Engine** com hash chain
- ✅ **Neurodevelopmental Registry** (8 entidades DDD, lifecycle completo)
- ✅ **Clinical Genome Engine v1.0** (Registry versionado, GeneService, ReplayEngine)
- ✅ **InMemoryKnowledgeRepository** + migration SQL pronta (mas sem adapter SQL executável)
- ✅ **Pacote normativo** (ADR-0001..0008, AS-000/001/002, ASM-001, Architecture Freeze v1.0)

### O que ainda impede um MVP funcional?

1. **🔴 SQLKnowledgeRepository ausente** (Sprint 4.5 W1.3 não implementado)
2. **🔴 KnowledgeUnitOfWork ausente** (Sprint 4.5 W1.5 não implementado)
3. **🔴 Zero endpoints REST /api/knowledge/*** (Wave 3 não implementado)
4. **🔴 RBAC com 106 permissions catalogadas mas ZERO aplicação em endpoints** (auth_decorators.py tem só exemplos)
5. **🔴 Tenant isolation inconsistente**: 3 mecanismos divergentes (middleware Flask, helpers, resolver AraOS); middleware engole exceções
6. **🔴 Refresh token**: provider AraOS implementou, mas Flask login principal não emite
7. **🔴 MFA**: campo + evento presentes, sem implementação operacional
8. **🔴 CSRF**: helper existe, mas zero endpoints produção usam @csrf_protect
9. **🔴 Audit ledger central AraOS** não integrado às rotas Flask; LogAtividade legado é manual
10. **🟡 hypothesis_id cross-tenant leak** (manifest/code gap) — task #197 pendente
11. **🟡 ADR-0007 ausente** na sequência numérica
12. **🟡 Frontend SEM testes** (zero arquivos de teste em frontend/src/)
13. **🟡 Coverage artifacts zerados** (.coverage + coverage/coverage-final.json vazio)

### Quais funcionalidades antigas já existem e podem ser reaproveitadas?

- **Cannabis medicinal completo** (pacientes, prescrições, dosagens, evoluções, sintomas, exames)
- **Escalas neuro** (M-CHAT-R/F, CARS2, ATEC, Vineland-3, SNAP-IV, SRS-2, Beck, PHQ-9, GAD-7)
- **AI Integration** (chat, dashboard, configuração por tenant)
- **Voice service** (voice_sessions + transcripts + entities + actions + audit_logs)
- **Anonymization service** (read_only container com tmpfs)
- **Billing MercadoPago** (planos, assinaturas, faturas, webhooks)
- **Intelligent Import** (catálogo de produtos cannabis via IA)
- **Patient Portal** (login/register/dashboard separados)
- **AraFlow módulo neuroregulação** (sub-produto AraFlow com 64 docs + sprints 0–11)
- **Locust load test** + relatório de carga 2026-06

### Quais módulos devem ser descontinuados?

- **🔴 clinical.graph** (stub/experimental, models.py sem uso)
- **🔴 clinical.twin** (stub/experimental, models.py sem uso)
- **🔴 clinical.summary** (stub/experimental, engine.py sem uso)
- **🔴 clinical.projections** (legacy, engine.py)
- **🔴 IntelligentImportPage.jsx** (stub de 7 linhas no frontend)
- **🔴 neuro_pages** (NeuroScalesListPage + NeuroScaleApplyPage sem rota registrada em App.js)
- **🟡 Dockerfiles duplicados** (`Dockerfile.dockerfile` + `Dockerfile.js` idênticos)
- **🟡 ADR-0004 (Outcome Evolution Engine)** — histórico, superseded por ADR-0005
- **🟡 AraFlow ADRs 001-015** — listados no README Accepted mas SEM arquivos físicos
- **🟡 39 arquivos `test_*_debug.py/_fix.py/_simple.py` na raiz tests/** — debug/legacy candidates
- **🟡 V1/V2 violações registradas** (timeline.app → event_store.store; knowledge.domain → genome.app.ReplayEngine) — deferidas, requerem ADR-0007
- **🟡 SECRET_KEY hardcoded** em docker-compose.siap.yml (`SIAP_SECRET_REDACTED`, < 32 chars)

### Qual é o caminho mais curto até o primeiro MVP comercial?

**Trilha A — MVP Clinical Knowledge (~6 sprints de 1 semana):**
1. **Sprint 4.5 (em curso)**: completar W1.3 SQLKnowledgeRepository + W1.5 UoW + W1.7 PostgreSQL tests
2. **Sprint 4.6**: Wave 3 REST `/api/knowledge/*` (14 endpoints) + audit + permission binding
3. **Sprint 4.7**: Wave 4 Dashboard React read-only
4. **Sprint 4.8**: tenant_required decorator aplicado cross-cutting em TODOS os endpoints
5. **Sprint 4.9**: fix hypothesis_id cross-tenant (task #197) + ADR-0007
6. **Sprint 5.0**: smoke de produção + refactor de duplicações + auditoria final pré-MVP

**Trilha B — MVP SIAP legado (3 sprints):**
1. Sprint A: refactor tenant isolation (middleware + helpers consistentes)
2. Sprint B: aplicar @require_permission nos endpoints críticos (admin, AI, billing)
3. Sprint C: integrar AuditService central; corrigir CSRF; corrigir refresh token

**Recomendação:** Trilha A primeiro (Knowledge Engine é o diferencial competitivo e o que está mais próximo de finalizar); Trilha B em paralelo após MVP Knowledge.

---

## 3. Top 10 riscos arquiteturais (sem mitigação)

| # | Risco | Severidade | Evidência |
|---|---|:---:|---|
| 1 | RBAC 106 permissions NÃO aplicadas em endpoints | 🔴 Crítica | `auth_decorators.py` só tem exemplos no docstring |
| 2 | Tenant pode vir por header/body contradizendo middleware | 🔴 Crítica | `_helpers.py` + várias rotas Sprint 4 |
| 3 | SQLKnowledgeRepository não existe (W1.3 não entregue) | 🔴 Crítica | Migration criada mas sem classe executável |
| 4 | Zero REST `/api/knowledge/*` | 🔴 Crítica | Wave 3 apenas proposta |
| 5 | KnowledgeUnitOfWork ausente | 🔴 Crítica | Coordination transacional quebrada |
| 6 | hypothesis_id sem tenant_id na composição | 🟠 Alta | Code cross-tenant leak real |
| 7 | Audit ledger central AraOS não integrado a rotas | 🟠 Alta | `routes/*` gravam LogAtividade manual |
| 8 | CSRF não aplicado em produção | 🟠 Alta | Helper existe, sem uso |
| 9 | Secret hardcoded em compose | 🟠 Alta | `SIAP_SECRET_REDACTED` |
| 10 | Frontend sem testes | 🟠 Alta | 0 arquivos de teste em frontend/src/ |

---

## 4. Top 5 entregas de valor imediato

| # | Entrega | Esforço | Impacto |
|---|---|:---:|:---:|
| 1 | SQLKnowledgeRepository (mappers já prontos) | 1 sprint | 🔴 Crítica (desbloqueia Knowledge) |
| 2 | Aplicar @require_permission nos 57 blueprints | 1 sprint | 🔴 Crítica (segurança) |
| 3 | Decorator @tenant_required centralizado cross-cutting | 0.5 sprint | 🔴 Crítica (isolamento) |
| 4 | 14 endpoints REST /api/knowledge/* | 1 sprint | 🟠 Alta (feature) |
| 5 | Smoke E2E do pipeline completo | 0.5 sprint | 🟠 Alta (MVP) |

---

## 5. Sumário técnico

| Dimensão | Métrica |
|---|---|
| Total de tabelas | ~64 |
| Total de migrations | 24 |
| Total de blueprints Flask | 57 |
| Total de arquivos Python em araos/ | 330 (53k linhas) |
| Total de classes em araos/ | 549 |
| Total de ABCs | 44 |
| Total de testes (def test_*) | 1.684 |
| Total de arquivos de teste | 119 |
| Total de páginas frontend | 41 |
| Total de componentes frontend | 64 |
| Total de rotas registradas | 40 |
| Total de pages órfãs | 2 (neuro) + 1 stub (intelligent-import) |
| Total de permissions catalogadas | 106 |
| Total de roles catalogadas | 12 |
| Total de Standards AraOS | 4 (AS-000/001/002/004) + 1 metanorma (ASM-001) |
| Total de ADRs AraOS | 7 (1-6, 8; gap em 7) |
| Total de ADRs AraFlow | 14 físicos (016-029) + 15 referenciados sem arquivo |
| Architecture Freeze | 🟢 FROZEN 2026-07-21 (5 deliverables) |
| Cobertura target | ≥90% conformance, ≥95% novos |
| Cobertura real reportada | 75% Sprint 4.4, 87% Sprint 4.4.5 |
| Cobertura artifacts zerados | coverage-final.json = {} |

---

## 6. Conclusão

O AraOS tem **fundação sólida** (Clinical Event Engine, Neuro Registry, Genome Engine, Architecture Freeze v1.0) e **MVP técnico viável em 4-6 sprints** se foco for Knowledge Engine + tenant isolation + RBAC enforcement. O gargalo principal NÃO é volume de código, mas sim:

1. **Aplicar a infraestrutura normativa existente** (permissions, audit, CSRF, tenant) que está implementada como helper mas não usada nos endpoints.
2. **Concluir a camada SQL do Knowledge Engine** (W1.3 + W1.5 + W1.7).
3. **Expor REST + Dashboard** para o Knowledge Engine já construído.
4. **Refatorar inconsistências estruturais** (3 tenant isolation strategies, secret hardcoded, ARIA-0007 gap, hypothesis_id cross-tenant).

Os 11 documentos produzidos nesta auditoria fornecem o inventário factual necessário para planejar esse caminho com base em evidência, não em suposição.

---

**Próximos passos sugeridos:**
1. Revisar e aprovar prioridades com stakeholders
2. Iniciar Trilha A (MVP Knowledge) com Sprint 4.5 W1.3
3. Em paralelo, criar ADR-0007 para V1/V2 + hypothesis_id
4. Aplicar @tenant_required cross-cutting antes de qualquer REST novo
