# AraFlow — Product Requirements Document (PRD)

> **Versão:** 0.1.0
> **Status:** Fase 0 — Descoberta
> **Data:** 2026-06-24
> **Owner:** Product Owner
> **Stakeholders:** Equipe AraOS · médicos prescritores · psicólogos · pacientes

---

## 1. Sumário

1. Sumário
2. Contexto e objetivos
3. Personas resumidas (detalhe em 02)
4. Casos de uso
5. Escopo do MVP, Fase 2, Fase 3
6. Requisitos funcionais
7. Requisitos não-funcionais
8. Restrições e suposições
9. Critérios de aceitação
10. Dependências
11. Riscos
12. Métricas e KPIs
13. Glossário

---

## 2. Contexto e objetivos

### 2.1 Contexto

O **AraOS** é a plataforma principal de gestão clínica e terapêutica. Hoje ela oferece prontuário, agenda, IA, prescrição e telemedicina. Falta uma camada dedicada a **neuroregulação digital** que permita ao profissional prescrever e acompanhar técnicas respiratórias e meditativas como parte do plano terapêutico.

### 2.2 Objetivos de produto (OGs)

| OG | Descrição | Métrica de sucesso |
|----|-----------|--------------------|
| **OG-1** | Permitir ao profissional prescrever protocolos de neuroregulação com segurança e evidência | 100% dos protocolos com referência bibliográfica e nível de evidência. |
| **OG-2** | Oferecer ao paciente sessões curtas, simples e clinicamente eficazes | ≥ 60% de adesão a sessões prescritas. |
| **OG-3** | Medir impacto clínico (ansiedade, sono, dor, foco) | Redução mensurável em GAD-7 / ISI / EVA. |
| **OG-4** | Integrar AraFlow ao prontuário e à IA do AraOS | 100% das sessões ficam registradas no histórico do paciente (com consentimento). |
| **OG-5** | Apoiar 10 casos de uso clínicos primários | Lista (vide 4). |

### 2.3 Não-objetivos (Fase 0)

- Não diagnosticar.
- Não substituir tratamento medicamentoso ou psicoterapêutico.
- Não realizar consulta síncrona (telemedicina).
- Não vender conteúdo genérico de bem-estar.
- Não fabricar hardware (wearables).

---

## 3. Personas resumidas

Detalhamento completo em `02_USER_PERSONAS.md`.

| Persona | Perfil | Necessidade primária |
|---------|--------|----------------------|
| **Dra. Marina** | Médica prescritora (clínica geral / cannabis medicinal) | Prescrever protocolos com segurança. |
| **Dr. Rafael** | Psicólogo cognitivo-comportamental | Exercício entre sessões para ansiedade. |
| **Lúcia** | Fisioterapeuta (dor crônica) | Recurso coadjuvante para dor e sono. |
| **Carlos** | Paciente adulto com ansiedade e insônia | Alívio rápido, validado por médico. |
| **Bia** | Adolescente com TDAH (sob cuidado) | Foco para estudo; prescrito por profissional. |
| **Sr. Antônio** | Idoso com SAHOS e ansiedade | Respiração segura, simples, com áudio claro. |

---

## 4. Casos de uso (escopo AraFlow)

| # | Caso de uso | Persona-alvo | Tipo |
|---|-------------|---------------|------|
| UC-01 | Reduzir ansiedade aguda (pico) | Carlos, Bia, Sr. Antônio | Sessão pontual (3-5 min) |
| UC-02 | Melhorar qualidade do sono | Carlos, Lúcia, Sr. Antônio | Sessão noturna (10-20 min) |
| UC-03 | Alívio de dor crônica | Carlos, Lúcia | Sessão guiada (10-15 min) |
| UC-04 | Burnout e estresse ocupacional | Dr. Rafael, Carlos | Programa diário (5-10 min) |
| UC-05 | Suporte em uso de cannabis medicinal | Dra. Marina, Carlos | Sessão integrada ao tratamento |
| UC-06 | Pré-sono e apneia leve (com cuidado) | Sr. Antônio | Sessão lenta supervisionada |
| UC-07 | TEA — regulação sensorial | Bia | Sessão visual + auditiva repetível |
| UC-08 | TDAH — foco e atenção | Bia | Sessão curta de foco |
| UC-09 | Foco para trabalho/estudo | Carlos, Bia | Sessão rápida (5-10 min) |
| UC-10 | Relaxamento geral / bem-estar | Todos | Sessão livre |

---

## 5. Escopo por fase

### 5.1 MVP (Fase 1) — detalhe em `18_MVP.md`

- 12 protocolos clínicos pré-definidos.
- Player de sessão com visual animado (círculo respiratório).
- Áudio terapêutico (música + narração opcional).
- Biblioteca de sessões gratuitas.
- Login via AraOS.
- Histórico local do paciente.
- Prescrição simples pelo profissional (selecionar protocolo + dose).
- Adesão básica (sessões concluídas, minutos, sequência).
- LGPD: consentimento explícito, criptografia, exportação de dados.

### 5.2 Fase 2 — Personalização e analytics clínico

- 30+ protocolos, com variantes.
- Recomendações personalizadas (regras + modelo simples).
- Dashboards clínicos (adesão, padrão de uso, escores).
- Escalas padronizadas (GAD-7, ISI, PSS-10, EVA).
- Gamificação leve (sequências, conquistas).
- Compartilhamento de progresso com profissional.

### 5.3 Fase 3 — Biofeedback e IA avançada

- HRV em tempo real (via wearable integrado).
- Ajuste dinâmico de ritmo guiado pelo HRV.
- IA multimodal (personalização profunda, geração de conteúdo).
- Pesquisa clínica integrada (consentimento específico).

---

## 6. Requisitos funcionais (RF)

### 6.1 Autenticação e conta

- **RF-001** O AraFlow deve autenticar via AraOS (SSO).
- **RF-002** Deve respeitar o tipo de usuário do AraOS (paciente / profissional / admin).
- **RF-003** Deve permitir logout local sem afetar AraOS.

### 6.2 Biblioteca de protocolos

- **RF-010** Deve existir uma biblioteca com protocolos categorizados por objetivo (ansiedade, sono, dor, foco, relaxamento, etc.).
- **RF-011** Cada protocolo deve ter ficha técnica: tempo de inspiração, expiração, pausas, frequência respiratória, duração total, objetivo clínico, contraindicações, base fisiológica, nível de evidência, referências bibliográficas.
- **RF-012** Cada protocolo deve ter versão, autor clínico revisor e data de revisão.

### 6.3 Sessão

- **RF-020** O usuário deve poder iniciar uma sessão em ≤ 2 cliques a partir da home.
- **RF-021** A sessão deve mostrar visual animado de respiração + áudio opcional + tempo restante.
- **RF-022** O usuário deve poder pausar, retomar ou encerrar a qualquer momento.
- **RF-023** Ao fim, deve registrar: protocolo, duração efetiva, completude (% do tempo alvo), data/hora, escala subjetiva (opcional).
- **RF-024** Deve funcionar offline; sincronizar quando online.

### 6.4 Prescrição (profissional)

- **RF-030** O profissional deve poder criar uma prescrição: protocolo, dose (sessões/dia), duração do plano, observações.
- **RF-031** O profissional deve poder ver adesão e resposta clínica do paciente.
- **RF-032** O profissional deve poder ajustar ou encerrar a prescrição.

### 6.5 Personalização (Fase 2)

- **RF-040** Recomendar protocolo com base em objetivo do paciente, horário e histórico.
- **RF-041** Adaptar gradualmente ritmo e duração.

### 6.6 Biofeedback (Fase 3)

- **RF-050** Integrar com pelo menos 1 wearable (PPG ou ECG) para HRV.
- **RF-051** Visualizar HRV em tempo real durante a sessão.

### 6.7 Analytics (Fase 2)

- **RF-060** Dashboard do paciente: sessões, minutos, sequência, escores.
- **RF-061** Dashboard do profissional: lista de pacientes, adesão, alertas.

### 6.8 Privacidade e LGPD

- **RF-070** Consentimento explícito antes de qualquer coleta.
- **RF-071** Exportação completa dos dados pessoais.
- **RF-072** Exclusão total da conta (direito ao esquecimento).
- **RF-073** Telemetria mínima e opt-in.

---

## 7. Requisitos não-funcionais (RNF)

| Categoria | Requisito | Métrica |
|-----------|-----------|---------|
| Performance | Início de sessão | < 2s P95 |
| Performance | Animação fluida | ≥ 60fps em mid-range |
| Disponibilidade | Uptime | ≥ 99,5% |
| Acessibilidade | WCAG 2.1 AA | 100% das telas principais |
| Acessibilidade | Modos daltonismo, alto contraste, leitor de tela | Suportados |
| Compatibilidade | Browsers | Chrome, Safari, Firefox, Edge (últimas 2 versões) |
| Compatibilidade | Mobile | iOS 15+, Android 10+ |
| Offline | Sessão completa sem rede | Garantido |
| Privacidade | Criptografia em trânsito e repouso | TLS 1.3 + AES-256 |
| Privacidade | Conformidade LGPD | 100% |
| Segurança | Autenticação | SSO via AraOS + MFA opcional |
| Localização | Idiomas | PT-BR (MVP), EN (Fase 2), ES (Fase 3) |
| Escalabilidade | Usuários simultâneos | 10k no MVP; 100k na Fase 2 |
| Auditoria | Logs clínicos imutáveis | Mínimo 5 anos |

---

## 8. Restrições e suposições

### 8.1 Restrições

- Não competir com AraOS em UX/visual; manter identidade.
- Não reinventar autenticação; usar AraOS.
- Não hospedar dados clínicos em servidor fora do Brasil (LGPD).
- Não usar tecnologia proprietária que impossibilite evolução futura.

### 8.2 Suposições

- Profissionais prescritores terão pelo menos 1 smartphone/computador atualizado.
- Pacientes terão acesso a fones de ouvido (não obrigatório, mas recomendado).
- AraOS terá camada de "módulos" que aceita o AraFlow como filho.

---

## 9. Critérios de aceitação do MVP

O MVP será considerado pronto quando:

1. ✅ 12 protocolos clínicos publicados, revisados por pelo menos 1 profissional de cada categoria.
2. ✅ Sessão completa (visual + áudio) funcional em iOS, Android e Web.
3. ✅ Login via AraOS funcionando.
4. ✅ Prescrição simples pelo profissional e exibição para o paciente.
5. ✅ Histórico do paciente com últimas 30 sessões.
6. ✅ LGPD: consentimento, exportação e exclusão implementados e testados.
7. ✅ Acessibilidade AA nas 5 telas principais.
8. ✅ Performance < 2s para iniciar sessão.
9. ✅ Zero eventos adversos críticos em teste interno.
10. ✅ Documentação técnica e clínica completa.

---

## 10. Dependências

| Dependência | Tipo | Criticidade |
|-------------|------|-------------|
| AraOS — autenticação | Externa | Alta |
| AraOS — prontuário | Externa | Alta |
| AraOS — agenda | Externa | Média |
| AraOS — IA | Externa | Média |
| AraOS — analytics | Externa | Média |
| Biblioteca de áudio royalty-free | Externa | Alta |
| Biblioteca de animações Lottie/Rive | Externa | Média |
| Wearable (Fase 3) | Externa | Alta (Fase 3) |

---

## 11. Riscos do PRD

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Baixa adesão do paciente | Média | Alto | UX simples, sessões curtas, IA, gamificação leve. |
| Resistência do profissional | Média | Alto | Educação médica contínua, evidência, integração ao AraOS. |
| Regulação ANVISA | Média | Alto | Classificar como wellness device; revisão jurídica contínua. |
| Privacidade / LGPD | Baixa | Muito alto | Privacy by design, DPO, auditoria externa. |
| Performance mobile | Média | Médio | PWA + nativo opcional; testar mid-range. |
| Conteúdo de baixa qualidade | Baixa | Alto | Curadoria clínica, revisão periódica. |

---

## 12. Métricas e KPIs

### 12.1 KPIs de produto

| KPI | Meta MVP (3 meses pós-lançamento) |
|-----|REDACTED|
| Profissionais com pelo menos 1 prescrição ativa | 100 |
| Pacientes ativos (1 sessão/semana) | 1.000 |
| Sessões concluídas / prescritas | ≥ 60% |
| NPS paciente | ≥ 40 |
| Sessões médias por paciente ativo por semana | ≥ 3 |

### 12.2 KPIs técnicos

| KPI | Meta |
|-----|------|
| Uptime | ≥ 99,5% |
| Latência P95 início de sessão | < 2s |
| Crash-free sessions | ≥ 99% |
| Lighthouse Performance | ≥ 85 (PWA) |

---

## 13. Glossário

(Vide `00_VISION.md` § 12 para glossário completo.)

---

## 14. Aprovações

| Papel | Nome | Data |
|-------|------|------|
| Product Owner | — | — |
| UX Designer | — | — |
| Software Architect | — | — |
| Tech Lead | — | — |
| Diretor Clínico AraOS | — | — |
| DPO | — | — |

---

*Este documento é vivo. Revisões semestrais obrigatórias.*