# AraFlow — Sistema de Analytics

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** Product Owner + Data Engineer
>
> Analytics do AraFlow são divididos em **4 camadas**: produto, clínica, técnica e pesquisa. Todas respeitam LGPD com privacidade por padrão.

---

## Sumário

1. Princípios
2. Camadas de analytics
3. Eventos do produto (paciente)
4. Eventos do produto (profissional)
5. Métricas clínicas
6. Escalas padronizadas
7. Dashboards
8. Relatórios
9. Alertas clínicos
10. Telemetria técnica
11. Armazenamento e retenção
12. Privacidade e LGPD
13. Analytics para pesquisa (futuro)
14. Stack técnica sugerida
15. KPIs e metas

---

## 1. Princípios

1. **Mínimo necessário.** Coletar só o que gera valor.
2. **Consentimento explícito** para qualquer dado além de uso básico.
3. **Anonimização por padrão** em qualquer análise populacional.
4. **Nada de dark analytics** (rastreamento agressivo, fingerprinting).
5. **Transparência**: usuário vê o que é coletado.
6. **Servidores no Brasil** (LGPD).

---

## 2. Camadas de analytics

```
┌────────────────────────────────────────────┐
│ 1. Uso de produto                          │ ← produto (sempre)
├────────────────────────────────────────────┤
│ 2. Clínico (adesão, escores)               │ ← opt-in por paciente
├────────────────────────────────────────────┤
│ 3. Pesquisa (desfechos, comparativos)      │ ← consentimento específico
├────────────────────────────────────────────┤
│ 4. Telemetria técnica                      │ ← SRE / segurança
└────────────────────────────────────────────┘
```

---

## 3. Eventos do produto (paciente)

### 3.1 Onboarding

| Evento | Propriedades |
|--------|--------------|
| `onboarding_started` | — |
| `onboarding_step_completed` | `step`, `duration_ms` |
| `onboarding_completed` | `total_duration_ms` |
| `onboarding_skipped` | `at_step` |

### 3.2 Sessão

| Evento | Propriedades |
|--------|--------------|
| `session_started` | `protocol_id`, `source` (prescrito/explorar/sos) |
| `session_phase_changed` | `phase`, `time_in_phase_ms` |
| `session_paused` | `time_elapsed_ms` |
| `session_resumed` | `time_elapsed_ms` |
| `session_completed` | `protocol_id`, `total_duration_ms`, `completion_pct`, `subjective_rating?` |
| `session_aborted` | `protocol_id`, `reason` (user/adverse/technical) |
| `session_adverse_event` | `type` (dizziness, panic, etc.) |
| `session_audio_changed` | `track`, `volume` |

### 3.3 Visual

| Evento | Propriedades |
|--------|--------------|
| `visual_changed` | `from`, `to`, `reason` |

### 3.4 Engajamento

| Evento | Propriedades |
|--------|--------------|
| `streak_extended` | `new_streak` |
| `streak_broken` | `previous_streak` |
| `achievement_unlocked` | `achievement_id` |
| `notification_received` | `type` |
| `notification_action` | `type`, `action` (open/dismiss) |

### 3.5 Conteúdo

| Evento | Propriedades |
|--------|--------------|
| `protocol_explored` | `protocol_id`, `source` |
| `protocol_favorited` | `protocol_id` |
| `protocol_started` | `protocol_id` |

### 3.6 LGPD

| Evento | Propriedades |
|--------|--------------|
| `consent_updated` | `consents` |
| `data_exported` | `format` |
| `account_deleted` | — |

---

## 4. Eventos do produto (profissional)

| Evento | Propriedades |
|--------|--------------|
| `prescription_created` | `protocol_id`, `patient_id`, `dose` |
| `prescription_modified` | `protocol_id`, `change_type` |
| `prescription_ended` | `protocol_id`, `reason` |
| `patient_viewed` | `patient_id` |
| `clinical_note_added` | `patient_id`, `length` |
| `library_protocol_viewed` | `protocol_id` |

---

## 5. Métricas clínicas

### 5.1 Adesão

| Métrica | Fórmula |
|---------|---------|
| **Sessões prescritas** | Σ sessões previstas |
| **Sessões realizadas** | Σ sessões concluídas |
| **Taxa de adesão** | realizadas / prescritas × 100 |
| **Minutos acumulados** | Σ duração efetiva |
| **Sequência atual** | dias consecutivos com ≥ 1 sessão |
| **Sequência máxima** | maior sequência histórica |
| **Frequência semanal** | sessões/semana (média 4 sem) |
| **Dias sem sessão** | dias desde a última sessão |

### 5.2 Resposta clínica (Fase 2)

| Métrica | Origem |
|---------|--------|
| **GAD-7 delta** | Diferença pré/pós |
| **ISI delta** | Diferença pré/pós |
| **PSS-10 delta** | Diferença pré/pós |
| **EVA dor delta** | Diferença pré/pós |
| **% respondedores** | ≥ 50% redução no escore |
| **Tempo até resposta** | Semanas até melhora significativa |

### 5.3 Engajamento

| Métrica | Origem |
|---------|--------|
| **Sessões por horário** | Histograma |
| **Sessões por objetivo** | Distribuição |
| **% sessões concluídas vs iniciadas** | Funil |
| **Retenção D7/D30/D90** | Coortes |

---

## 6. Escalas padronizadas (Fase 2)

### 6.1 Inventário

| Escala | Domínio | Itens | Tempo | Pontuação |
|--------|---------|-------|-------|-----------|
| **GAD-7** | Ansiedade | 7 | 2–3 min | 0–21 |
| **PHQ-9** | Depressão | 9 | 2–3 min | 0–27 |
| **ISI** | Insônia | 7 | 2–3 min | 0–28 |
| **PSS-10** | Estresse percebido | 10 | 3–4 min | 0–40 |
| **EVA dor** | Intensidade de dor | 1 | 30s | 0–10 |
| **WHO-5** | Bem-estar | 5 | 1 min | 0–25 |
| **MFI-20** | Fadiga | 20 | 5 min | 0–100 |

### 6.2 Cadência

| Escala | Cadência sugerida |
|--------|-------------------|
| GAD-7 | A cada 4 semanas |
| PHQ-9 | A cada 4 semanas (se escore alto) |
| ISI | A cada 2 semanas (em tratamento de sono) |
| PSS-10 | A cada 4 semanas |
| EVA dor | Semanal |
| WHO-5 | Mensal |
| MFI-20 | A cada 4 semanas |

### 6.3 UX da escala

- **Não na primeira sessão.**
- **Após 7 dias de uso** (mínimo).
- **Curta e respeitosa**.
- **Nunca obrigatória**.
- Profissional vê resultados consolidados.

---

## 7. Dashboards

### 7.1 Dashboard do paciente

```
┌──────────────────────────────────────┐
│ Seu progresso — Junho                │
│                                      │
│ ┌────────┐ ┌────────┐ ┌────────┐    │
│ │   12   │ │  60    │ │  7 🔥  │    │
│ │sessões │ │ minutos│ │ streak │    │
│ └────────┘ └────────┘ └────────┘    │
│                                      │
│ Últimos 7 dias                       │
│ ▁▂▃▅▇▆▇                               │
│                                      │
│ Como você tem se sentido             │
│ (escala 1-5, últimas 4 semanas)      │
│ ▁▃▄▆                                  │
│                                      │
│ Categorias mais usadas               │
│ • Ansiedade  ▇▇▇▇▇▇▇ 60%             │
│ • Sono       ▇▇▇▇   30%             │
│ • Foco       ▇      10%              │
│                                      │
│ [ Relatório completo ]               │
│ [ Compartilhar com profissional ]    │
└──────────────────────────────────────┘
```

### 7.2 Dashboard do profissional

```
┌──────────────────────────────────────┐
│ Carlos Henrique — Última: hoje       │
│                                      │
│ Prescrição ativa: 4-7-8 • 5 min • 2x│
│                                      │
│ Adesão (últ. 30d)                    │
│ ████████░░ 86%                       │
│                                      │
│ Escalas                              │
│ GAD-7: 16 → 11 (Δ -5 ✓)              │
│ ISI:   18 → 14 (Δ -4 ✓)              │
│                                      │
│ Alertas                              │
│ ⚠ Carlos pulou 2 dias                │
│                                      │
│ Notas clínicas                       │
│ [...............]                    │
│ [ Salvar ]                           │
└──────────────────────────────────────┘
```

### 7.3 Dashboard do admin

- Usuários ativos (D1, D7, D30).
- Profissionais ativos.
- Sessões/dia.
- Latência P95.
- Erros por categoria.

---

## 8. Relatórios

### 8.1 Tipos

| Relatório | Frequência | Quem |
|-----------|-----------|------|
| Diário | Diário | Paciente (push opcional) |
| Semanal | Semanal | Paciente (push opcional) |
| Mensal | Mensal | Paciente + profissional |
| Trimestral | Trimestral | Paciente |
| Clínico | Sob demanda | Profissional |
| Pesquisa | Sob demanda | Pesquisador (anonimizado) |

### 8.2 Formatos

- **In-app** (visual).
- **PDF** (para compartilhar com profissional de fora do AraOS).
- **CSV** (para análise pessoal).
- **JSON** (LGPD).

---

## 9. Alertas clínicos

### 9.1 Tipos

| Alerta | Regra |
|--------|-------|
| **Queda de adesão** | < 50% por 7 dias seguidos |
| **Efeito adverso** | Evento adverso reportado |
| **Escala crítica** | GAD-7 ≥ 15 ou PHQ-9 ≥ 20 |
| **Sinal de risco** | Termos-chave em notas livres |
| **Inatividade prolongada** | Sem sessão por 14 dias |

### 9.2 Canais

| Alerta | Canal |
|--------|-------|
| Adesão | Notificação ao profissional |
| Efeito adverso | Notificação imediata ao profissional |
| Escala crítica | Notificação imediata ao profissional |
| Inatividade | Mensagem suave ao paciente |

### 9.3 Tom

> Linguagem cuidadosa. Sem alarmismo. Sugere ação sem impor.

---

## 10. Telemetria técnica

| Categoria | Eventos |
|-----------|---------|
| App | Inicialização, crash, ANR |
| Sessão técnica | Início de áudio, latência |
| Rede | Online/offline, retries |
| Permissões | Granted/denied |
| Performance | FPS, uso de memória |
| Erros | Stack trace + contexto |

> Não inclui **nenhum dado clínico** ou pessoal identificável.

---

## 11. Armazenamento e retenção

| Tipo de dado | Retenção |
|--------------|----------|
| Eventos de produto | 24 meses |
| Escalas clínicas | Enquanto conta ativa + 60 meses após exclusão (anonimizado) |
| Telemetria técnica | 6 meses |
| Logs de auditoria | 60 meses (regulatório) |

> Após expiração: agregação irreversível ou exclusão.

---

## 12. Privacidade e LGPD

### 12.1 Princípios aplicados

| Princípio | Aplicação |
|-----------|-----------|
| **Finalidade** | Cada evento documenta seu propósito. |
| **Necessidade** | Coleta-se o mínimo. |
| **Transparência** | Tela "Seus dados" lista tudo coletado. |
| **Consentimento** | Opt-in por categoria (vide § 3.6). |
| **Eliminação** | Direito ao esquecimento respeitado. |
| **Portabilidade** | Exportação completa (JSON/PDF). |

### 12.2 Anonimização

- Hash de IDs pessoais para análise populacional.
- Sem nomes, e-mails, telefones em eventos.
- K-anonimato (k≥5) em qualquer dataset público.

### 12.3 Compartilhamento com profissional

- Paciente controla o que é compartilhado.
- Pode revogar a qualquer momento.
- Profissional vê apenas pacientes que autorizou.

---

## 13. Analytics para pesquisa (Fase 3)

### 13.1 Consentimento específico

- Texto claro: "Seus dados anonimizados podem ser usados em pesquisa clínica."
- Opt-in separado.
- Pode ser revogado a qualquer momento.

### 13.2 Dados disponíveis para pesquisa

- Adesão por período.
- Resposta por escala (anonimizada).
- Padrões de uso por objetivo.

### 13.3 Comitê científico

- Toda pesquisa passa por comitê.
- Resultado retorna aos participantes (resumo).

---

## 14. Stack técnica sugerida

| Camada | Ferramenta |
|--------|-----------|
| Eventos (cliente) | Segment / RudderStack / interno |
| Coleta | API própria + Kafka |
| Armazenamento | ClickHouse / BigQuery / Postgres + TimescaleDB |
| Visualização | Metabase / Looker / interno |
| Alertas | Rules engine + Slack/PagerDuty |
| ETL | dbt |
| Privacy | Hash + tokenização |

---

## 15. KPIs e metas

### 15.1 KPIs de produto

| KPI | Meta MVP (3 meses) |
|-----|---------------------|
| DAU / MAU | ≥ 25% |
| Retenção D7 | ≥ 50% |
| Retenção D30 | ≥ 25% |
| Sessões/usuário/semana | ≥ 3 |
| Adesão média a prescrições | ≥ 60% |
| NPS paciente | ≥ 40 |

### 15.2 KPIs clínicos

| KPI | Meta 12 meses |
|-----|---------------|
| % respondedores (GAD-7) | ≥ 40% |
| % respondedores (ISI) | ≥ 35% |
| Δ médio GAD-7 (aderentes) | ≥ 4 pontos |

### 15.3 KPIs técnicos

| KPI | Meta |
|-----|------|
| Uptime | ≥ 99,5% |
| Latência início sessão P95 | < 2s |
| Crash-free rate | ≥ 99% |
| Cobertura de testes de analytics | ≥ 80% |

---

*Medir para cuidar, não para vigiar.*