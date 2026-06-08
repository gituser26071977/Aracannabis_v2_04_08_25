# 🌿 Week 11B — Cannabis Module V1

> **Tag:** `v0.7.0-alpha`  
> **Data:** 2025-06-06  
> **Testes:** 276 passando (52 novos)  
> **Arquivos:** 25 novos, 2 modificados  

---

## 🎯 Visão Geral

Primeiro módulo de especialidade completo (`araos/specialties/cannabis/`), provando o princípio arquitetural:

> **"A plataforma é o centro. As especialidades são plugins."**

O Cannabis Module integra **todas** as camadas da plataforma AraOS:
- Specialty Framework
- Adaptive Follow-up Engine
- Digital Twin
- Knowledge Layer
- Intelligence Layer (Trust Levels)
- Event Bus

---

## 📦 Componentes Entregues

### 1. Perfil Terapêutico (`profile/`)
- `CannabisProfile` — perfil completo do paciente em tratamento com cannabis
- `TherapeuticGoal` — metas mensuráveis (dor, sono, ansiedade, qualidade de vida)
- `EligibilityStatus` — elegibilidade com motivo documentado

### 2. Registro de Medicamentos (`medication/`)
- `CannabisProductRegistry` — registro de produtos autorizados
- `ProductType` — categorias: ÓLEO, FLOR, CÁPSULA, TOPICO, SEMENTE, OUTRO
- `ProductRoute` — vias de administração

### 3. Linha do Tempo de Doses (`dose/`)
- `DoseTimeline` — histórico longitudinal de todas as doses administradas
- `DoseEvent` — evento individual com produto, quantidade, via, contexto
- `CurrentDoseSnapshot` — estado atual consolidado

### 4. Motor de Desfechos (`outcome/`)
- `CannabisOutcome` — acompanhamento de sintomas-alvo ao longo do tempo
- `OutcomeEngine.analyze()` — cálculo de tendências (melhora/piora/estável)
- `TrendDirection` — IMPROVING, WORSENING, STABLE, INCONCLUSIVE
- Requer ≥3 pontos de dados para tendência conclusiva

### 5. Sistema de Alertas (`alerts/`)
- `AlertSeverity` — INFO, LOW, MEDIUM, HIGH, CRITICAL
- `AlertRule` — regras configuráveis (ex: dose > limite, efeito adverso)
- `AlertEngine` — motor de avaliação contínua
- `AlertState` — ACTIVE, ACKNOWLEDGED, RESOLVED, DISMISSED

### 6. Agente Cannabis (`agent/`)
- `CannabisAgent` — respostas **somente leitura** sobre dados estruturados
- `generate_therapeutic_summary()` → `TrustedResponse` (`GENERATED_SUMMARY`)
- `answer_longitudinal_evolution()` → `TrustedResponse` (`STRUCTURED_DATA`)
- `answer_dose_history()` → `TrustedResponse` (`STRUCTURED_DATA`)
- `answer_adverse_effects()` → `TrustedResponse` (`STRUCTURED_DATA`)
- **Nunca** usa `AI_INFERENCE` sem marcação explícita
- `requires_human_verification()` garante que apenas inferências precisam de revisão

### 7. Dashboard (`dashboard/`)
- `CannabisDashboard` — visão unificada do tratamento
- `TreatmentStatus` — ACTIVE, PAUSED, DISCONTINUED, COMPLETED

### 8. Camada de Conhecimento (`knowledge/`)
- Integração com Knowledge Layer para protocolos e evidências
- `CannabisKnowledgeAdapter` — busca contextualizada por especialidade

### 9. Eventos (`events/`)
- 7 novos eventos no Event Catalog:
  - `CANNABIS_STARTED`
  - `CANNABIS_PRODUCT_ADDED`
  - `CANNABIS_PRODUCT_CHANGED`
  - `CANNABIS_DOSE_CHANGED`
  - `CANNABIS_OUTCOME_RECORDED`
  - `CANNABIS_ALERT_TRIGGERED`
  - `CANNABIS_DISCONTINUED`
- Domínio: `cannabis`, aggregate: `cannabis_treatment`
- Consumers: `audit`, `clinical`, `knowledge`, `followup`

---

## 🧪 Testes

```bash
$ python -m pytest tests/test_week11b_cannabis.py -q
52 passed in 0.70s
```

Cobertura:
- Criação de perfil terapêutico
- Registro e troca de produtos
- Timeline de doses com snapshots
- Análise de desfechos e tendências
- Geração e gestão de alertas
- Respostas do agente com Trust Levels
- Jornada completa do paciente (4 fases)
- Integração com Event Bus

---

## 🔒 Princípios de Segurança Clínica

| Princípio | Implementação |
|-----------|---------------|
| **Sem automação diagnóstica** | Agente apenas lê dados estruturados |
| **Sem ajuste automático de dose** | DoseTimeline registra; não prescreve |
| **Sem prescrição automática** | ProductRegistry é catálogo; não receituário |
| **Trust Levels obrigatórios** | Toda resposta AI carrega proveniência |
| **Revisão humana para inferências** | `requires_human_verification()` em `AI_INFERENCE` |

---

## 📊 Métricas do Projeto

| Semana | Testes | Arquivos | Tag |
|--------|--------|----------|-----|
| W6 | 11 | - | - |
| W7A | +28 | 12 | - |
| W7B | +32 | 16 | - |
| W8 | +46 | 12 | `v0.4.0-alpha` |
| W10 | +68 | 23 | `v0.5.0-alpha` |
| W11A | +50 | 18 | `v0.6.0-alpha` |
| **W11B** | **+52** | **25** | **`v0.7.0-alpha`** |
| **Total** | **276** | **120+** | - |

---

## 🔄 Próximos Passos (Week 12)

- [ ] Digital Twin v2: sincronização bidirecional com cannabis events
- [ ] Prescrição digital integrada (Anvisa RDC 327/2019)
- [ ] Integração com farmácias de manipulação parceiras
- [ ] Módulo de telemedicina para acompanhamento remoto
- [ ] Reporte de eventos adversos à ANVISA (fluxo automático)

---

*AraOS — Cannabis Module V1. Construído com responsabilidade clínica.*
