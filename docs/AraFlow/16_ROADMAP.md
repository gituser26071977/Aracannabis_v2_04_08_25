# AraFlow — Roadmap

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** Product Owner + Tech Lead
>
> Roadmap de evolução do AraFlow em **4 fases** ao longo de **24 meses**, do MVP ao produto clínico completo com biofeedback e IA avançada.

---

## Sumário

1. Visão geral
2. Princípios do roadmap
3. Fase 0 — Discovery (em curso)
4. Fase 1 — MVP
5. Fase 2 — Personalização e analytics clínico
6. Fase 3 — Biofeedback e IA avançada
7. Marcos transversais
8. Marcos regulatórios
9. Marcos de equipe
10. Métricas por fase
11. Riscos do roadmap
12. Revisão e atualização

---

## 1. Visão geral

```
2026                            2027                            2028
 Q3    Q4  │ Q1    Q2    Q3    Q4  │ Q1    Q2    Q3    Q4  │ Q1    Q2
────────────┼──────────────────────┼──────────────────────┼──────────
   F0       │        F1           │         F2          │    F3
Discovery   │       MVP           │  Personalização     │ Biofeedback
            │                     │   + Analytics       │  + IA
```

| Fase | Duração | Foco |
|------|---------|------|
| **F0** | 2–3 meses | Discovery + arquitetura |
| **F1** | 4–5 meses | MVP técnico + clínico |
| **F2** | 5–6 meses | Personalização + analytics clínico |
| **F3** | 6–9 meses | Biofeedback + IA avançada |

---

## 2. Princípios do roadmap

1. **Segurança clínica antes de feature.** Cada fase adiciona valor sem remover cuidado.
2. **Feedback real antes de expansão.** Validar com profissionais e pacientes antes de crescer.
3. **Estabilidade do AraOS é intocável.** AraFlow é módulo independente.
4. **LGPD desde o MVP.** Não é adicionado depois.
5. **Foco no valor.** Cortar o que não serve; dobrar no que serve.

---

## 3. Fase 0 — Discovery (em curso)

**Período:** até 2026-Q3.

**Entregas:**
- [x] 21 documentos de discovery e arquitetura.
- [ ] Entrevistas com 10 profissionais prescritores.
- [ ] Teste de usabilidade com 20 pacientes.
- [ ] Validação comitê clínico AraOS.
- [ ] Aprovação DPO + segurança.
- [ ] Decisão de classificação regulatória (MVP).

**Critério de saída:**
- Documentação aprovada.
- Personas validadas.
- MVP definido e priorizado.

---

## 4. Fase 1 — MVP

**Período:** 2026-Q4 → 2027-Q1 (5 meses).

**Objetivo:** entregar valor clínico real a 100 profissionais e 1.000 pacientes, com segurança e evidência.

### 4.1 Features (do MVP — `18_MVP.md`)

- 12 protocolos clínicos publicados.
- Player completo (visual + áudio).
- 12 trilhas de áudio.
- Modo SOS.
- Modo Idoso, Modo Infantil.
- Login via AraOS.
- Prescrição simples (1 protocolo + dose).
- Histórico do paciente.
- Adesão básica.
- LGPD completo (consentimento, exportação, exclusão).
- Acessibilidade WCAG AA.
- Analytics essenciais.

### 4.2 Marcos

| Marco | Data |
|-------|------|
| Kick-off técnico | Q4 2026 semana 1 |
| Backend MVP pronto | Q4 2026 semana 8 |
| Frontend MVP pronto | Q4 2026 semana 12 |
| Beta fechado (20 profissionais) | Q1 2027 semana 4 |
| Lançamento público | Q1 2027 semana 12 |

### 4.3 Equipe

- 1 Product Owner (dedicado)
- 1 UX Designer
- 2 Engenheiros backend
- 2 Engenheiros frontend
- 1 Engenheiro QA
- 0.5 Designer Motion
- 0.3 Engenheiro DevOps
- 0.3 DPO
- 0.3 Diretor clínico (revisão)

### 4.4 Critérios de saída

- 100 profissionais ativos prescrevendo.
- 1.000 pacientes ativos.
- Adesão média ≥ 60%.
- NPS ≥ 40.
- Sem P0/P1 em segurança.

---

## 5. Fase 2 — Personalização e analytics clínico

**Período:** 2027-Q2 → 2027-Q3 (5 meses).

**Objetivo:** tornar o AraFlow mais inteligente, mensurável e integrado ao cuidado.

### 5.1 Features

- 30+ protocolos (com variantes).
- Modelos preditivos leves (adesão, recomendação).
- Escalas clínicas (GAD-7, ISI, PSS-10, EVA, WHO-5).
- Dashboard clínico para profissional.
- Compartilhamento de progresso.
- Gamificação leve (XP, planta que cresce).
- Missões semanais.
- Insights personalizados.
- Modo profundo expandido.
- Integração mais profunda com AraOS (prontuário).
- Suporte EN.

### 5.2 Marcos

| Marco | Data |
|-------|------|
| Modelos IA v1 em produção | Q2 2027 semana 4 |
| Escalas clínicas | Q2 2027 semana 8 |
| Dashboard profissional | Q2 2027 semana 10 |
| Lançamento Fase 2 | Q3 2027 semana 12 |

### 5.3 Equipe

- Mantém base.
- +1 Engenheiro de ML.
- +1 Engenheiro de dados.
- +0.5 Designer.

### 5.4 Critérios de saída

- ≥ 30% dos profissionais usando dashboard semanal.
- ≥ 50% dos pacientes com pelo menos 1 escala preenchida.
- Modelos de personalização com AUC ≥ 0.7.
- Adesão média ≥ 65%.

---

## 6. Fase 3 — Biofeedback e IA avançada

**Período:** 2027-Q4 → 2028-Q2 (9 meses).

**Objetivo:** tornar o AraFlow a plataforma de referência em neuroregulação digital baseada em biofeedback.

### 6.1 Features

- Integração com 2+ wearables (PPG/ECG).
- HRV em tempo real durante sessão.
- Visual respiratório adaptativo ao HRV.
- Áudio modulado por biofeedback.
- IA generativa com guardrails (narração personalizada).
- Edge AI (modelos leves no dispositivo).
- Pesquisa clínica integrada (consentimento específico).
- Suporte ES.
- Modo profissional expandido (grupos).
- Certificação ANVISA (SaMD) em avaliação.

### 6.2 Marcos

| Marco | Data |
|-------|------|
| Biofeedback beta | Q1 2028 semana 4 |
| IA generativa com guardrails | Q1 2028 semana 8 |
| Pesquisa clínica autorizada | Q2 2028 semana 4 |
| Lançamento Fase 3 | Q2 2028 semana 12 |

### 6.3 Equipe

- +1 Engenheiro de ML sênior.
- +1 Engenheiro embarcado (mobile native).
- +1 Designer de motion especialista.
- +0.5 ResearchOps.
- +0.3 Especialista regulatório.

### 6.4 Critérios de saída

- ≥ 30% dos pacientes com wearable integrado.
- Coerência cardíaca média em aderentes ≥ 0.7.
- Publicação de 1 estudo clínico.
- Aprovação regulatória (ou enquadramento confirmado).

---

## 7. Marcos transversais

| Marco | Fase | Descrição |
|-------|------|-----------|
| **M1** | F0 → F1 | Aprovação do discovery |
| **M2** | F1 | Lançamento MVP |
| **M3** | F1 → F2 | Atingir 100 profissionais |
| **M4** | F2 | Lançamento IA preditiva |
| **M5** | F2 → F3 | Atingir 1.000 profissionais |
| **M6** | F3 | Biofeedback em produção |
| **M7** | F3 | Certificação regulatória |
| **M8** | F3+ | Expansão internacional |

---

## 8. Marcos regulatórios

| Marco | Fase | Descrição |
|-------|------|-----------|
| **R1** | F0 | Classificação regulatória (wellness vs SaMD) |
| **R2** | F1 | LGPD compliance audit |
| **R3** | F2 | Avaliação SaMD inicial |
| **R4** | F3 | Submissão ANVISA (se aplicável) |
| **R5** | F3+ | GDPR compliance (se expansão UE) |

---

## 9. Marcos de equipe

| Marco | Fase | Descrição |
|-------|------|-----------|
| **E1** | F0 | Squad AraFlow formado |
| **E2** | F1 | Onboarding completo |
| **E3** | F2 | Time expandido |
| **E4** | F3 | Cultura de pesquisa clínica |

---

## 10. Métricas por fase

### 10.1 Fase 1 (MVP)

| Categoria | Métrica | Meta |
|-----------|---------|------|
| Adoção | Profissionais com prescrição ativa | 100 |
| Adoção | Pacientes ativos (1 sessão/semana) | 1.000 |
| Adesão | Sessões concluídas / prescritas | ≥ 60% |
| Engajamento | Sessões médias/paciente/semana | ≥ 3 |
| Qualidade | NPS paciente | ≥ 40 |
| Técnico | Uptime | ≥ 99,5% |
| Técnico | Latência P95 início de sessão | < 2s |
| Segurança | Incidentes P0/P1 | 0 |

### 10.2 Fase 2

| Categoria | Métrica | Meta |
|-----------|---------|------|
| Adoção | Profissionais ativos | 500 |
| Adoção | Pacientes ativos | 5.000 |
| Adesão | Adesão média | ≥ 65% |
| Clínica | Δ médio GAD-7 (aderentes) | ≥ 4 pontos |
| IA | AUC modelo de recomendação | ≥ 0,7 |
| Engajamento | Retenção D30 | ≥ 35% |

### 10.3 Fase 3

| Categoria | Métrica | Meta |
|-----------|---------|------|
| Adoção | Profissionais ativos | 2.000 |
| Adoção | Pacientes ativos | 50.000 |
| Clínica | Publicação de estudo | 1 |
| Biofeedback | % pacientes com wearable | ≥ 30% |
| Biofeedback | Coerência média em aderentes | ≥ 0,7 |
| Regulatório | SaMD aprovado (se aplicável) | — |

---

## 11. Riscos do roadmap

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Atraso no MVP | Média | Alto | Sprints curtos; cortes claros. |
| Baixa adesão | Média | Alto | IA, UX, gamificação. |
| Resistência regulatória | Média | Alto | Jurídico desde F0. |
| Dependência AraOS | Baixa | Alto | Contrato claro de SLA. |
| Escassez de profissionais prescritores | Média | Médio | Programa de embaixadores. |
| Mudança de mercado | Baixa | Médio | Revisões trimestrais. |
| Problema com biblioteca de áudio | Baixa | Médio | Múltiplos fornecedores. |

---

## 12. Revisão e atualização

- **Revisão quinzenal** do progresso (squad interno).
- **Revisão mensal** com stakeholders.
- **Revisão trimestral** com diretoria.
- **Revisão anual** completa do roadmap.

> Mudanças de prazo são comunicadas com **30 dias de antecedência**.

---

*Roadmap é hipótese. Valide com dados reais e ajuste.*