# AraOS Week 6 — MVP Integration Sprint

**Status:** ✅ CONCLUÍDO  
**Release:** AraOS Alpha 0.1  
**Data:** 2026-06-06  
**Branch:** `main` (commit `8f623f1`)

---

## Objetivo

Provar que a plataforma AraOS funciona como um **sistema operacional clínico integrado**, conectando todos os módulos construídos nas semanas 0–5 em fluxos end-to-end reais, **sem uso de LLMs**.

> *"Primeiro construir o cérebro. Depois conectar os LLMs."* — Week 4 motto

---

## Arquitetura dos Fluxos

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Concierge  │────▶│ Digital Twin│────▶│    Voice    │
│  (WhatsApp) │     │   (SQLite)  │     │  (Copilot)  │
└─────────────┘     └─────────────┘     └─────────────┘
       Fluxo 1

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Smart Flow │────▶│  Event Bus  │────▶│  Consulta   │
│  (Check-in) │     │   (Redis)   │     │  (SIAP)     │
└─────────────┘     └─────────────┘     └─────────────┘
       Fluxo 2

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  WhatsApp   │────▶│   Intake    │────▶│  Consulta   │
│ (Documento) │     │  (OCR/IA)   │     │ (Agendada)  │
└─────────────┘     └─────────────┘     └─────────────┘
       Fluxo 3
```

---

## Fluxo 1: Concierge → Digital Twin → Voice

### Passos
1. Paciente envia mensagem via WhatsApp (`WHATSAPP_RECEIVED`)
2. Concierge identifica sintomas (`DIAGNOSIS_ADDED`)
3. Clinical Projection Engine aplica evento ao banco
4. Patient Digital Twin é reconstruído do estado atual
5. Clinical Summary Engine gera resumo estruturado
6. Voice Copilot responde com contexto completo

### Eventos Emitidos
| # | Evento | Categoria | Fonte |
|---|--------|-----------|-------|
| 1 | `WHATSAPP_RECEIVED` | COMMUNICATION | Concierge |
| 2 | `DIAGNOSIS_ADDED` | CLINICAL | Concierge |

### Tempo Médio de Execução
**46.2 ms** (SQLite em memória, sem I/O de rede)

---

## Fluxo 2: Smart Flow → Check-in → Consulta

### Passos
1. Smart Flow detecta paciente na entrada (`CHECKIN_DETECTED`)
2. Check-in concluído com biometria (`CHECKIN_COMPLETED`)
3. Contexto propagado automaticamente para Voice
4. Consulta iniciada com Digital Twin carregado (`CONSULTATION_STARTED`)
5. Evolução clínica registrada (`EVOLUTION_CREATED`)

### Eventos Emitidos
| # | Evento | Categoria | Fonte |
|---|--------|-----------|-------|
| 1 | `CHECKIN_DETECTED` | OPERATIONAL | Smart Flow |
| 2 | `CHECKIN_COMPLETED` | OPERATIONAL | Smart Flow |
| 3 | `CONSULTATION_STARTED` | CLINICAL | SIAP |
| 4 | `EVOLUTION_CREATED` | CLINICAL | SIAP |

### Tempo Médio de Execução
**35.7 ms** (mais rápido — menos projeções de entidades)

---

## Fluxo 3: WhatsApp → Intake → Documentos → Consulta

### Passos
1. Paciente envia receita médica via WhatsApp (`DOCUMENT_UPLOADED`)
2. OCR processa documento (`DOCUMENT_PROCESSED`)
3. Medicação extraída adicionada ao perfil (`MEDICATION_PRESCRIBED`)
4. Clinical Projection Engine atualiza entidades
5. Timeline clínica atualizada
6. Digital Twin reconstruído com nova medicação
7. Consulta agendada automaticamente (`CONSULTATION_SCHEDULED`)

### Eventos Emitidos
| # | Evento | Categoria | Fonte |
|---|--------|-----------|-------|
| 1 | `DOCUMENT_UPLOADED` | OPERATIONAL | WhatsApp |
| 2 | `DOCUMENT_PROCESSED` | OPERATIONAL | Intake |
| 3 | `MEDICATION_PRESCRIBED` | CLINICAL | Intake |
| 4 | `CONSULTATION_SCHEDULED` | OPERATIONAL | Concierge |

### Tempo Médio de Execução
**47.3 ms** (mais lento — projeção + timeline + twin rebuild)

---

## Componentes Utilizados por Fluxo

| Componente | Fluxo 1 | Fluxo 2 | Fluxo 3 |
|-----------|:-------:|:-------:|:-------:|
| Event Bus (Redis) | ✅ | ✅ | ✅ |
| Clinical Projection Engine | ✅ | ❌ | ✅ |
| Patient Digital Twin | ✅ | ✅ | ✅ |
| Clinical Summary Engine | ✅ | ❌ | ❌ |
| Timeline | ❌ | ❌ | ✅ |
| Identity Context | ✅ | ✅ | ✅ |
| Tenant Context | ✅ | ✅ | ✅ |

---

## Testes

```bash
python -m pytest tests/test_week6_flows.py -v
```

**Resultado:** 11 passed, 0 failed

### Casos de Teste
| Classe | Teste | Descrição |
|--------|-------|-----------|
| `TestFluxo1ConciergeIntake` | `test_fluxo_completo` | Valida eventos, twin, summary |
| `TestFluxo1ConciergeIntake` | `test_correlation_chain` | Cadeia de correlação ≥ 2 |
| `TestFluxo1ConciergeIntake` | `test_digital_twin_builds` | Twin reconstruído com dados |
| `TestFluxo2SmartFlowCheckin` | `test_fluxo_completo` | 4 eventos, check-in facial |
| `TestFluxo2SmartFlowCheckin` | `test_checkin_detected_emits_event` | Evento único emitido |
| `TestFluxo2SmartFlowCheckin` | `REDACTED` | Contexto carregado |
| `TestFluxo3WhatsappDocument` | `test_fluxo_completo` | 4 eventos, OCR 94% |
| `TestFluxo3WhatsappDocument` | `REDACTED` | Atenolol adicionado |
| `TestFluxo3WhatsappDocument` | `test_consultation_auto_scheduled` | Agendamento automático |
| `TestTodosOsFluxos` | `test_fluxos_sao_independentes` | Ambientes isolados |
| `TestTodosOsFluxos` | `test_event_bus_rastreia_correlacao` | Correlation ID em todos |

---

## Cobertura de Testes

- **Demo modules (`araos/demo/`)**: 100%
- **Clinical Projection Engine**: 58% (parcial — métodos de replay não testados)
- **Platform geral**: 46% (inclui código não exercitado pelos fluxos MVP)

Relatório HTML: `htmlcov_week6/index.html`

---

## Migrations

**Nenhuma migration nova necessária.** A Week 6 utiliza exclusivamente tabelas criadas nas semanas anteriores:

| Semana | Migration | Tabelas |
|--------|-----------|---------|
| W1 | `83c3e98787e1` | `araos_organizations`, `araos_clinics`, `araos_professionals`, `araos_users`, `araos_service_accounts`, `araos_feature_flags` |
| W3 | `ca1ef05ac0d2` | `araos_event_store`, `araos_event_dlq`, `araos_event_correlations`, `araos_audit_ledger` |
| W4 | `9b93d2cb67d7` | `araos_clinical_profiles`, `araos_clinical_diagnoses`, `araos_clinical_medications`, `araos_clinical_allergies`, `araos_clinical_procedures`, `araos_clinical_risk_factors`, `araos_clinical_timeline_entries` |
| W5 | `791ba78aa8fb` | `araos_agent_registry`, `araos_agent_memory` |

---

## Decisões Arquiteturais

1. **Sem LLMs**: Todos os fluxos usam regras determinísticas. NLP/NLU será adicionado na Intelligence Layer v1.
2. **Event Bus em memória nos testes**: Produção usa Redis; demos usam `InMemoryEventBus` para determinismo.
3. **SQLite em memória**: Demos rodam sem dependências externas. Produção usa PostgreSQL.
4. **Digital Twin reconstruído sob demanda**: Não é persistido — é uma projeção live do estado atual.

---

## Próximos Passos (Week 7 — Intelligence Layer v1)

Ver `docs/WEEK6_RELATORIO_FINAL.md` para análise completa de gargalos, acoplamentos e recomendações.
