# AraFlow — Backlog Priorizado

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** Product Owner
>
> Backlog completo priorizado por **valor clínico + viabilidade técnica + risco regulatório**. Itens agrupados em épicos.

---

## Sumário

1. Metodologia de priorização
2. Épicos
3. Backlog Fase 1 (MVP) — detalhado
4. Backlog Fase 2
5. Backlog Fase 3
6. Backlog contínuo (transversal)
7. Dependências críticas
8. Critérios de "pronto"
9. Anti-backlog (itens descartados)
10. Próximas revisões

---

## 1. Metodologia de priorização

Usamos **RICE + ajuste clínico**:

| Critério | Peso |
|----------|------|
| **Reach** (alcance) | 1x |
| **Impact** (impacto clínico) | 2x |
| **Confidence** (confiança na estimativa) | 0.5x |
| **Effort** (esforço) | -1x |
| **Risco clínico** | bônus (se risco alto, sobe) |
| **Risco regulatório** | bônus (se alto, desce) |

> Score final prioriza itens de **alto impacto clínico, baixa complexidade**.

---

## 2. Épicos

| Código | Épico | Fase |
|--------|-------|------|
| **E1** | Identidade e autenticação | F1 |
| **E2** | Biblioteca de protocolos | F1 |
| **E3** | Player de sessão | F1 |
| **E4** | Áudio terapêutico | F1 |
| **E5** | Visual respiratório | F1 |
| **E6** | Modos especiais (SOS, Idoso, Infantil) | F1 |
| **E7** | Prescrição | F1 |
| **E8** | Histórico e adesão | F1 |
| **E9** | Gamificação inicial | F1 |
| **E10** | LGPD | F1 |
| **E11** | Acessibilidade | F1 |
| **E12** | Telemetria e analytics essenciais | F1 |
| **E13** | Personalização preditiva | F2 |
| **E14** | Escalas clínicas | F2 |
| **E15** | Dashboard clínico | F2 |
| **E16** | Integração AraOS (prontuário) | F2 |
| **E17** | Gamificação avançada | F2 |
| **E18** | Internacionalização (EN) | F2 |
| **E19** | Biofeedback (HRV) | F3 |
| **E20** | IA generativa | F3 |
| **E21** | Pesquisa clínica | F3 |
| **E22** | Certificação SaMD | F3 |
| **E23** | Internacionalização (ES) | F3 |
| **E24** | Edge AI | F3 |

---

## 3. Backlog Fase 1 (MVP) — detalhado

### E1 — Identidade e autenticação

| Item | Prioridade | Esforço | Dependências |
|------|-----------|---------|--------------|
| Login via AraOS (SSO) | P0 | M | — |
| Refresh token | P0 | S | E1.Login |
| Logout | P0 | S | E1.Login |
| Perfil mínimo (objetivo, idioma) | P0 | S | E1.Login |

### E2 — Biblioteca de protocolos

| Item | Prioridade | Esforço | Dependências |
|------|-----------|---------|--------------|
| Schema e seed dos 12 protocolos MVP | P0 | M | — |
| Página de detalhe do protocolo | P0 | M | E2.Seed |
| Página de listagem com filtros | P0 | M | E2.Seed |
| Busca textual | P1 | M | E2.Lista |
| Sistema de tags (domínio, intensidade) | P0 | S | E2.Seed |
| Sistema de versionamento | P1 | M | E2.Seed |

### E3 — Player de sessão

| Item | Prioridade | Esforço | Dependências |
|------|-----------|---------|--------------|
| Estado de sessão (fase atual, ciclo) | P0 | M | E2.Seed |
| Visualização base (círculo) | P0 | M | E3.Estado |
| Cronômetro + barra de progresso | P0 | S | E3.Estado |
| Controles (pausar, encerrar) | P0 | S | E3.Estado |
| Registro de sessão (final) | P0 | M | E3.Estado |
| Tela de conclusão | P0 | S | E3.Registro |
| Avaliação subjetiva pós-sessão | P1 | S | E3.Conclusão |
| Tratamento de offline | P0 | M | E3.Registro |
| Tela de segurança clínica (SAMU/CVV) | P0 | S | E3.Estado |

### E4 — Áudio terapêutico

| Item | Prioridade | Esforço | Dependências |
|------|-----------|---------|--------------|
| Player de áudio (12 trilhas) | P0 | M | — |
| Streaming adaptativo | P1 | M | E4.Player |
| Cache local (últimas 5) | P1 | S | E4.Player |
| 3 trilhas offline embarcadas | P1 | M | E4.Player |
| Metronômo respiratório | P0 | M | E3.Estado |
| Controle de volume | P0 | S | E4.Player |
| Mute total | P0 | S | E4.Player |
| Narração feminina PT-BR | P1 | M | E4.Player |
| Paisagens sonoras (3) | P1 | S | E4.Player |

### E5 — Visual respiratório

| Item | Prioridade | Esforço | Dependências |
|------|-----------|---------|--------------|
| Círculo respiratório (SVG + CSS) | P0 | M | E3.Estado |
| Crescimento/decrescimento animado | P0 | S | E5.Círculo |
| Glow interno | P1 | S | E5.Círculo |
| Modo reduzido (prefers-reduced-motion) | P0 | S | E5.Círculo |
| Troca de visual em sessão (futuro, P2) | P2 | M | E5.Círculo |

### E6 — Modos especiais

| Item | Prioridade | Esforço | Dependências |
|------|-----------|---------|--------------|
| SOS 60 segundos (acesso rápido) | P0 | S | E3.Player |
| Modo Idoso (acessibilidade ampliada) | P0 | M | E11.Acessibilidade |
| Modo Infantil (visual lúdico) | P1 | M | E5.Visual, E11.Acessibilidade |

### E7 — Prescrição

| Item | Prioridade | Esforço | Dependências |
|------|-----------|---------|--------------|
| Tela de seleção de paciente | P0 | M | E1.Login |
| Tela de seleção de protocolo | P0 | M | E2.Seed |
| Tela de dose e horário | P0 | S | E7.Protocolo |
| Confirmação de prescrição | P0 | S | E7.Dose |
| Lista de prescrições ativas (paciente) | P0 | M | E7.Confirmação |
| Lista de pacientes (profissional) | P0 | M | E1.Login |
| Ajuste de prescrição | P1 | M | E7.Confirmação |
| Encerramento de prescrição | P1 | S | E7.Confirmação |

### E8 — Histórico e adesão

| Item | Prioridade | Esforço | Dependências |
|------|-----------|---------|--------------|
| Histórico de sessões (paciente) | P0 | M | E3.Registro |
| Sumário de progresso | P0 | M | E8.Histórico |
| Cálculo de streak | P0 | S | E3.Registro |
| Tela de progresso | P0 | S | E8.Sumário |
| Adesão por prescrição (profissional) | P1 | M | E8.Sumário |

### E9 — Gamificação inicial

| Item | Prioridade | Esforço | Dependências |
|------|-----------|---------|--------------|
| Streak (visual + persistência) | P0 | M | E3.Registro |
| Conquistas básicas (5-7) | P1 | M | E9.Streak |
| Mensagens calorosas | P0 | S | E9.Streak |
| Re-engajamento (7 dias) | P1 | S | E9.Streak |

### E10 — LGPD

| Item | Prioridade | Esforço | Dependências |
|------|-----------|---------|--------------|
| Tela de consentimento granular | P0 | M | E1.Login |
| Consent log (auditoria) | P0 | S | E10.Consentimento |
| Tela "Seus dados" | P0 | M | E10.Consentimento |
| Exportação JSON | P0 | M | E10.Tela |
| Exportação PDF | P1 | M | E10.Exportação |
| Solicitação de exclusão (60 dias) | P0 | M | E10.Tela |
| Cancelamento de exclusão | P0 | S | E10.Exclusão |
| Política de privacidade | P0 | S | — |
| Termos de uso | P0 | S | — |
| RIPD atualizado | P0 | M | — |

### E11 — Acessibilidade

| Item | Prioridade | Esforço | Dependências |
|------|-----------|---------|--------------|
| WCAG AA nas 5 telas principais | P0 | M | E2-E8 |
| Modo alto contraste | P0 | S | E11.WCAG |
| Tamanho de texto ajustável | P0 | S | E11.WCAG |
| Áreas de toque ≥ 44×44 | P0 | S | E11.WCAG |
| Suporte a leitor de tela | P0 | M | E11.WCAG |
| `prefers-reduced-motion` | P0 | S | E5 |
| Versão "sem áudio" | P1 | S | E4 |
| Versão "sem animação" | P1 | S | E5 |

### E12 — Telemetria e analytics essenciais

| Item | Prioridade | Esforço | Dependências |
|------|-----------|---------|--------------|
| Eventos básicos (sessão, prescrição) | P0 | M | E3, E7 |
| Dashboard interno (uso, latência) | P0 | M | E12.Eventos |
| Alertas de erro | P0 | S | E12.Eventos |
| Métricas de adoção | P0 | S | E12.Eventos |
| Funil de onboarding | P1 | M | E12.Eventos |

---

## 4. Backlog Fase 2

### E13 — Personalização preditiva

| Item | Prioridade | Esforço |
|------|-----------|---------|
| Modelo de recomendação (regra + ML leve) | P0 | M |
| Modelo de previsão de abandono | P1 | M |
| Modelo de previsão de resposta clínica | P2 | L |
| Feature store | P0 | M |
| Pipeline de treino | P0 | L |
| Avaliação clínica dos modelos | P0 | M |
| Logs de recomendação | P0 | S |
| Endpoint de explicabilidade | P1 | M |

### E14 — Escalas clínicas

| Item | Prioridade | Esforço |
|------|-----------|---------|
| GAD-7 (template + UI + cálculo) | P0 | M |
| ISI | P0 | M |
| PSS-10 | P0 | M |
| EVA dor | P0 | S |
| WHO-5 | P1 | S |
| MFI-20 | P2 | M |
| Cadência automática | P1 | M |
| Visualização de histórico | P0 | M |
| Alerta para escore crítico | P0 | M |

### E15 — Dashboard clínico

| Item | Prioridade | Esforço |
|------|-----------|---------|
| Lista de pacientes com adesão | P0 | M |
| Detalhe do paciente | P0 | M |
| Gráficos de progresso | P0 | M |
| Notas clínicas | P0 | M |
| Exportação de relatório | P1 | M |
| Alertas clínicos (queda, evento adverso) | P0 | M |

### E16 — Integração AraOS

| Item | Prioridade | Esforço |
|------|-----------|---------|
| Notas de sessão no prontuário | P0 | M |
| Visualização no prontuário | P0 | M |
| Sincronização de agenda | P1 | M |
| Compartilhamento de insights | P1 | M |

### E17 — Gamificação avançada

| Item | Prioridade | Esforço |
|------|-----------|---------|
| Sistema de níveis (XP) | P1 | M |
| Planta que cresce | P1 | L |
| Missões semanais | P1 | M |
| Insights personalizados | P1 | M |
| Selo compartilhável | P2 | S |

### E18 — Internacionalização (EN)

| Item | Prioridade | Esforço |
|------|-----------|---------|
| Arquivo de tradução EN | P0 | M |
| Adaptação de conteúdo | P0 | M |
| Adaptação de data/número | P0 | S |
| Suporte a timezones | P0 | S |

---

## 5. Backlog Fase 3

### E19 — Biofeedback (HRV)

| Item | Prioridade | Esforço |
|------|-----------|---------|
| Integração com wearable X (PPG) | P0 | L |
| Cálculo de HRV em tempo real | P0 | L |
| Visual respiratório adaptativo | P0 | L |
| Áudio modulado por biofeedback | P1 | L |
| Sessão com biofeedback + pós-análise | P0 | M |

### E20 — IA generativa

| Item | Prioridade | Esforço |
|------|-----------|---------|
| Pipeline de narração personalizada | P1 | L |
| Geração de insights com LLM | P1 | L |
| Guardrails clínicos | P0 | M |
| Revisão humana de amostragem | P0 | M |
| Logs auditáveis | P0 | M |

### E21 — Pesquisa clínica

| Item | Prioridade | Esforço |
|------|-----------|---------|
| Consentimento específico | P0 | M |
| Pipeline de anonimização | P0 | M |
| Dataset desnormalizado | P1 | L |
| Comitê científico | P0 | S |
| Publicação de 1 estudo | P0 | L |

### E22 — Certificação SaMD

| Item | Prioridade | Esforço |
|------|-----------|---------|
| Avaliação ANVISA | P0 | L |
| Classificação de risco | P0 | M |
| Documentação regulatória | P0 | L |
| Validação clínica | P0 | L |

### E23 — Internacionalização (ES)

| Item | Prioridade | Esforço |
|------|-----------|---------|
| Tradução ES | P1 | M |
| Adaptações culturais | P1 | M |

### E24 — Edge AI

| Item | Prioridade | Esforço |
|------|-----------|---------|
| Modelos leves no cliente | P2 | L |
| Inferência offline | P2 | L |
| Sincronização opcional | P2 | M |

---

## 6. Backlog contínuo (transversal)

| Item | Fase | Descrição |
|------|------|-----------|
| Atualização da biblioteca de protocolos | F1+ | Revisão trimestral |
| Revisão de evidências | F1+ | Atualização anual |
| Revisão de conteúdos em áudio | F1+ | Renovação semestral |
| Treinamento de equipe | F1+ | LGPD, segurança, clínico |
| Auditoria de segurança | F1+ | Anual |
| Testes de carga | F2+ | Semestral |
| Otimização de performance | F1+ | Contínuo |
| Pesquisa com usuários | F1+ | Trimestral |
| Revisão de UX | F1+ | Trimestral |
| Atualização de dependências | F1+ | Mensal |

---

## 7. Dependências críticas

| Dependência | Impacto se atrasar |
|-------------|-------------------|
| AraOS — SSO | Bloqueia E1 |
| AraOS — modelo de módulos | Bloqueia integração |
| Biblioteca de áudio | Bloqueia E4 |
| Revisão clínica dos protocolos | Bloqueia E2 publicação |
| Aprovação DPO | Bloqueia LGPD |

---

## 8. Critérios de "pronto" (DoD)

Para considerar um item pronto:

- [ ] Código revisado por 1+ engenheiro.
- [ ] Testes unitários (cobertura ≥ 80%).
- [ ] Testes de integração (fluxo principal).
- [ ] Testes de segurança (autorização).
- [ ] Acessibilidade verificada (quando aplicável).
- [ ] Documentação atualizada.
- [ ] Eventos de analytics implementados.
- [ ] Logs clínicos gerados (quando aplicável).
- [ ] QA aprovado.
- [ ] PM aceitou.

---

## 9. Anti-backlog (itens descartados)

Itens avaliados e **não** aprovados. Documentados para evitar re-apresentação.

| Item | Motivo |
|------|--------|
| Marketplace de conteúdo de terceiros | Fora de escopo clínico. |
| Vídeos de meditação guiada longa | Risco de substituir psicoterapia. |
| Integração com mídias sociais automática | Risco à privacidade. |
| Login com redes sociais | Não compatível com AraOS. |
| Versão kids com mascote comercial | Risco de marketing infantil. |
| Compra de bens virtuais | Gamificação monetária viola princípios. |
| Compra de sessões extras | Conflita com prescrição clínica. |
| Integração com smartwatches genéricos sem DPA | Risco regulatório. |
| Análise de sentimento do paciente por voz | Complexidade + privacidade. |

---

## 10. Próximas revisões

| Revisão | Data | Escopo |
|---------|------|--------|
| Refinamento F1 | Q4 2026 semana 1 | Detalhamento técnico MVP |
| Refinamento F2 | Q1 2027 semana 8 | Detalhamento IA + escalas |
| Refinamento F3 | Q3 2027 semana 4 | Detalhamento biofeedback |
| Revisão geral | Trimestral | Realinhamento |

---

*Backlog é promessa e limite. Cumprir o que está dentro; questionar o que está fora.*