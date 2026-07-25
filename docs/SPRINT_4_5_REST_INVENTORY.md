# Sprint 4.5 — REST Endpoint Inventory + Authorization Matrix

**Status:** 📋 Proposed (G5 — Pre-Wave Governance Gate)
**Data:** 2026-07-22
**Sprint:** 4.5 (Infrastructure Layer)
**Conformidade:** Architecture Freeze v1.0 · Foundation Freeze · AS-001..002 · ADR-0006

---

## 1. Propósito

Este documento é o **inventário canônico** dos endpoints REST que
Sprint 4.5 Wave 3 implementará em `interfaces/rest/`. É publicado
**antes** da implementação (G5) para:

1. **Congelar paths** — prevenir conflitos com rotas legacy em `routes/`.
2. **Congelar permission mapping** — usar apenas permissions já existentes
   (sem criar redundantes — diretriz do usuário).
3. **Congelar tenant source** — todo endpoint deriva `tenant_id` do JWT
   validado, nunca de path/query/body sem validação.
4. **Pré-validar DTOs** — contratos de request/response antes do código.

Qualquer endpoint não listado aqui **NÃO será implementado** sem
atualizar este documento primeiro.

---

## 2. Princípios de Design

### 2.1 Tenant Isolation

| Princípio | Aplicação |
|---|---|
| Tenant SEMPRE de JWT | `g.tenant_id` populado por `@tenant_required` decorator (W3.1) |
| Tenant NUNCA de path | Não usar `/api/knowledge/<tenant_id>/...` |
| Tenant NUNCA de query | `?tenant_id=...` é IGNORADO se enviado |
| Tenant NUNCA de body | Validar contra JWT se cliente enviar |
| Mismatch → 404 (não 403) | Não vaza existência de outro tenant |

### 2.2 Permission Mapping

**REGRA:** usar apenas permissions já existentes em
`araos/platform/identity/permissions.py`. **Não criar novas.**

Justificativa: ADR-0006 proíbe criação de standards/redundâncias
sem processo formal. Permissions redundantes quebram auditoria.

### 2.3 Response Codes

| Code | Significado |
|---|---|
| 200 | OK (read) |
| 201 | Created (POST com sucesso) |
| 204 | No content (DELETE com sucesso) |
| 400 | Validation error (payload malformado) |
| 401 | Missing/invalid JWT |
| 403 | Permission denied (JWT válido, falta permission) |
| 404 | Not found **OR** cross-tenant mismatch (não distinguir) |
| 409 | Conflict (state inválido para operação) |
| 500 | Server error (logado + audit) |

### 2.4 Audit Log

Todo endpoint chama `audit(action, resource, outcome, **meta)` após
response. Audit failure **NÃO bloqueia** response (best-effort).

---

## 3. Endpoint Inventory

### 3.1 Genome — `/api/knowledge/genomes`

| Method | Path | Permission | Tenant Source | Request DTO | Response DTO |
|---|---|---|---|---|---|
| `GET` | `/api/knowledge/genomes` | `INTELLIGENCE_CORRELATION_READ` | JWT | `?patient_id` (opcional) | `GenomesListResponse` |
| `GET` | `/api/knowledge/genomes/<genome_id>` | `INTELLIGENCE_CORRELATION_READ` | JWT | — | `GenomeResponse` |

### 3.2 Correlations — `/api/knowledge/correlations`

| Method | Path | Permission | Tenant Source | Request DTO | Response DTO |
|---|---|---|---|---|---|
| `GET` | `/api/knowledge/correlations` | `INTELLIGENCE_CORRELATION_READ` | JWT | `?genome_id` (opcional) | `CorrelationsListResponse` |
| `GET` | `/api/knowledge/correlations/<correlation_id>` | `INTELLIGENCE_CORRELATION_READ` | JWT | — | `CorrelationResponse` |
| `POST` | `/api/knowledge/correlations/compute` | `INTELLIGENCE_CORRELATION_COMPUTE` | JWT | `CorrelationComputeRequest` | `CorrelationComputeResponse` |

### 3.3 Hypotheses — `/api/knowledge/hypotheses`

| Method | Path | Permission | Tenant Source | Request DTO | Response DTO |
|---|---|---|---|---|---|
| `GET` | `/api/knowledge/hypotheses` | `INTELLIGENCE_CORRELATION_READ` | JWT | `?genome_id` (opcional) | `HypothesesListResponse` |
| `GET` | `/api/knowledge/hypotheses/<hypothesis_id>` | `INTELLIGENCE_CORRELATION_READ` | JWT | — | `HypothesisResponse` |

### 3.4 Cohorts — `/api/knowledge/cohorts`

| Method | Path | Permission | Tenant Source | Request DTO | Response DTO |
|---|---|---|---|---|---|
| `GET` | `/api/knowledge/cohorts` | `INTELLIGENCE_COHORT_READ` | JWT | — | `CohortsListResponse` |
| `GET` | `/api/knowledge/cohorts/<cohort_id>` | `INTELLIGENCE_COHORT_READ` | JWT | — | `CohortResponse` |
| `POST` | `/api/knowledge/cohorts` | `INTELLIGENCE_COHORT_DEFINE` | JWT | `CohortDefineRequest` | `CohortResponse` |

### 3.5 Knowledge Graphs — `/api/knowledge/graphs`

| Method | Path | Permission | Tenant Source | Request DTO | Response DTO |
|---|---|---|---|---|---|
| `GET` | `/api/knowledge/graphs` | `INTELLIGENCE_CORRELATION_READ` | JWT | `?patient_id` (opcional) | `GraphsListResponse` |
| `GET` | `/api/knowledge/graphs/<graph_id>` | `INTELLIGENCE_CORRELATION_READ` | JWT | — | `GraphResponse` (nodes + edges JSON) |

### 3.6 Research Sessions — `/api/knowledge/research`

| Method | Path | Permission | Tenant Source | Request DTO | Response DTO |
|---|---|---|---|---|---|
| `GET` | `/api/knowledge/research/sessions` | `INTELLIGENCE_ANALYTICS_READ` | JWT | — | `SessionsListResponse` |
| `GET` | `/api/knowledge/research/sessions/<session_id>` | `INTELLIGENCE_ANALYTICS_READ` | JWT | — | `SessionResponse` |
| `POST` | `/api/knowledge/research/execute` | `INTELLIGENCE_CORRELATION_COMPUTE` | JWT | `ResearchExecuteRequest` | `SessionResponse` |

### 3.7 Replay — `/api/knowledge/replay`

| Method | Path | Permission | Tenant Source | Request DTO | Response DTO |
|---|---|---|---|---|---|
| `POST` | `/api/knowledge/replay` | `INTELLIGENCE_CORRELATION_COMPUTE` | JWT | `ReplayRequest` | `ReplayResponse` |

**ReplayRequest** MUST incluir `events` (event payload) e `expected_state_hash`.
**ReplayResponse** MUST retornar `replayed_state_hash` + boolean `byte_identical`.

### 3.8 Explainability — `/api/knowledge/explanations`

| Method | Path | Permission | Tenant Source | Request DTO | Response DTO |
|---|---|---|---|---|---|
| `GET` | `/api/knowledge/explanations/<explanation_id>` | `EXPLAINABILITY_READ` | JWT | — | `ExplanationResponse` |

### 3.9 Events — `/api/knowledge/events`

| Method | Path | Permission | Tenant Source | Request DTO | Response DTO |
|---|---|---|---|---|---|
| `GET` | `/api/knowledge/events` | `INTELLIGENCE_TIMELINE_READ` | JWT | `?patient_id`, `?from`, `?to` | `EventsListResponse` |

---

## 4. DTO Contracts

### 4.1 GenomeResponse

```python
@dataclass(frozen=True)
class GenomeResponse:
    genome_id: str
    tenant_id: str
    patient_id: str
    window_start: str   # ISO8601
    window_end: str     # ISO8601
    window_label: str
    state_hash: str
    built_at: str       # ISO8601
    correlation_count: int    # NOT counts only — list of IDs (lossless)
    correlation_ids: tuple[str, ...]
    hypothesis_count: int
    hypothesis_ids: tuple[str, ...]
    gene_count: int
    gene_ids: tuple[str, ...]
```

### 4.2 CorrelationResponse

```python
@dataclass(frozen=True)
class CorrelationResponse:
    correlation_id: str
    tenant_id: str
    method: str
    gene_x_id: str
    gene_y_id: str
    window_start: str
    window_end: str
    coefficient: float
    p_value: float | None
    state_hash: str
```

### 4.3 CohortDefineRequest

```python
@dataclass(frozen=True)
class CohortDefineRequest:
    name: str
    criteria: tuple[CriterionRequest, ...]

@dataclass(frozen=True)
class CriterionRequest:
    field: str
    operator: str  # "eq" | "gt" | "lt" | "in" | "contains"
    value: str | int | float | bool | list[str]
```

### 4.4 ReplayRequest

```python
@dataclass(frozen=True)
class ReplayRequest:
    events: tuple[dict, ...]
    expected_state_hash: str
```

### 4.5 ReplayResponse

```python
@dataclass(frozen=True)
class ReplayResponse:
    expected_state_hash: str
    replayed_state_hash: str
    byte_identical: bool
    duration_ms: int
```

### 4.6 GraphResponse

```python
@dataclass(frozen=True)
class GraphResponse:
    graph_id: str
    tenant_id: str
    patient_id: str
    state_hash: str
    built_at: str
    nodes: tuple[GraphNodeDTO, ...]
    edges: tuple[GraphEdgeDTO, ...]
```

**Nota:** GraphResponse expõe `nodes`/`edges` lossless (proveniente de
`KnowledgeGraph.to_canonical_dict()` per ADR-0008 Opção A).

---

## 5. Permission Mapping Rationale

### 5.1 Reuso Explícito

| Domínio | Permission usada | Justificativa |
|---|---|---|
| Genome | `INTELLIGENCE_CORRELATION_READ` | Genome é base de correlação. Quem lê correlações lê genomes. |
| Correlation | `INTELLIGENCE_CORRELATION_READ/_COMPUTE` | Já existem, semântica exata. |
| Hypothesis | `INTELLIGENCE_CORRELATION_READ` | Hipóteses derivam de correlações. Permission dedicada seria redundante. |
| Cohort | `INTELLIGENCE_COHORT_READ/_DEFINE` | Já existem, semântica exata. |
| Graph | `INTELLIGENCE_CORRELATION_READ` | Grafo é visualização de correlações + hipóteses. Permission dedicada seria redundante. |
| Research session (read) | `INTELLIGENCE_ANALYTICS_READ` | Sessions são outputs analíticos. |
| Research execute | `INTELLIGENCE_CORRELATION_COMPUTE` | Reusa compute permission (ambos disparam pipelines). |
| Replay | `INTELLIGENCE_CORRELATION_COMPUTE` | Replay é re-execução de pipeline compute. |
| Explanation | `EXPLAINABILITY_READ` | Já existe, semântica exata. |
| Events | `INTELLIGENCE_TIMELINE_READ` | Reusa timeline permission (events são timeline). |

### 5.2 Permissions NÃO Criadas

Sprint 4.5 **NÃO cria**:

- ❌ `INTELLIGENCE_GENOME_READ` (reusada `INTELLIGENCE_CORRELATION_READ`)
- ❌ `INTELLIGENCE_HYPOTHESIS_READ` (reusada)
- ❌ `INTELLIGENCE_GRAPH_READ` (reusada)
- ❌ `INTELLIGENCE_RESEARCH_*` (reusadas analytics/compute)
- ❌ `INTELLIGENCE_REPLAY_EXECUTE` (reusada compute)

Justificativa: cada nova permission adiciona superfície de auditoria
e complexidade de role mapping sem ganho semântico.

---

## 6. Conflitos com Rotas Legacy

### 6.1 Routes existentes que podem conflitar

| Rota legacy | Conflito potencial | Resolução |
|---|---|---|
| `routes/intelligence_timeline.py` | `/api/intelligence/timeline/*` | Sem conflito (path diferente). |
| `routes/explainability.py` | `/api/explainability/*` | Sem conflito. |
| `routes/clinical_context.py` | `/api/clinical/contexts/*` | Sem conflito. |
| `routes/neuro_registry.py` | `/api/neuro/registry/*` | Sem conflito. |

### 6.2 Prefixo Padronizado

Todos os endpoints Sprint 4.5 usam `/api/knowledge/*` para evitar
conflito com rotas legacy em outros prefixos. Justificativa:

- `/api/knowledge/*` é namespace novo.
- Mantém backward compat com rotas existentes.
- Permite evolução futura para `/api/v2/knowledge/*` se necessário.

---

## 7. Validação

### 7.1 Testes obrigatórios (W3.7)

| Cenário | Arquivo |
|---|---|
| Authorization matrix completa | `test_rest_authorization.py` |
| Tenant isolation (A não vê B) | `test_rest_tenant_isolation.py` |
| ID enumeration indistinguível | `test_rest_id_enumeration.py` |
| Payload validation | `test_rest_payload_validation.py` |
| Pagination (list endpoints) | `test_rest_pagination.py` |
| Audit log por endpoint | `test_rest_audit.py` |

### 7.2 Critérios de aceitação W3

- [ ] Todos os 14 endpoints retornam 200/201 para cenários válidos.
- [ ] Cross-tenant access sempre retorna 404 (não 403).
- [ ] Audit log escrito para cada request.
- [ ] Permission denied retorna 403 com mensagem genérica.
- [ ] Nenhum endpoint fora de `interfaces/rest/` registra rotas conflitantes.

---

## 8. Conformidade

| Foundation | Compatível? | Notas |
|---|---|---|
| AS-000 Language Specification | ✅ | Termos canônicos preservados |
| AS-001 Clinical Gene | ✅ | Genome DTO compatível |
| AS-002 Clinical Expression | ✅ | Correlation DTO compatível |
| ASM-001 Meta Model | ✅ | 16 seções canônicas respeitadas |
| ADR-0001 Clinical Event Engine | ✅ | Events endpoint expõe via DTO |
| ADR-0005 Clinical Genome Pivot | ✅ | Genome permanece projection |
| ADR-0006 Normative Conflict Resolution | ✅ | Hierarquia normativa respeitada |
| ADR-0008 Materialized Knowledge Graph | ✅ | GraphResponse usa JSON blob |
| Architecture Freeze v1.0 | ✅ | Endpoints em `interfaces/rest/` namespace reservado |

---

## 9. Próximas Etapas

Após G5 aprovado:

1. **W3.1** — `araos/auth/decorators.py` com `@tenant_required`.
2. **W3.2** — `interfaces/rest/` blueprints (9 arquivos).
3. **W3.3** — `interfaces/rest/dto.py` (DTOs conforme §4).
4. **W3.4** — Permission mapping aplicado em cada handler.
5. **W3.5** — Registration em `app_cors_livre.py`.
6. **W3.6** — `interfaces/rest/audit.py` helper.
7. **W3.7** — Tests conforme §7.1.

---

## Histórico de Revisões

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 2026-07-22 | Redação inicial. 14 endpoints, 8 permissions reusadas, 0 novas. |

---

> **Foundation Freeze respeitada.**
> **Architecture Freeze v1.0 preservada.**
> **Permissions existentes reusadas (zero redundância).**
> **Tenant sempre de JWT, nunca de path/query/body.**
