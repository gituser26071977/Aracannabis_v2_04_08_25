# AraOS Week 7A — Platform Hardening

**Status:** ✅ CONCLUÍDO  
**Release:** AraOS Alpha 0.2  
**Data:** 2026-06-07  
**Branch:** `main`

---

## Objetivo

Transformar a arquitetura validada na Week 6 em uma **plataforma pronta para receber inteligência artificial**, corrigindo os 4 débitos arquiteturais identificados no relatório da Week 6.

> *"O cérebro está construído. Agora vamos blindá-lo."*

---

## 4 Pilares de Hardening

### P1: Event Consumers de Produção 🔴

**Problema:** Os fluxos da Week 6 chamavam `ClinicalProjectionEngine.process()` diretamente após publicar eventos. Isso viola o princípio de desacoplamento do Event-Driven Architecture.

**Solução:**
- Criado `ClinicalProjectionConsumer` (`araos/clinical/consumers.py`)
- Registrado automaticamente no `InMemoryEventBus` (demos) e pronto para `AraOSEventBus.subscribe()` (produção)
- Todos os eventos clínicos são processados por consumers, nunca pelo publisher

**Eventos consumidos automaticamente:**
```
DIAGNOSIS_ADDED, DIAGNOSIS_UPDATED
MEDICATION_PRESCRIBED, MEDICATION_STOPPED
ALLERGY_REGISTERED, ALLERGY_REMOVED
EXAM_RESULTED, CLINICAL_NOTE_CREATED, PROCEDURE_APPLIED
```

**Validação:**
```bash
# Nenhuma chamada direta aos fluxos
grep -r "ClinicalProjectionEngine(env.db)" araos/demo/  # vazio ✓
grep -r "projection.process(" araos/demo/  # vazio ✓
```

---

### P2: Digital Twin Cache 🔴

**Problema:** O `PatientDigitalTwinBuilder` reconstruía o twin do zero a cada consulta, fazendo múltiplas queries sequenciais.

**Solução:**
- Criado contrato `TwinCache` + implementações `InMemoryTwinCache` e `RedisTwinCache`
- TTL padrão: **300 segundos (5 minutos)**
- `PatientDigitalTwinBuilder` agora recebe `cache: Optional[TwinCache]`
- Cache invalidado automaticamente pelo `ClinicalProjectionEngine` após cada projeção

**Métricas:**

| Métrica | Sem Cache | Com Cache | Redução |
|---------|-----------|-----------|---------|
| Twin rebuild | 0.67 ms | 0.38 ms | **43%** |
| Fluxo 1 completo | 46.2 ms | 30.9 ms | **33%** |
| Fluxo 2 completo | 35.7 ms | 10.9 ms | **69%** |
| Fluxo 3 completo | 47.3 ms | 37.9 ms | **20%** |

**Nota:** A redução varia por fluxo porque:
- Fluxo 1: consumer processa evento + invalida cache + rebuild = cache não ajuda muito no primeiro acesso
- Fluxo 2: apenas leitura do twin = cache hit máximo
- Fluxo 3: projeção + invalidação + rebuild = similar ao fluxo 1

---

### P3: Projection Idempotency 🔴

**Problema:** O mesmo evento processado 2x criaria entidades duplicadas (especialmente em cenários de retry do Event Bus).

**Solução:**
- Criado contrato `IdempotencyTracker` + implementações `InMemoryIdempotencyTracker` e `RedisIdempotencyTracker`
- `ClinicalProjectionEngine.process()` verifica `tracker.is_processed(event_id)` antes de processar
- Eventos já processados retornam `{"processed": False, "reason": "already_processed"}`
- Eventos falhos são marcados separadamente para retry controlado

**Validação:**
```python
# Primeira vez
result1 = await projection.process(event)  # {"processed": True, ...}

# Segunda vez (mesmo event_id)
result2 = await projection.process(event)  # {"processed": False, "reason": "already_processed"}

# Entidades não duplicadas ✓
```

---

### P4: Clinical Repository 🔴

**Problema:** `ClinicalProjectionEngine`, `PatientDigitalTwinBuilder` e `ClinicalSummaryEngine` dependiam diretamente de `SQLAlchemy Session`.

**Solução:**
- Criado contrato `ClinicalRepository` (`araos/clinical/repository.py`)
- Implementações:
  - `SqlAlchemyClinicalRepository`: produção (usa Session internamente)
  - `InMemoryClinicalRepository`: testes/demos (dicionários Python)
- Todos os componentes clínicos agora recebem `ClinicalRepository` via injeção de dependência

**Interfaces:**
```python
class ClinicalRepository(ABC):
    def get_profile(self, patient_id, tenant_id) -> Optional[ClinicalProfile]
    def get_diagnoses(self, patient_id, tenant_id, active_only=True) -> List[Diagnosis]
    def get_medications(self, patient_id, tenant_id, active_only=True) -> List[Medication]
    def get_allergies(self, patient_id, tenant_id, active_only=True) -> List[Allergy]
    def get_risk_factors(self, patient_id, tenant_id, active_only=True) -> List[RiskFactor]
    def get_procedures(self, patient_id, tenant_id, limit=10) -> List[Procedure]
    def save_entity(self, entity) -> None
    def update_profile(self, profile) -> None
    def add_timeline_entry(self, entry) -> None
    def commit(self) -> None
```

---

## Arquitetura Atualizada

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   Publisher     │────▶│   Event Bus          │────▶│   Consumer      │
│   (Fluxos)      │     │   (Redis Streams)    │     │   (Clinical)    │
└─────────────────┘     └──────────────────────┘     └────────┬────────┘
                                                              │
                                                              ▼
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   Twin Cache    │◀────│   Projection Engine  │────▶│   Repository    │
│   (Redis)       │     │   (Idempotente)      │     │   (SQLAlchemy)  │
└─────────────────┘     └──────────────────────┘     └─────────────────┘
         │                                                       │
         │              ┌──────────────────────┐                  │
         └─────────────▶│   Digital Twin       │◀─────────────────┘
                        │   (Builder + Cache)  │
                        └──────────────────────┘
```

---

## Testes

```bash
python -m pytest tests/test_week6_flows.py tests/test_week7a_hardening.py -v
```

**Resultado:** 28 passed, 0 failed

### Testes da Week 7A (17 casos)

| Classe | Teste | Status |
|--------|-------|--------|
| `TestP1EventConsumers` | `test_consumer_processes_diagnosis_event` | ✅ |
| `TestP1EventConsumers` | `test_consumer_processes_medication_event` | ✅ |
| `TestP1EventConsumers` | `test_no_direct_projection_calls_in_fluxo1` | ✅ |
| `TestP1EventConsumers` | `test_no_direct_projection_calls_in_fluxo3` | ✅ |
| `TestP2TwinCache` | `test_cache_miss_then_hit` | ✅ |
| `TestP2TwinCache` | `test_cache_invalidation_on_clinical_event` | ✅ |
| `TestP2TwinCache` | `test_cache_ttl_expires` | ✅ |
| `TestP3Idempotency` | `test_event_processed_only_once` | ✅ |
| `TestP3Idempotency` | `test_tracker_tracks_processed_events` | ✅ |
| `TestP4ClinicalRepository` | `test_repository_interface` | ✅ |
| `TestP4ClinicalRepository` | `test_sqlalchemy_repository_uses_session` | ✅ |
| `TestP4ClinicalRepository` | `test_inmemory_repository_isolation` | ✅ |
| `TestP4ClinicalRepository` | `test_twin_builder_uses_repository_not_session` | ✅ |
| `TestMetrics` | `test_twin_rebuild_faster_with_cache` | ✅ |
| `TestMetrics` | `test_fluxo1_completo_com_nova_arquitetura` | ✅ |
| `TestMetrics` | `test_fluxo2_completo_com_nova_arquitetura` | ✅ |
| `TestMetrics` | `test_fluxo3_completo_com_nova_arquitetura` | ✅ |

---

## Arquivos Criados/Modificados

### Novos
| Arquivo | Descrição |
|---------|-----------|
| `araos/clinical/repository.py` | ClinicalRepository + SqlAlchemy + InMemory implementations |
| `araos/clinical/cache.py` | TwinCache + InMemory + Redis implementations |
| `araos/clinical/idempotency.py` | IdempotencyTracker + InMemory + Redis implementations |
| `araos/clinical/consumers.py` | ClinicalProjectionConsumer + register function |
| `tests/test_week7a_hardening.py` | 17 testes de hardening |
| `docs/WEEK7A_PLATFORM_HARDENING.md` | Esta documentação |

### Modificados
| Arquivo | Mudança |
|---------|---------|
| `araos/clinical/projections/engine.py` | Usa Repository + Tracker + Cache |
| `araos/clinical/twin/models.py` | Builder recebe Repository + Cache |
| `araos/demo/demo_base.py` | Inicializa Repository, Cache, Tracker, Consumer |
| `araos/demo/concierge_intake_flow.py` | Remove chamada direta ao Projection Engine |
| `araos/demo/whatsapp_document_flow.py` | Remove chamada direta ao Projection Engine |
| `araos/demo/smart_flow_checkin.py` | Usa novo TwinBuilder |

---

## Checklist do CTO

| # | Requisito | Status |
|---|-----------|--------|
| 1 | Nenhuma chamada direta ao Projection Engine | ✅ |
| 2 | Digital Twin cacheado | ✅ |
| 3 | Projection Engine idempotente | ✅ |
| 4 | ClinicalRepository implementado | ✅ |
| 5 | Fluxos da Week 6 continuam funcionando | ✅ (11/11 testes passam) |
| 6 | Latência reduzida | ✅ (até 69% em leituras cacheadas) |

---

## Próximos Passos

**AraOS Week 7B — Intelligence Layer v1**

Agora que a plataforma está blindada:
- ✅ Eventos são consumidos, não chamados
- ✅ Cache reduz latência
- ✅ Idempotência previne duplicação
- ✅ Repository desacopla o ORM

Está autorizado a iniciar a especificação da Intelligence Layer v1:
1. Integrar LLM Provider (OpenAI/Gemini/Claude)
2. Implementar Embedding Provider + Vector Store
3. RAG Pipeline básico
4. Agent Runtime com LLM

**A plataforma está pronta para receber inteligência.** 🧠
