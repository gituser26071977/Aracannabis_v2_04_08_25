# AraOS Week 11A — Adaptive Follow-up Engine

**Status:** ✅ CONCLUÍDO  
**Release:** AraOS Alpha 0.6  
**Data:** 2026-06-08  
**Branch:** `main`

---

## Objetivo

Transformar o AraOS de **prontuário eletrônico** em **plataforma de acompanhamento longitudinal ativo**.

> *"Hoje: Consulta → Retorno 30 dias. Futuro: Agente acompanha diariamente → Médico intervém apenas quando necessário."*

**Princípio:** Follow-up não deve ser baseado apenas em datas fixas. O acompanhamento deve ser **adaptativo** — baseado em fases terapêuticas, eventos clínicos e interação automática.

---

## Arquitetura do Adaptive Follow-up Engine

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ADAPTIVE FOLLOW-UP ENGINE                             │
│                                                                          │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐              │
│  │  Program    │────→│   Phase     │────→│ Checkpoint  │              │
│  │  (lifecycle)│     │ (adaptive)  │     │ (trigger)   │              │
│  └──────┬──────┘     └─────────────┘     └──────┬──────┘              │
│         │                                         │                     │
│         │    ┌────────────────────────────────────┘                     │
│         │    │                                                          │
│         ▼    ▼                                                          │
│  ┌─────────────────────────────────────────────────────────┐           │
│  │              AdaptiveFollowupEngine                      │           │
│  │  • register_program()  • get_due_checkpoints()           │           │
│  │  • process_response()  • evaluate_rules()                │           │
│  │  • get_summary()       • start/complete/pause            │           │
│  └─────────────────────────────────────────────────────────┘           │
│         │                                                               │
│    ┌────┴────┬──────────┬──────────┬──────────┐                        │
│    ▼         ▼          ▼          ▼          ▼                        │
│ ┌──────┐ ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐                      │
│ │Rule  │ │Event │  │Twin  │ │Know- │  │Whats-│                      │
│ │Engine│ │ Bus  │  │Update│ │ledge │  │App   │                      │
│ └──────┘ └──────┘  └──────┘ └──────┘  └──────┘                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              ┌──────────┐   ┌──────────┐   ┌──────────┐
              │ Cannabis │   │Cardiology│   │Psychiatry│
              │ Follow-up│   │ Follow-up│   │ Follow-up│
              └──────────┘   └──────────┘   └──────────┘
```

---

## Componentes Implementados

### Parte 1: Follow-up Core

**Arquivo:** `araos/followup/core/models.py`

**Modelos:**
| Modelo | Descrição |
|--------|-----------|
| `FollowupProgram` | Programa de acompanhamento com lifecycle |
| `FollowupPhase` | Fase terapêutica (ordem, duração, critérios) |
| `FollowupCheckpoint` | Ponto de verificação com janela temporal |
| `FollowupQuestionnaire` | Questionário com múltiplas perguntas |
| `FollowupQuestion` | Pergunta com tipo, categoria, validação |
| `FollowupResponse` | Resposta do paciente com answers |
| `FollowupRule` | Regra SE/ENTÃO com condição e ações |
| `FollowupAlert` | Alerta com lifecycle (open → ack → resolved) |

---

### Parte 2: Adaptive Phases

**4 fases terapêuticas:**

| Fase | Duração | Checkpoints | Foco |
|------|---------|-------------|------|
| **Início** | Dias 0–14 | D+2, D+5, D+10, D+14 | Adesão, tolerabilidade, efeitos adversos |
| **Titulação** | Dias 15–45 | Semanais | Resposta clínica, ajuste de dose |
| **Estabilização** | Dias 45–90 | Quinzenais | Manutenção, monitoramento |
| **Manutenção** | 90+ | Mensais/bimestrais | Acompanhamento de longo prazo |

Cada fase define `entry_criteria` e `exit_criteria` para transições adaptativas.

---

### Parte 3: WhatsApp Integration

**Contratos:**
- `FollowupResponse.channel` — `whatsapp`, `app`, `sms`, `email`, `phone`
- `FollowupCheckpoint.auto_trigger` — dispara automaticamente via scheduler
- `FollowupQuestionnaire.estimated_duration_minutes` — otimização de UX

**Fluxo:**
```
Scheduler → WhatsApp Agent → Questionário → Resposta → Event Bus → Digital Twin
```

---

### Parte 4: Follow-up Events (Event Bus)

**6 novos eventos no Event Catalog:**

| Evento | Domínio | Prioridade | Consumers |
|--------|---------|-----------|-----------|
| `FOLLOWUP_STARTED` | followup | NORMAL | audit, knowledge, digital_twin, connect |
| `FOLLOWUP_COMPLETED` | followup | NORMAL | audit, knowledge, digital_twin |
| `FOLLOWUP_RESPONSE_RECEIVED` | followup | NORMAL | audit, knowledge, digital_twin, followup_engine |
| `FOLLOWUP_ALERT_TRIGGERED` | followup | HIGH/CRITICAL | audit, connect, digital_twin |
| `FOLLOWUP_ESCALATED` | followup | CRITICAL | audit, connect, concierge |
| `FOLLOWUP_PHASE_CHANGED` | followup | NORMAL | audit, knowledge, digital_twin |

---

### Parte 5: Rule Engine

**Arquivo:** `araos/followup/rules/engine.py`

**Regras built-in:**
| Regra | Condição | Ação | Severidade |
|-------|----------|------|------------|
| `severe_adverse_effect` | Efeito adverso >= 7/10 | alertar médico | CRITICAL |
| `no_clinical_response` | Ausência de resposta | criar revisão | HIGH |
| `patient_no_response` | 3+ tentativas sem resposta | reengajar | MEDIUM |
| `patient_requests_help` | Solicitação de ajuda | escalar imediatamente | CRITICAL |
| `dose_tolerance_issue` | Problema de tolerância | alertar médico | HIGH |
| `worsening_symptoms` | Piora de sintomas | criar revisão | HIGH |

**API:**
```python
engine = FollowupRuleEngine()
engine.register_rule(FollowupRule(
    rule_id="custom_rule",
    name="Regra Custom",
    condition="severe_adverse_effect",
    actions=["alert_physician"],
    severity=AlertSeverity.CRITICAL,
))
alerts = engine.evaluate(program, response)
```

---

### Parte 6: Digital Twin Integration

Toda resposta processada pelo `AdaptiveFollowupEngine`:
1. Atualiza `FollowupProgram.responses`
2. Recalcula `adherence_rate` e `response_rate`
3. Avalia regras e gera alertas
4. Emite eventos para o Event Bus
5. Atualiza Digital Twin via eventos (consumers)

---

### Parte 7: Specialty Integration

**Arquivo:** `araos/followup/core/specialty_integration.py`

`SpecialtyFollowupProgram` permite que cada especialidade registre:
- Fases terapêuticas
- Questionários
- Regras

```python
specialty_program = SpecialtyFollowupProgram(
    specialty_code="cannabis",
    name="Acompanhamento Cannabis",
)
specialty_program.add_phase(phase_initial)
specialty_program.add_questionnaire(q_pain)
specialty_program.add_rule(rule_severe_ae)

# Instanciar para paciente
program = specialty_program.create_program("id", "patient_id", "tenant_id")
```

---

### Parte 8: Observabilidade

**Arquivo:** `araos/followup/observability/metrics.py`

**Métricas:**
| Métrica | Descrição |
|---------|-----------|
| `response_rate` | Taxa de resposta do paciente |
| `adherence_rate` | Taxa de adesão ao tratamento |
| `alert_generated` | Alertas gerados |
| `escalation` | Escalonamentos |
| `satisfaction` | Satisfação do paciente |
| `intervention_time_hours` | Tempo até intervenção |

---

### Parte 9: Cannabis Follow-up V1

**Arquivo:** `araos/followup/programs/cannabis/program.py`

**Estrutura completa:**
- 4 fases (Início, Titulação, Estabilização, Manutenção)
- 13 checkpoints
- 6 questionários
- 4 regras de escalonamento

**Checkpoints:**
| Fase | Checkpoints |
|------|-------------|
| Início (0–14d) | D+2, D+5, D+10, D+14 |
| Titulação (15–45d) | D+21, D+28, D+35, D+42 |
| Estabilização (45–90d) | D+60, D+75, D+90 |
| Manutenção (90d+) | M4, M5, M6 |

---

### Parte 10: Questionários Cannabis

**6 questionários:**

| Questionário | ID | Perguntas | Foco |
|-------------|-----|-----------|------|
| Avaliação de Dor | `cannabis_pain_v1` | 3 | Intensidade, sono, atividades |
| Avaliação de Ansiedade | `cannabis_anxiety_v1` | 2 | Nível, crises de pânico |
| Avaliação do Sono | `cannabis_sleep_v1` | 2 | Qualidade, horas |
| Qualidade de Vida | `cannabis_qol_v1` | 1 | Geral |
| Efeitos Adversos | `cannabis_adverse_v1` | 6 | Sonolência, tontura, boca seca, ansiedade paradoxal, taquicardia, severidade |
| Adesão | `cannabis_adherence_v1` | 3 | Tomou corretamente, doses esquecidas, interrompeu |

---

### Parte 11: Escalonamento

**4 regras de escalonamento no programa Cannabis:**

| Regra | Gatilho | Severidade |
|-------|---------|------------|
| Efeito Adverso Grave | AE >= 7/10 | CRITICAL |
| Piora dos Sintomas | Piora significativa | HIGH |
| Ausência de Resposta | 3+ tentativas sem resposta | MEDIUM |
| Solicitação de Ajuda | Paciente pede ajuda | CRITICAL |

**Alertas automáticos quando:**
- Evento adverso grave
- Piora importante
- Solicitação explícita do paciente
- Ausência de melhora após período definido

---

## NÃO IMPLEMENTADO (por design)

- ❌ Diagnóstico automático
- ❌ Ajuste automático de dose
- ❌ Recomendação terapêutica automática

**A decisão clínica permanece com o profissional.**

---

## Testes

```bash
python -m pytest tests/test_week11a_followup.py -v
```

**Resultado:** 50 passed, 0 failed

### Testes por categoria

| Categoria | Testes | Status |
|-----------|--------|--------|
| Follow-up Core | 7 | ✅ |
| Adaptive Phases | 2 | ✅ |
| WhatsApp Integration | 2 | ✅ |
| Follow-up Events | 4 | ✅ |
| Rule Engine | 4 | ✅ |
| Digital Twin Integration | 2 | ✅ |
| Specialty Integration | 2 | ✅ |
| Observabilidade | 6 | ✅ |
| Cannabis Program | 6 | ✅ |
| Cannabis Questionnaires | 4 | ✅ |
| Escalonamento | 6 | ✅ |
| Full Integration | 5 | ✅ |

---

## Testes completos (Weeks 6 + 7A + 7B + 8 + 10 + 11A)

```bash
python -m pytest tests/test_week*.py -v
```

**Resultado:** 224 passed, 0 failed

| Semana | Testes | Status |
|--------|--------|--------|
| Week 6 (Fluxos MVP) | 11 | ✅ |
| Week 7A (Hardening) | 17 | ✅ |
| Week 7B (Intelligence) | 32 | ✅ |
| Week 8 (Knowledge) | 46 | ✅ |
| Week 10 (Specialty Framework) | 68 | ✅ |
| Week 11A (Follow-up Engine) | 50 | ✅ |
| **Total** | **224** | **✅** |

---

## Arquivos Criados/Modificados

### Novos (Week 11A)
| Arquivo | Descrição |
|---------|-----------|
| `araos/followup/__init__.py` | Exportações do pacote |
| `araos/followup/core/__init__.py` | Exportações do core |
| `araos/followup/core/models.py` | Program, Phase, Checkpoint, Questionnaire, Response, Rule, Alert |
| `araos/followup/core/engine.py` | AdaptiveFollowupEngine |
| `araos/followup/core/specialty_integration.py` | SpecialtyFollowupProgram |
| `araos/followup/rules/__init__.py` | Exportações das regras |
| `araos/followup/rules/engine.py` | FollowupRuleEngine com 6 built-in conditions |
| `araos/followup/events/__init__.py` | Exportações dos eventos |
| `araos/followup/events/events.py` | 6 funções de criação de eventos |
| `araos/followup/observability/__init__.py` | Exportações de observabilidade |
| `araos/followup/observability/metrics.py` | FollowupObservability + FollowupMetric |
| `araos/followup/programs/__init__.py` | Exportações dos programas |
| `araos/followup/programs/cannabis/__init__.py` | Exportações do programa Cannabis |
| `araos/followup/programs/cannabis/program.py` | Programa Cannabis completo (4 fases, 13 checkpoints, 6 questionários, 4 regras) |
| `tests/test_week11a_followup.py` | 50 testes |
| `docs/WEEK11A_ADAPTIVE_FOLLOWUP.md` | Esta documentação |

### Modificados
| Arquivo | Mudança |
|---------|---------|
| `araos/platform/events/catalog.py` | 6 novos eventos de follow-up |
| `araos/platform/sdk/__init__.py` | Exporta Follow-up Engine |

---

## Checklist do CTO

| # | Requisito | Status |
|---|-----------|--------|
| 1 | Follow-up Core (program, phase, checkpoint, questionnaire, response, rule, alert) | ✅ |
| 2 | Adaptive Phases (initial, titration, stabilization, maintenance) | ✅ |
| 3 | WhatsApp Integration contracts | ✅ |
| 4 | 6 Follow-up Events no Event Bus | ✅ |
| 5 | Rule Engine (SE/ENTÃO) | ✅ |
| 6 | Digital Twin Integration | ✅ |
| 7 | Specialty Integration (SpecialtyFollowupProgram) | ✅ |
| 8 | Observabilidade (taxas, adesão, alertas, escalonamentos) | ✅ |
| 9 | Cannabis Follow-up V1 (4 fases, 13 checkpoints) | ✅ |
| 10 | Questionários Cannabis (6 questionários, 18 perguntas) | ✅ |
| 11 | Escalonamento (4 regras automáticas) | ✅ |
| 12 | Nenhum diagnóstico automático | ✅ |
| 13 | Nenhum ajuste automático de dose | ✅ |
| 14 | SDK exporta todos os componentes | ✅ |
| 15 | Todos os testes passando | ✅ (224/224) |

---

## Próximos Passos

**AraOS Week 11B+ — Módulos Especializados Operacionais**

Agora que o Adaptive Follow-up Engine está operacional:
- ✅ Motor universal de acompanhamento longitudinal
- ✅ Cannabis como primeiro programa real
- ✅ Regras de escalonamento automático
- ✅ Integração com Event Bus, Digital Twin, Specialty Framework
- ✅ 224 testes da plataforma passando

Próximas capacidades:
1. **Cannabis Module v2** — regras clínicas específicas, ajuste de dose supervisionado
2. **Nutrology Follow-up** — jornada de perda de peso
3. **Psychiatry Follow-up** — monitoramento de medicação
4. **Connect Layer** — integração real com WhatsApp
5. **Scheduler** — agendamento automático de checkpoints

**O AraOS deixou de ser prontuário. Tornou-se plataforma de acompanhamento contínuo.** 🏥🌿📱
