# AraOS Week 7B — Intelligence Layer v1

**Status:** ✅ CONCLUÍDO  
**Release:** AraOS Alpha 0.3  
**Data:** 2026-06-07  
**Branch:** `main`

---

## Objetivo

Adicionar a **primeira camada de inteligência artificial** ao AraOS, mantendo a arquitetura intacta. A IA é um **plugin**, nunca o centro da plataforma.

> *"O cérebro está blindado. Agora vamos conectar a inteligência."*

---

## Arquitetura da Intelligence Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENTES                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Concierge   │  │Voice Copilot │  │  Futuros...  │          │
│  │  (Chat)      │  │  (Read-Only) │  │              │          │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘          │
│         │                 │                                      │
│         └────────┬────────┘                                      │
│                  ▼                                               │
│         ┌──────────────┐                                         │
│         │  LLMRuntime  │  ← Orquestração, Métricas, Trust       │
│         └──────┬───────┘                                         │
│                │                                                 │
│         ┌──────┴───────┐                                         │
│         │  LLMRouter   │  ← Seleção de provider, Fallback       │
│         └──────┬───────┘                                         │
│                │                                                 │
│    ┌───────────┼───────────┐                                    │
│    ▼           ▼           ▼                                    │
│ ┌──────┐  ┌──────┐  ┌──────┐                                    │
│ │OpenAI│  │Gemini│  │Claude│  ← Providers (stub/mock/real)     │
│ └──────┘  └──────┘  └──────┘                                    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │     ClinicalContextBuilder (Twin + Summary + Timeline)   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   AraOS Platform │
                    │  (Event Bus,     │
                    │   Audit Ledger,  │
                    │   Digital Twin)  │
                    └─────────────────┘
```

---

## Componentes Implementados

### Parte 1: LLM Runtime

**Arquivos:**
- `araos/intelligence/runtime/runtime.py` — `LLMRuntime`
- `araos/intelligence/runtime/metrics.py` — `LLMMetricsCollector`, `LLMCallMetric`
- `araos/intelligence/runtime/observability.py` — `LLMObservability`

**Responsabilidades:**
- Orquestra chamadas LLM via Router
- Coleta métricas automaticamente (latência, tokens, custo)
- Registra observabilidade (audit hooks)
- Adiciona **Trust Level** em todas as respostas

**API:**
```python
runtime = LLMRuntime(router)
result = await runtime.complete(
    messages=[...],
    source_type=SourceType.AI_INFERENCE,
    correlation_id="corr_001",
)
# → TrustedResponse com proveniência e métricas
```

---

### Parte 2: LLM Router

**Arquivo:** `araos/intelligence/providers/router.py` — `LLMRouter`

**Responsabilidades:**
- Registra múltiplos providers com prioridade
- Seleciona provider por nome preferencial
- Implementa **fallback chain** — se um provider falha, tenta o próximo
- Registra métricas de cada tentativa

**Uso:**
```python
router = LLMRouter()
router.register("openai", OpenAIProvider(api_key=...), priority=1)
router.register("gemini", GeminiProvider(api_key=...), priority=2)
router.register("mock", MockLLMProvider(), priority=0)

response = await router.route(request, preferred_provider="openai")
```

---

### Parte 3: LLM Providers

**Arquivos:**
- `araos/intelligence/providers/openai_provider.py` — `OpenAIProvider`
- `araos/intelligence/providers/gemini_provider.py` — `GeminiProvider`
- `araos/intelligence/providers/claude_provider.py` — `ClaudeProvider` (stub)
- `araos/intelligence/providers/mock_provider.py` — `MockLLMProvider` (testes)

**Características:**
- Todos implementam `LLMProvider` (contrato existente)
- Stubs funcionam sem API key (modo simulação)
- Mock provider responde deterministicamente para testes
- Preparados para integração real (basta fornecer API key)

---

### Parte 4: Context Builder

**Arquivo:** `araos/intelligence/context/builder.py` — `ClinicalContextBuilder`

**Responsabilidades:**
- Recebe `PatientDigitalTwin`, `ClinicalTimeline`, `ClinicalSummary`
- Produz contexto formatado para LLM
- **Token budgeting** — limita tamanho do contexto
- **Truncation** — corta partes menos importantes se necessário
- **System prompt com restrições clínicas**:
  - NUNCA faça diagnósticos
  - NUNCA prescreva medicamentos
  - NUNCA substitua o julgamento médico

**Uso:**
```python
builder = ClinicalContextBuilder(max_tokens=4000)
context = builder.build(twin=twin, timeline_entries=entries)

messages = [
    LLMMessage(role=MessageRole.SYSTEM, content=context.system_prompt),
    LLMMessage(role=MessageRole.USER, content=context.patient_context),
]
```

---

### Parte 5: Concierge Intelligence

**Arquivo:** `araos/agents/intelligent/concierge.py` — `ConciergeAgent`

**Capacidades:**
- **Detecção de intenção:** scheduling, symptom_report, information_request, clinical_question, general
- **Triagem administrativa:** direciona para o fluxo correto
- **Agendamento:** inicia processo de marcação de consulta
- **Captura de informações:** registra sintomas para o médico

**RESTRIÇÕES:**
- ❌ NUNCA faz diagnóstico
- ❌ NUNCA prescreve medicamentos
- ❌ NUNCA recomenda tratamentos
- ✅ SEMPRE encaminha questões clínicas para o médico

**Exemplo de interação:**
```
Paciente: "Estou com dor de cabeça e tontura"
Concierge: "Entendo que está sentindo tontura. Vou registrar seus sintomas 
           para o médico."
→ Intent: symptom_report
→ TrustLevel: AI_INFERENCE
→ Emite evento para médico avaliar
```

---

### Parte 6: Voice Read-Only Intelligence

**Arquivo:** `araos/agents/intelligent/voice.py` — `VoiceCopilotAgent`

**Capacidades:**
- Responde consultas sobre dados estruturados do paciente
- Comandos suportados:
  - `"Ara, resumo do paciente"` → `summary`
  - `"Ara, medicamentos atuais"` → `medications`
  - `"Ara, alergias registradas"` → `allergies`
  - `"Ara, diagnósticos"` → `diagnoses`
  - `"Ara, timeline recente"` → `timeline`

**Fonte de dados:**
- `STRUCTURED_DATA` — dados diretos do Digital Twin
- `GENERATED_SUMMARY` — resumo rules-based do ClinicalSummaryEngine

**Sem inferências clínicas:**
- Nunca sugere tratamentos
- Nunca interpreta dados além do que está registrado
- Responde apenas com fatos do prontuário

**Exemplo de interação:**
```
Médico: "Ara, medicamentos atuais"
Ara:    "Medicações ativas:
          • Losartana 50mg — 1x ao dia"
→ TrustLevel: STRUCTURED_DATA
→ SourceType: STRUCTURED_DATA
→ Não requer verificação humana
```

---

### Parte 7: Trust Levels

**Arquivo:** `araos/intelligence/trust/levels.py`

**Valores:**
| Nível | Valor | Descrição | Requer Verificação |
|-------|-------|-----------|-------------------|
| `STRUCTURED_DATA` | `structured_data` | Dado direto do banco | ❌ Não |
| `GENERATED_SUMMARY` | `generated_summary` | Resumo rules-based | ❌ Não |
| `AI_INFERENCE` | `ai_inference` | Inferência do LLM | ✅ Sim |

**Toda resposta carrega:**
- `content`: texto da resposta
- `source_type`: de onde veio
- `trust_level`: nível de confiança
- `provider`: qual LLM gerou
- `model`: qual modelo
- `metadata`: latência, tokens, custo

---

### Parte 8: Observabilidade

**Arquivos:**
- `araos/intelligence/runtime/metrics.py`
- `araos/intelligence/runtime/observability.py`

**Métricas coletadas:**
- Provider utilizado
- Latência (ms)
- Tokens (prompt, completion, total)
- Custo estimado (USD)
- Falhas
- Fallbacks

**Integração com Audit Ledger:**
- Todas as chamadas LLM podem ser auditadas
- Hook para `AuditService.log()`
- Eventos de observabilidade com `correlation_id`

---

## Testes

```bash
python -m pytest tests/test_week7b_intelligence.py -v
```

**Resultado:** 32 passed, 0 failed

### Testes por categoria

| Categoria | Testes | Status |
|-----------|--------|--------|
| Trust Levels | 4 | ✅ |
| LLM Providers | 7 | ✅ |
| LLM Router | 4 | ✅ |
| LLM Runtime | 3 | ✅ |
| Context Builder | 2 | ✅ |
| Concierge Agent | 4 | ✅ |
| Voice Copilot | 5 | ✅ |
| Observabilidade | 3 | ✅ |

---

## Testes completos (Weeks 6 + 7A + 7B)

```bash
python -m pytest tests/ -v
```

**Resultado:** 60 passed, 0 failed

| Semana | Testes | Status |
|--------|--------|--------|
| Week 6 (Fluxos MVP) | 11 | ✅ |
| Week 7A (Hardening) | 17 | ✅ |
| Week 7B (Intelligence) | 32 | ✅ |
| **Total** | **60** | **✅** |

---

## Arquivos Criados/Modificados

### Novos (Week 7B)
| Arquivo | Descrição |
|---------|-----------|
| `araos/intelligence/trust/levels.py` | TrustLevel, SourceType, TrustedResponse |
| `araos/intelligence/providers/mock_provider.py` | MockLLMProvider para testes |
| `araos/intelligence/providers/openai_provider.py` | OpenAIProvider |
| `araos/intelligence/providers/gemini_provider.py` | GeminiProvider |
| `araos/intelligence/providers/claude_provider.py` | ClaudeProvider (stub) |
| `araos/intelligence/providers/router.py` | LLMRouter com fallback |
| `araos/intelligence/runtime/runtime.py` | LLMRuntime |
| `araos/intelligence/runtime/metrics.py` | LLMMetricsCollector |
| `araos/intelligence/runtime/observability.py` | LLMObservability |
| `araos/intelligence/context/builder.py` | ClinicalContextBuilder |
| `araos/agents/intelligent/concierge.py` | ConciergeAgent |
| `araos/agents/intelligent/voice.py` | VoiceCopilotAgent |
| `tests/test_week7b_intelligence.py` | 32 testes |
| `docs/WEEK7B_INTELLIGENCE_LAYER.md` | Esta documentação |

### Modificados
| Arquivo | Mudança |
|---------|---------|
| `araos/intelligence/__init__.py` | Exporta novos componentes |

---

## Checklist do CTO

| # | Requisito | Status |
|---|-----------|--------|
| 1 | LLM Runtime | ✅ |
| 2 | LLM Router (OpenAI, Gemini, Claude) | ✅ |
| 3 | Context Builder (Twin + Summary + Timeline) | ✅ |
| 4 | Concierge Intelligence | ✅ |
| 5 | Voice Read-Only Intelligence | ✅ |
| 6 | Trust Levels (STRUCTURED_DATA, GENERATED_SUMMARY, AI_INFERENCE) | ✅ |
| 7 | Observabilidade (provider, latência, custo, tokens, falhas, fallback) | ✅ |
| 8 | Nenhum diagnóstico automático | ✅ |
| 9 | Nenhuma prescrição automática | ✅ |
| 10 | Arquitetura da plataforma intacta | ✅ |
| 11 | Todos os testes passando | ✅ (60/60) |

---

## Próximos Passos

**AraOS Week 8 — RAG Pipeline v1**

Agora que a Intelligence Layer está operacional:
- ✅ LLM Runtime executa com observabilidade
- ✅ Router gerencia fallback
- ✅ Context Builder serializa dados clínicos
- ✅ Concierge conversa naturalmente
- ✅ Voice responde consultas read-only
- ✅ Trust Levels protegem cada resposta

Próximas capacidades:
1. **Embedding Provider** real (OpenAI, local)
2. **Vector Store** (PGVector, Qdrant)
3. **RAG Pipeline** — busca semântica em documentos clínicos
4. **Indexação automática** de evoluções, receitas, exames
5. **Busca conversacional** — "Ara, quando o paciente fez o último exame de creatinina?"

**A plataforma tem inteligência. Está pronta para memória."** 🧠🌿
