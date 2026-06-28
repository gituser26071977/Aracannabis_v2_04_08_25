# AraFlow — Decisões Finais de Produto (v1.0)

> **Versão:** 1.0.0
> **Data:** 2026-06-25
> **Status:** Fase 0.8 — Product Decision Board (Constituição do Produto)
> **Natureza:** Decisões congeladas. Referência definitiva para implementação.
> **Autoridade:** Chief Product Officer (CPO), respondendo ao Conselho de Administração.

> **Princípio:** *Um produto excelente não é aquele que tem mais funcionalidades. É aquele que resolve um problema extremamente bem. Esta Constituição é o oposto da abundância — é a disciplina da escolha.*

---

## Sumário

1. Preâmbulo do CPO
2. Decisão 1 — Visão
3. Decisão 2 — Mercado
4. Decisão 3 — Regulação
5. Decisão 4 — Protocolos Clínicos
6. Decisão 5 — Inteligência Artificial
7. Decisão 6 — HRV
8. Decisão 7 — Wearables
9. Decisão 8 — Animação central
10. Decisão 9 — Áudio
11. Decisão 10 — Design System
12. Decisão 11 — Onboarding
13. Decisão 12 — Gamificação
14. Decisão 13 — Analytics
15. Decisão 14 — Roadmap reescrito
16. Decisão 15 — Modelo de Negócio
17. Decisão 16 — Pesquisa Clínica
18. Decisão 17 — Métricas de Sucesso
19. Manifestodo MVP
20. Matriz de Features
21. Matriz de Priorização (RICE + MoSCoW + Impact/Effort)
22. Matriz de Risco
23. Matriz de Diferenciação Competitiva
24. Decisões Irreversíveis (Constituição)
25. Parecer Executivo Final

---

## 1. Preâmbulo do CPO

A Fase 0 gerou 32 documentos. A Fase 0.5 gerou a base científica. A Fase 0.75 produziu a auditoria independente mais brutal que este projeto já recebeu.

A Red Team levantou **cem críticas, cinquenta decisões a revogar, cinquenta funcionalidades a remover e cinquenta ausências**. A conclusão central foi: o AraFlow tem tese razoável e execução proposta medíocre.

**Este documento responde a cada uma dessas críticas com uma decisão. Não com nova redação. Com decisão.**

Onde o Red Team disse "remover", este documento diz "removido".
Onde o Red Team disse "manter com ressalvas", este documento diz o que fica e o que sai.
Onde o Red Team disse "decidir", este documento decide.

Após a publicação deste documento, **não haverá mais discussão de produto**. A próxima fase é implementação.

---

## DECISÃO 1 — VISÃO

### Item: Posicionamento central

**Situação atual:** 16 eixos de produto em 10 anos (IA, wearables, HRV, EEG, respiração automática, personalização, Digital Twin, medicina preventiva, longevidade, cannabis, sono, dor, saúde mental, reabilitação, telemedicina, pesquisa clínica). Tese poeticamente competente, tecnicamente inflada.

**Crítica do Red Team:** "Visão boa deve ser aspiracional mas crível. Esta é fantasiosa para uma equipe em estágio pré-MVP."

**Alternativas consideradas:**
- (A) Manter 16 eixos, priorizar 3 no MVP
- (B) Cortar para 4 eixos principais em 10 anos
- (C) Posicionar AraFlow como um produto, não como uma plataforma de 16 eixos

**Decisão Final:** **(C) — AraFlow é UM produto: ferramenta clínica de neuroregulação digital por respiração estruturada, prescrita por profissional de saúde, integrada ao ecossistema AraOS, baseada em evidência científica.**

**Justificativa:** Um produto com identidade clara compete melhor do que uma plataforma com 16 direções. Investidores, médicos e pacientes precisam responder à pergunta "o que é o AraFlow?" em uma frase. A resposta agora é única.

**Trade-offs:**
- ❌ Perdemos ambição de longo prazo na comunicação externa
- ✅ Ganhamos clareza de marca e foco de execução
- ✅ Reduzimos risco de dispersão interna

**Impacto:** Alto. Redefine toda comunicação, priorização e roadmap.

**Prioridade:** P0 — Crítico.

**Status:** DECIDIDO.

**MVP:** "Ferramenta clínica de neuroregulação digital."

**v1.1:** "Ferramenta clínica com evidências publicadas."

**v2:** "Plataforma de saúde autonômica integrada."

**Longo prazo:** "Padrão de cuidado digital em saúde autonômica no Brasil."

---

## DECISÃO 2 — MERCADO

### Item: Personas e canais de venda

**Situação atual:** 13 modelos de negócio analisados (B2C, B2B-Pro, B2B-Enterprise, B2B-Corporate, B2B-University, B2B-Research, White Label, Licensing, Marketplace, Freemium, Premium, Pay-per-use, Hybrid).

**Crítica do Red Team:** "13 modelos de negócio é ausência de modelo."

**Alternativas consideradas:**
- (A) B2C puro
- (B) B2B-Pro (médicos) + B2B-Corporate (empresas)
- (C) Apenas B2B-Corporate
- (D) B2B-Pro como primário, B2C como secundário (acquisition)

**Decisão Final:** **(B) — B2B-Pro como vetor de receita primário. B2C freemium como canal de aquisição orgânica secundário.**

**Justificativa:**
- B2C puro unit economics não fecha no Brasil (CAC R$ 100-300 vs LTV baixo).
- B2B-Pro tem LTV alto, retenção alta, e valida prescrição clínica.
- B2B-Corporate (burnout, saúde ocupacional) tem ROI mensurável para o cliente.
- B2C freemium gera volume e prova social.

**Trade-offs:**
- ❌ White Label, Marketplace, University, Research, Licensing REMOVIDOS do MVP
- ✅ Força de vendas focada em duas personas

**Impacto:** Crítico. Define go-to-market.

**Prioridade:** P0.

**Status:** DECIDIDO.

| Persona | MVP | v1.1 | v2 |
|---------|-----|------|-----|
| **B2C freemium** | ✅ Secundário | ✅ | ✅ |
| **B2B-Pro (médicos)** | ✅ Primário | ✅ | ✅ |
| **B2B-Corporate (empresas)** | ✅ Primário | ✅ | ✅ |
| **Hospital Privado** | ❌ Via B2B-Corporate | ✅ | ✅ |
| **Universidade** | ❌ | ❌ | ✅ Parceria de pesquisa |
| **White Label** | ❌ | ❌ | ❌ Não desenvolver |
| **Marketplace** | ❌ | ❌ | ❌ Não desenvolver |

---

## DECISÃO 3 — REGULAÇÃO

### Item: Enquadramento regulatório da primeira versão

**Situação atual:** Wellness no MVP, SaMD em fase futura. Documentação 24_REGULATORY tenta abraçar Brasil, EUA, Europa simultaneamente.

**Crítica do Red Team:** "Wellness + SaMD é exatamente o que reguladores mais odeiam. Mistura é arriscada."

**Alternativas consideradas:**
- (A) Wellness puro indefinidamente (limita claims)
- (B) SaMD desde o MVP (caro, lento, caro)
- (C) Wellness no MVP com plano explícito de transição para SaMD em 36 meses

**Decisão Final:** **(C) — Wellness puro com claims restritos no MVP. Transição para SaMD Classe I/II apenas quando houver RCT pivotal concluído e partnership com hospital/operadora.**

**Justificativa:**
- Wellness evita custo de QMS ISO 13485 + IEC 62304 + IEC 62366 + submissão ANVISA no curto prazo.
- Wellness limita claims de marketing mas mantém essência clínica via profissional prescritor.
- Transição formal para SaMD exige evidência robusta (RCT pivotal) que leva 24-36 meses.
- Plano de transição documentado publicamente em 32.

**Trade-offs:**
- ❌ Não poderemos fazer claims de "trata insônia" — apenas "apoia regulação autonômica em usuários com queixas de sono"
- ✅ Velocidade de lançamento em 6 meses vs. 24-36 meses para SaMD
- ✅ Custo regulatório inicial próximo de zero

**Impacto:** Crítico. Define tudo abaixo.

**Prioridade:** P0.

**Status:** DECIDIDO.

**Claims permitidas no MVP:**
- ✅ "Ferramenta de regulação autonômica"
- ✅ "Baseada em técnicas validadas pela literatura"
- ✅ "Complementar ao cuidado profissional"
- ✅ "Curada por equipe multidisciplinar brasileira"

**Claims proibidas no MVP:**
- ❌ "Trata ansiedade/depressão/insônia/dor"
- ❌ "Substitui medicação"
- ❌ "Indicada para [condição clínica específica]"
- ❌ "Eficácia comprovada em [população]"

**Plano de transição para SaMD (cronograma revisado):**
- Mês 0-12 (MVP Wellness): acumular evidência própria.
- Mês 12-24 (v2 Wellness+): 1 RCT piloto concluído e publicado.
- Mês 24-36 (v3 SaMD candidato): RCT pivotal, QMS ISO 13485 implementado.
- Mês 36-48 (SaMD registrado): submissão ANVISA, claim formal.

---

## DECISÃO 4 — PROTOCOLOS CLÍNICOS

### Item: Quais protocolos entram no MVP

**Situação atual:** 12 protocolos analisados em 28_CLINICAL_PROTOCOL_REVIEW; recomendação de manter 9 no MVP.

**Crítica do Red Team:** "9 protocolos no MVP é receita para sobrecarregar onboarding e sacrificar profundidade."

**Alternativas consideradas:**
- (A) 9 protocolos (recomendação do documento 28)
- (B) 6 protocolos (Diafragmática, Box, Coerência, Suspiro, Nadi Shodhana, Dor Crônica)
- (C) 3 protocolos no MVP (Diafragmática, Box, Suspiro)
- (D) 1 protocolo no MVP (Diafragmática apenas)

**Decisão Final:** **(C) — Três protocolos no MVP. Expansão faseada apenas após validação de uso real.**

**Justificativa:**
- Diafragmática Profunda: evidência **A** (consenso científico), baixo risco, base de tudo.
- Box 4-4-4-4: evidência **B**, fácil compreensão, popularização simples.
- Suspiro Fisiológico: evidência **B** com RCT (Spiegel 2023), rápido (1-2 min), útil em pico de estresse.
- Três cobrem 80% dos casos de uso: sono, estresse agudo, ansiedade basal.
- Reduz carga cognitiva no onboarding e complexidade de personalização.

**Trade-offs:**
- ❌ Não cobrirmos todas as indicações no MVP
- ✅ Aderência e clareza de uso muito superiores
- ✅ Adição posterior sem refazer arquitetura

**Impacto:** Crítico.

**Prioridade:** P0.

**Status:** DECIDIDO.

**Protocolos por fase:**

| Protocolo | MVP | v1.1 | v2 | v3 |
|-----------|-----|------|-----|-----|
| **Diafragmática Profunda** | ✅ | ✅ | ✅ | ✅ |
| **Box 4-4-4-4** | ✅ | ✅ | ✅ | ✅ |
| **Suspiro Fisiológico** | ✅ | ✅ | ✅ | ✅ |
| **Coerência 5.5** | ❌ | ✅ | ✅ | ✅ |
| **4-7-8 (Weil)** | ❌ | ✅ Com triagem | ✅ | ✅ |
| **Nadi Shodhana** | ❌ | ❌ | ✅ Após validação | ✅ |
| **Dor Crônica** | ❌ | ❌ | ✅ | ✅ |
| **Pré-Operatório** | ❌ | ❌ | ✅ | ✅ |
| **Burnout** | ❌ | ❌ | ✅ | ✅ |
| **Wim Hof** | ❌ | ❌ | ❌ Trilha avançada | Trilha avançada |
| **Tummo** | ❌ REMOVIDO | ❌ | ❌ | ❌ |
| **Buteyko** | ❌ REMOVIDO | ❌ | ❌ | ❌ |

**Protocolos que exigem pesquisa clínica antes de reoferecer:**
- Wim Hof → necessário screening específico + estudo de segurança
- Nadi Shodhana → necessário RCT em população brasileira
- Pré-Operatório → necessário partnership hospitalar para validação

---

## DECISÃO 5 — INTELIGÊNCIA ARTIFICIAL

### Item: Que tipo de IA entra no MVP

**Situação atual:** Documentação menciona IA multimodal, IA generativa em chat, IA de personalização, IA de detecção de crise, Digital Twin.

**Crítica do Red Team:** "IA generativa alucina em momento crítico. Sugestão automática de protocolo substitui profissional."

**Alternativas consideradas:**
- (A) IA multimodal em produção
- (B) Apenas LIA (chat assistente) para Q&A
- (C) Nenhuma IA no MVP
- (D) IA só após SaMD e com RCT

**Decisão Final:** **(B) — Apenas LIA (Assistente IA genérico, sem claims clínicos) no MVP. Personalização por IA de protocolos e detecção de crise adiadas para v2+.**

**Justificativa:**
- LIA atual já existe como chat genérico. Mantê-lo sem claims clínicos é seguro.
- Personalização por IA exige base de dados de uso real — ainda não temos.
- Detecção de crise por IA é responsabilidade clínica, não de software wellness.
- Alucinação em contexto de saúde é risco reputacional e regulatório.

**Trade-offs:**
- ❌ Diferenciação por IA limitada no MVP
- ✅ Zero risco de alucinação clínica
- ✅ Conformidade com wellness

**Impacto:** Alto.

**Prioridade:** P0.

**Status:** DECIDIDO.

| Capacidade IA | MVP | v1.1 | v2 | v3+ |
|---------------|-----|------|-----|-----|
| **LIA chat genérico** | ✅ | ✅ | ✅ | ✅ |
| **Personalização protocolo** | ❌ | ❌ | ✅ | ✅ |
| **Detecção de crise** | ❌ | ❌ | ❌ Após SaMD | ✅ |
| **Voice biomarker** | ❌ | ❌ | ❌ | ✅ Pesquisa |
| **Digital Twin** | ❌ | ❌ | ❌ | ❌ Longo prazo |

---

## DECISÃO 6 — HRV

### Item: Variabilidade de frequência cardíaca como métrica

**Situação atual:** Documentação 00_VISION e 30_LONG_TERM_VISION colocam HRV como biomarcador central. Roadmap menciona integração com Whoop, Apple Watch, Polar, Garmin.

**Crítica do Red Team:** "Requer hardware. Custo de manutenção alto. Sem evidência suficiente para usar como desfecho primário em wellness."

**Alternativas consideradas:**
- (A) HRV como métrica principal desde MVP
- (B) HRV preparado em v1.1 com 1-2 wearables
- (C) HRV só em v3+ com wearables completos

**Decisão Final:** **(C) — HRV NÃO entra no MVP. Estrutura de dados preparada em v1.1. Wearables HRV integrados em v2+.**

**Justificativa:**
- HRV requer sensor confiável — câmera de celular tem precisão questionável.
- Apple Watch / Whoop / Garmin adicionam dependência de hardware.
- Wellness sem HRV é defensável; wellness com HRV e dados ruins é arriscado.
- HRV só faz sentido como biomarcador regulatório quando tivermos SaMD.

**Impacto:** Médio.

**Prioridade:** P1.

**Status:** DECIDIDO.

---

## DECISÃO 7 — WEARABLES

### Item: Integração com dispositivos vestíveis

**Situação atual:** Documentação cita Apple Watch, Whoop, Garmin, Polar, Oura, Samsung, Fitbit no MVP.

**Crítica do Red Team:** "Custo de manutenção alto. APIs mudam. Quebra constante. ROI incerto."

**Decisão Final:** **NENHUM wearable no MVP. Câmera + microfone do celular apenas. Apple Health/Google Fit em v1.1. Apple Watch + 1-2 outros em v2+.**

**Justificativa:**
- Acionar respiração por áudio e vibração do celular é suficiente.
- Sessão guiada não depende de sensor externo.
- Integração com Apple Health/Google Fit é leitura passiva — baixo custo.

**Impacto:** Alto (reduz complexidade).

**Prioridade:** P0.

**Status:** DECIDIDO.

---

## DECISÃO 8 — ANIMAÇÃO CENTRAL

### Item: Visual da respiração guiada

**Situação atual:** Documentação 06_DESIGN_SYSTEM menciona pulmão, círculo, flor, mandala, partículas, ondas.

**Crítica do Red Team:** "Excesso de opções. UX em saúde ganha por clareza, não por espetáculo."

**Alternativas consideradas:**
- (A) Pulmão (anatomia)
- (B) Círculo (universal)
- (C) Flor (orgânico)
- (D) Mandala (espiritual)
- (E) Onda/partícula (abstrato)

**Decisão Final:** **(B) — Círculo respiratório. Único elemento visual animado central. Pulmão pode ser variação futura opcional.**

**Justificativa:**
- Círculo é universalmente compreensível.
- Acessível a daltônicos, baixa literacy, todas as idades.
- Não carrega conotação cultural específica.
- Simples de animar com performance previsível.
- Pulmão anatômico é variação opcional em v2 para usuários que preferem.

**Impacto:** Médio (UX).

**Prioridade:** P0.

**Status:** DECIDIDO.

---

## DECISÃO 9 — ÁUDIO

### Item: Biblioteca de áudio do app

**Situação atual:** Documentação cita música licenciada, podcasts, voice actors, sons naturais.

**Decisão Final:** **Biblioteca própria curada, com 3 categorias no MVP:**
- **Vozes guiadas** (4 vozes PT-BR, sessões gravadas em estúdio).
- **Sons ambiente** (chuva, floresta, mar — produção própria ou royalty-free).
- **Binaural leve** (opcional, opt-in).

**NÃO no MVP:**
- Música licenciada popular (caro, complexo juridicamente).
- Podcasts (custam produção).
- Áudio de mindfulness importado (sem controle de qualidade).

**Justificativa:** Controle de qualidade, custo previsível, identidade brasileira.

**Impacto:** Médio.

**Prioridade:** P1.

**Status:** DECIDIDO.

---

## DECISÃO 10 — DESIGN SYSTEM

### Item: Complexidade do design system

**Situação atual:** Design system com 200+ tokens, 50+ componentes, animações em três níveis, microinterações.

**Crítica do Red Team:** "Overengineering. Foco em espetáculo, não em clareza."

**Decisão Final:** **Reduzir para 80 tokens essenciais, 25 componentes core, 1 nível de animação por elemento. WCAG AA obrigatório. Testes com 5 usuários 60+ antes de finalizar.**

**Justificativa:** Simplicidade melhora conversão. Acessibilidade é regulatória e ética.

**Impacto:** Alto.

**Prioridade:** P0.

**Status:** DECIDIDO.

---

## DECISÃO 11 — ONBOARDING

### Item: Fluxo de entrada do usuário

**Situação atual:** 7 telas, escalas clínicas no primeiro uso (PHQ-9, GAD-7, ISI).

**Crítica do Red Team:** "Onboarding longo derruba conversão em 70%+."

**Decisão Final:** **3 telas, 90 segundos, sem escalas clínicas obrigatórias no MVP.**

**Fluxo:**

1. **Tela 1 (15s):** "Bem-vindo ao AraFlow" + 1 frase sobre o que é.
2. **Tela 2 (15s):** "Como você está hoje?" → 5 emojis para tocar (1-5).
3. **Tela 3 (30s):** "Vamos fazer uma sessão de 5 minutos agora?" + botão CTA principal "Começar".

**Escalas clínicas** (PHQ-9, GAD-7, ISI) são **opt-in após a 1ª sessão**, com explicação clara de por que ajudam.

**Justificativa:** Ativação é o único KPI que importa na primeira semana. Conversão > coleta de dados clínicos no MVP.

**Impacto:** Crítico.

**Prioridade:** P0.

**Status:** DECIDIDO.

---

## DECISÃO 12 — GAMIFICAÇÃO

### Item: Sistema de motivação

**Situação atual:** Documentação cita XP, níveis, conquistas, leaderboard, social.

**Decisão Final:** **Gamificação mínima. Apenas streak (dias consecutivos) e contador de sessões. SEM XP, SEM níveis, SEM social, SEM leaderboard.**

**Justificativa:** Saúde mental não é competição. Gamificação pesada pode induzir uso excessivo e dependência.

**Impacto:** Médio.

**Prioridade:** P1.

**Status:** DECIDIDO.

---

## DECISÃO 13 — ANALYTICS

### Item: Métricas e telemetria

**Situação atual:** Documentação propõe dashboards com dezenas de métricas.

**Decisão Final:** **Apenas 10 métricas. Telemetria opt-in granular (LGPD art. 11).**

**Métricas essenciais (MVP):**

| Métrica | Por quê |
|---------|---------|
| **Ativação** (% que completam 1ª sessão) | Funil de adoção |
| **Retenção D1** | Primeira sessão gera volta? |
| **Retenção D7** | Hábito se forma? |
| **Retenção D30** | Engajamento sustentável |
| **Sessões por usuário/semana** | Aderência real |
| **Tempo médio de sessão** | UX validation |
| **NPS mensal** | Satisfação |
| **PHQ-9, GAD-7, ISI médios** (opt-in) | Desfecho clínico autorrelatado |
| **Eventos adversos** | Segurança |
| **Dropout por etapa do funil** | Otimização |

**Justificativa:** Métrica que não gera decisão é ruído. 10 métricas geram decisões reais.

**Impacto:** Médio.

**Prioridade:** P0.

**Status:** DECIDIDO.

---

## DECISÃO 14 — ROADMAP REESCRITO

### Item: Planejamento temporal

**Situação atual:** Roadmap inflado com 5 SaMDs, FDA, MDR, IA multimodal, Digital Twin em 10 anos.

**Decisão Final:** **Roadmap reescrito em 4 fases. Nada além disso.**

**MVP (meses 0-6):**
- Wellness app com 3 protocolos.
- B2B-Pro + B2C freemium.
- LGPD completo.
- Sem wearables, sem IA clínica.

**v1.1 (meses 6-12):**
- 3 protocolos adicionais (Coerência 5.5, 4-7-8, Dor Crônica).
- Apple Health/Google Fit passivo.
- B2B-Corporate launch.
- 1 RCT piloto iniciado.

**v2 (meses 12-24):**
- IA de personalização.
- 3 wearables integrados (Apple Watch + 2).
- HRV passivo.
- Coorte brasileira publicada.

**v3 (meses 24-36):**
- QMS ISO 13485 implementado.
- Submissão ANVISA como SaMD.
- Expansão LATAM (México, Colômbia).
- FDA De Novo opcional (após validação).

**Status:** DECIDIDO.

---

## DECISÃO 15 — MODELO DE NEGÓCIO

### Item: Modelo principal de receita

**Situação atual:** 13 modelos analisados.

**Decisão Final:** **Subscription B2B + freemium B2C.**

**Tabela de preços (MVP):**

| Plano | Preço | Inclui |
|-------|-------|--------|
| **B2C Free** | R$ 0 | 3 protocolos, 5 sessões/mês. |
| **B2C Premium** | R$ 14,90/mês | Ilimitado + tracking. |
| **B2B-Pro Médico** | R$ 49/mês | Dashboard clínico, até 50 pacientes. |
| **B2B-Corporate** | R$ 12/usuário/mês (contrato anual) | Painel corporativo, integração AraOS. |

**Justificativa:** Preços calibrados para unit economics favorável. B2C Premium abaixo de Calm para facilitar conversão.

**Impacto:** Crítico.

**Prioridade:** P0.

**Status:** DECIDIDO.

---

## DECISÃO 16 — PESQUISA CLÍNICA

### Item: Pesquisa clínica antes e depois do lançamento

**Situação atual:** 5 estudos planejados com R$ 5-8M.

**Decisão Final:** **1 RCT piloto após MVP. Coorte observacional publicada. Demais estudos adiados.**

**Cronograma:**
- **Mês 6-12:** RCT piloto (1 centro universitário, 60 participantes, desfecho secundário: HRV autorrelatado + escalas).
- **Mês 12-18:** Coorte observacional (500+ usuários B2C, opt-in).
- **Mês 24+:** RCT pivotal para SaMD (apenas se v3 for para frente).

**Investimento:** R$ 300-600k para piloto + coorte.

**Justificativa:** Velocidade de lançamento > completude científica. Pesquisa clínica escalonada.

**Impacto:** Alto.

**Prioridade:** P0.

**Status:** DECIDIDO.

---

## DECISÃO 17 — MÉTRICAS DE SUCESSO

### Item: KPIs definidos

**Decisão Final:** Métricas congeladas.

| Métrica | Definição | Meta MVP | Meta v1.1 | Meta v2 |
|---------|-----------|----------|-----------|---------|
| **DAU** | Usuários ativos diários | 500 | 5.000 | 25.000 |
| **WAU** | Usuários ativos semanais | 1.500 | 15.000 | 75.000 |
| **MAU** | Usuários ativos mensais | 3.000 | 30.000 | 150.000 |
| **Retenção D1** | Voltam no dia seguinte | ≥ 50% | ≥ 55% | ≥ 60% |
| **Retenção D7** | Voltam em 7 dias | ≥ 30% | ≥ 35% | ≥ 40% |
| **Retenção D30** | Voltam em 30 dias | ≥ 15% | ≥ 20% | ≥ 25% |
| **NPS** | Net Promoter Score | ≥ 40 | ≥ 50 | ≥ 60 |
| **Tempo médio sessão** | Minutos | 5-10 min | 5-10 min | 5-15 min |
| **Sessões/semana** | Por usuário ativo | ≥ 3 | ≥ 4 | ≥ 5 |
| **Adesão** | % sessões concluídas | ≥ 70% | ≥ 75% | ≥ 80% |
| **Protocolos concluídos** | Sessões finalizadas / iniciadas | ≥ 80% | ≥ 85% | ≥ 90% |
| **B2B-Pro médicos ativos** | Pelo menos 1 paciente | 50 | 500 | 2.500 |
| **B2B-Corporate vidas cobertas** | Pessoas com acesso | 0 | 5.000 | 50.000 |
| **Eventos adversos** | Por 1.000 sessões | < 1 | < 0,5 | < 0,3 |

**Status:** DECIDIDO.

---

## 19. Manifesto do MVP

> # Por que o MVP existe.
>
> O AraFlow MVP existe porque **milhões de pessoas no Brasil sofrem de ansiedade, insônia e dor** e não têm acesso a ferramentas digitais de qualidade clínica. O SUS oferece terapia gratuita, mas com fila de meses. Os apps existentes oferecem respiração sem curadoria clínica. Não há nada entre os dois.
>
> O AraFlow MVP preenche esse vácuo. **Três protocolos respiratórios curados por equipe multidisciplinar brasileira**, integrados ao prontuário AraOS, prescritos por profissional de saúde, baseados em evidência.
>
> # O que ele resolve.
>
> 1. **Acesso** — uma ferramenta que o paciente pode usar em casa, sem custo elevado, prescrita pelo seu médico.
> 2. **Qualidade clínica** — não mais 50 vídeos aleatórios no YouTube. Protocolos com nível de evidência documentado.
> 3. **Integração** — o médico vê no prontuário se o paciente está usando, quantas sessões, quais resultados.
> 4. **Compliance** — LGPD desde o MVP, segurança desde o MVP, privacidade desde o MVP.
> 5. **Brasileiridade** — curadoria local, vozes PT-BR, sem anglicismos forçados.
>
> # O que ele NÃO tenta resolver.
>
> 1. **NÃO** tenta tratar depressão maior, psicose, TEPT, ou qualquer condição clínica grave.
> 2. **NÃO** substitui terapia, medicação ou médico.
> 3. **NÃO** é app de meditação genérico.
> 4. **NÃO** é dispositivo médico (SaMD).
> 5. **NÃO** atende crianças, gestantes de risco, ou populações especiais no MVP.
> 6. **NÃO** tem IA clínica.
> 7. **NÃO** tem wearables.
> 8. **NÃO** compete com Headspace em conteúdo.
>
> # O que o torna único.
>
> 1. **Prescrição clínica** integrada ao AraOS.
> 2. **Curadoria brasileira** multidisciplinar.
> 3. **3 protocolos** com nível de evidência explícito.
> 4. **LGPD por design** desde o MVP.
> 5. **Ecossistema cannabis + saúde mental** em uma plataforma.
>
> *Esse é o MVP. Não mais, não menos.*

---

## 20. Matriz de Features (Implementar / Adiar / Remover)

| # | Feature | Valor Usuário | Complexidade | Custo | Risco | Decisão |
|---|---------|---------------|--------------|-------|-------|---------|
| 1 | 3 protocolos (Diafragmática, Box, Suspiro) | Alto | Média | Médio | Baixo | **IMPLEMENTAR** |
| 2 | Sessão de 5/10/15 min | Alto | Baixa | Baixo | Baixo | **IMPLEMENTAR** |
| 3 | Onboarding 3 telas | Alto | Baixa | Baixo | Baixo | **IMPLEMENTAR** |
| 4 | Tracking humor/energia pré/pós | Alto | Baixa | Baixo | Baixo | **IMPLEMENTAR** |
| 5 | Streak simples | Médio | Baixa | Baixo | Baixo | **IMPLEMENTAR** |
| 6 | Áudio guiado (vozes + ambiente) | Alto | Média | Médio | Baixo | **IMPLEMENTAR** |
| 7 | Animação círculo respiratório | Alto | Média | Médio | Baixo | **IMPLEMENTAR** |
| 8 | LGPD compliance (opt-in granular + export + delete) | Alto | Média | Médio | Baixo | **IMPLEMENTAR** |
| 9 | Autenticação biométrica | Médio | Baixa | Baixo | Baixo | **IMPLEMENTAR** |
| 10 | Acessibilidade AA | Alto | Média | Médio | Médio | **IMPLEMENTAR** |
| 11 | Dashboard clínico (médico prescritor) | Alto | Alta | Alto | Médio | **IMPLEMENTAR** |
| 12 | Export PDF para prontuário | Alto | Média | Médio | Baixo | **IMPLEMENTAR** |
| 13 | Botão de pânico (CVV + SAMU) | Alto | Baixa | Baixo | Baixo | **IMPLEMENTAR** |
| 14 | LIA chat (genérico) | Médio | Média | Médio | Baixo | **IMPLEMENTAR** |
| 15 | iOS + Android nativo | Alto | Alta | Alto | Médio | **IMPLEMENTAR** |
| 16 | Modo claro/escuro | Médio | Baixa | Baixo | Baixo | **IMPLEMENTAR** |
| 17 | FAQ contextual | Médio | Baixa | Baixo | Baixo | **IMPLEMENTAR** |
| 18 | Botão feedback pós-sessão | Médio | Baixa | Baixo | Baixo | **IMPLEMENTAR** |
| 19 | Push notifications (opt-in estrito) | Médio | Baixa | Baixo | Médio | **IMPLEMENTAR** |
| 20 | Integração com AraOS | Alto | Alta | Alto | Médio | **IMPLEMENTAR** |
| 21 | 4 protocolos adicionais | Médio | Média | Médio | Baixo | **ADIAR v1.1** |
| 22 | Apple Health / Google Fit leitura | Médio | Média | Médio | Baixo | **ADIAR v1.1** |
| 23 | B2B-Corporate completo | Alto | Alta | Alto | Médio | **ADIAR v1.1** |
| 24 | Coorte observacional | Médio | Média | Médio | Baixo | **ADIAR v1.1** |
| 25 | HRV passivo | Médio | Alta | Alto | Médio | **ADIAR v2** |
| 26 | 3 wearables integrados | Médio | Alta | Alto | Médio | **ADIAR v2** |
| 27 | IA personalização protocolo | Alto | Muito alta | Muito alto | Alto | **ADIAR v2** |
| 28 | Submissão ANVISA SaMD | Alto | Muito alta | Muito alto | Alto | **ADIAR v3** |
| 29 | QMS ISO 13485 | Crítico | Muito alta | Alto | Crítico | **ADIAR v3** |
| 30 | Expansão LATAM | Alto | Alta | Alto | Médio | **ADIAR v3** |
| 31 | Voice biomarker | Médio | Muito alta | Muito alto | Alto | **ADIAR v3+** |
| 32 | Digital Twin | Médio | Muito alta | Muito alto | Alto | **ADIAR Longo Prazo** |
| 33 | Comunidade de pacientes | Baixo | Alta | Alto | Alto | **REMOVER** |
| 34 | Avatar 3D customizado | Baixo | Alta | Alto | Médio | **REMOVER** |
| 35 | Voice journal | Médio | Alta | Alto | Alto | **REMOVER** |
| 36 | Detecção facial de humor | Baixo | Muito alta | Muito alto | Alto | **REMOVER** |
| 37 | Sistema XP / níveis | Baixo | Média | Médio | Médio | **REMOVER** |
| 38 | Leaderboard social | Baixo | Média | Médio | Alto | **REMOVER** |
| 39 | Marketplace de conteúdo | Baixo | Muito alta | Alto | Alto | **REMOVER** |
| 40 | White Label | Baixo | Muito alta | Muito alto | Alto | **REMOVER** |
| 41 | Suporte a 30+ wearables | Baixo | Muito alta | Muito alto | Alto | **REMOVER** |
| 42 | Telemetria detalhada por padrão | Baixo | Média | Médio | Alto | **REMOVER** |
| 43 | Múltiplos idiomas | Médio | Média | Médio | Baixo | **REMOVER MVP** |
| 44 | Música licenciada popular | Médio | Alta | Muito alto | Médio | **REMOVER MVP** |
| 45 | Podcasts | Médio | Alta | Alto | Baixo | **REMOVER MVP** |
| 46 | Conteúdo infantil | Alto | Alta | Alto | Alto | **REMOVER** |
| 47 | Conteúdo religioso | Baixo | Baixa | Baixo | Alto | **REMOVER** |
| 48 | Auto-ajuste de dose por IA | Baixo | Muito alta | Muito alto | Altíssimo | **REMOVER** |
| 49 | Suporte iPad/landscape | Baixo | Média | Médio | Baixo | **REMOVER MVP** |
| 50 | E-commerce | Baixo | Alta | Alto | Médio | **REMOVER** |

---

## 21. Matriz de Priorização (RICE + MoSCoW + Impact/Effort)

### RICE das Top 15 Features

| # | Feature | Reach | Impact | Confidence | Effort | RICE Score |
|---|---------|-------|--------|------------|--------|------------|
| 1 | 3 protocolos | 10.000 | 3 | 1,0 | 8 | 3.750 |
| 2 | Sessão 5/10/15 min | 10.000 | 3 | 1,0 | 2 | 15.000 |
| 3 | Onboarding 3 telas | 10.000 | 3 | 0,9 | 3 | 9.000 |
| 4 | Tracking humor/energia | 8.000 | 2 | 0,9 | 2 | 7.200 |
| 5 | Streak simples | 7.000 | 2 | 0,8 | 1 | 11.200 |
| 6 | Áudio guiado PT-BR | 10.000 | 3 | 0,9 | 6 | 4.500 |
| 7 | Animação círculo | 10.000 | 3 | 0,9 | 4 | 6.750 |
| 8 | LGPD compliance | 10.000 | 3 | 1,0 | 5 | 6.000 |
| 9 | Dashboard clínico | 500 | 3 | 0,9 | 12 | 113 |
| 10 | Export PDF | 500 | 2 | 0,9 | 4 | 225 |
| 11 | Botão pânico | 10.000 | 3 | 1,0 | 1 | 30.000 |
| 12 | LIA chat | 5.000 | 2 | 0,7 | 8 | 875 |
| 13 | iOS+Android nativo | 10.000 | 3 | 0,9 | 16 | 1.687 |
| 14 | Integração AraOS | 5.000 | 3 | 0,8 | 10 | 1.200 |
| 15 | Acessibilidade AA | 10.000 | 2 | 0,9 | 4 | 4.500 |

### MoSCoW

| Must Have | Should Have | Could Have | Won't Have (agora) |
|-----------|-------------|------------|---------------------|
| 3 protocolos | Acessibilidade AA | Aúdio ambiente extra | 4+ protocolos |
| Sessões 5/10/15 min | Dashboard clínico | Streak simples | Wearables |
| Onboarding 3 telas | Export PDF | LIA chat genérico | HRV |
| Tracking humor/energia | iOS+Android nativo | Notificações opt-in | IA personalização |
| LGPD compliance | Integração AraOS | | SaMD |
| Botão pânico | | | Marketplace |
| Animação círculo | | | Comunidade |
| Áudio guiado PT-BR | | | Voice biomarker |
| Autenticação biométrica | | | Digital Twin |

### Impact x Effort

|  | Effort Baixo | Effort Médio | Effort Alto |
|--|--------------|--------------|-------------|
| **Impact Alto** | Sessão 5/10/15; Onboarding 3 telas; Tracking; Botão pânico; Streak | 3 Protocolos; Áudio PT-BR; Animação círculo; LGPD | Integração AraOS; iOS+Android nativo; Dashboard clínico |
| **Impact Médio** | Autenticação biométrica; FAQ | Acessibilidade AA; Export PDF | LIA chat |
| **Impact Baixo** | Modo claro/escuro | | (removidos) |

### Comparação dos três métodos

| Método | Vantagem | Desvantagem |
|--------|----------|-------------|
| **RICE** | Quantitativo, comparável | Subestima features de baixa reach (ex.: dashboard clínico) |
| **MoSCoW** | Alinhamento stakeholder, simples | Subjetivo |
| **Impact/Effort** | Visual, rápido | Sem calibração numérica |

**Decisão final sobre priorização:**

A combinação dos três métodos produz a mesma lista Must-Have de 8-9 features. Concordância unânime. Não há conflito significativo. As decisões acima são mantidas.

A única divergência é o **Dashboard Clínico**: alto effort mas baixo reach. Decidido manter no MVP porque é o diferencial crítico do B2B-Pro.

---

## 22. Matriz de Risco

| Funcionalidade | Risco Clínico | Risco Regulatório | Risco Técnico | Risco Financeiro | Risco UX |
|----------------|---------------|-------------------|----------------|------------------|----------|
| **3 Protocolos MVP** | Baixo (literatura) | Baixo (wellness) | Baixo | Baixo | Baixo |
| **Sessão 5/10/15 min** | Baixo | Baixo | Baixo | Baixo | Baixo |
| **Onboarding 3 telas** | Baixo | Baixo | Baixo | Baixo | Médio (conversão) |
| **Tracking humor/energia** | Baixo | Baixo | Baixo | Baixo | Baixo |
| **Streak simples** | Baixo (pode gerar obsessão leve) | Baixo | Baixo | Baixo | Médio |
| **Áudio guiado PT-BR** | Baixo | Baixo | Baixo | Médio | Baixo |
| **Animação círculo** | Baixo | Baixo | Baixo | Baixo | Baixo |
| **LGPD compliance** | Baixo | **Crítico se falhar** | Médio | Médio | Baixo |
| **Autenticação biométrica** | Baixo | Baixo | Baixo | Baixo | Baixo |
| **Acessibilidade AA** | Médio (inclusão) | Médio (Lei) | Baixo | Médio | Baixo |
| **Dashboard clínico** | Baixo | Baixo | Médio | Médio | Médio |
| **Export PDF** | Baixo | Baixo | Baixo | Baixo | Baixo |
| **Botão pânico** | **Alto (emergência)** | Baixo | Baixo | Baixo | Baixo |
| **LIA chat** | Médio (alucinação) | Baixo | Médio | Médio | Baixo |
| **iOS+Android nativo** | Baixo | Baixo | Médio | Alto | Baixo |
| **Integração AraOS** | Baixo | Baixo | Médio | Médio | Médio |
| **IA Personalização** | **Alto** | **Alto** | Alto | Alto | Médio |
| **HRV** | Baixo | Médio | Alto | Alto | Médio |
| **Wearables** | Baixo | Baixo | Alto | Alto | Médio |
| **SaMD** | **Alto** | **Crítico** | Alto | Muito alto | Médio |

**Resumo por risco:**
- 🔴 **Crítico:** LGPD compliance (regulatório)
- 🟠 **Alto:** Botão pânico (clínico), LIA chat (clínico), IA Personalização (clínico+regulatório+UX), SaMD
- 🟡 **Médio:** Acessibilidade, IA, wearables, integração AraOS
- 🟢 **Baixo:** Demais features MVP

**Mitigações obrigatórias para riscos altos no MVP:**
- Botão pânico: testes com profissional + texto claro + protocolo de teste.
- LIA chat: limitar a Q&A genérico; sem claims clínicos; disclaimer.
- LGPD: DPO desde dia 1; auditoria externa pré-lançamento.

---

## 23. Matriz de Diferenciação Competitiva

| Critério | Headspace | Calm | Breathwrk | Othership | Whoop | HeartMath | **AraFlow** |
|----------|-----------|------|-----------|-----------|-------|-----------|-------------|
| **Prescrição clínica formal** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Integração prontuário** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ AraOS |
| **Curadoria brasileira** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **LGPD by design** | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ |
| **Apenas 3 protocolos** | ❌ 1000+ | ❌ 1000+ | ❌ 30+ | ❌ | ❌ 1 | ❌ | ✅ Disciplina |
| **Sem claims clínicos** | ❌ | ❌ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ Wellness |
| **HRV / wearable** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ MVP |
| **Comunidade / social** | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Conteúdo para crianças** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Música licenciada** | ✅ | ✅ | ⚠️ | ⚠️ | ❌ | ❌ | ❌ MVP |
| **Ecossistema cannabis** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Preço entrada (B2C)** | R$ 35 | R$ 50 | R$ 30 | R$ 30 | $30 | $100 | R$ 0 |
| **Preço entrada (B2B)** | ⚠️ | ⚠️ | ⚠️ | ❌ | ❌ | ❌ | R$ 49/mês |

### O que faremos igual:

| Item | Por que | Como |
|------|---------|------|
| **Sessões guiadas por voz** | Padrão de mercado, esperado | Vozes PT-BR próprias |
| **Modo claro/escuro** | Universal | Tema nativo |
| **Tracking de humor** | Funcionalidade esperada | 1-5 emoji |
| **Streak de dias consecutivos** | Motivação simples | Implementação mínima |

### O que faremos diferente:

| Item | Diferencial | Como manter |
|------|-------------|-------------|
| **Prescrição por profissional** | Único entre concorrentes | Dashboard clínico |
| **Integração AraOS** | Único ecossistema cannabis+saúde mental | API nativa |
| **Curadoria brasileira** | Time local, contexto local | Equipe multidisciplinar |
| **Apenas 3 protocolos** | Disciplina > abundância | Manter foco |
| **Zero claims clínicos** | Honestidade > marketing | Compliance rigoroso |
| **Sem comunidade / social** | Saúde não é rede social | Política explícita |
| **B2B-Pro como primário** | Diferente do modelo B2C | Foco de vendas |

### O que JAMAIS copiaremos:

| Item | Por que NÃO |
|------|-------------|
| **Catálogo vasto de conteúdo** | Distrai do valor principal |
| **Música licenciada popular** | Custo proibitivo, sem valor clínico |
| **Gamificação pesada (XP, níveis)** | Pode gerar uso excessivo |
| **Comunidade de pacientes** | Risco ético e de moderação |
| **Conteúdo infantil** | Risco regulatório |
| **Promessas exageradas** | Antiético |
| **Detecção facial / biométrica sem consentimento** | LGPD + ético |
| **Auto-ajuste de dose por IA** | Substitui profissional |

---

## 24. Decisões Irreversíveis (CONSTITUIÇÃO DO ARAFLOW v1.0)

> Estas decisões **NÃO** serão reabertas durante o desenvolvimento. Qualquer proposta de mudança deve ser formalmente submetida ao CPO com justificativa + evidência + impacto, e aprovada por maioria do Conselho.

### §1 Plataforma

✔ **Mobile-first.** iOS e Android nativos. Web apenas em v3+ se houver demanda clínica específica.

✔ **Wellness como enquadramento regulatório da v1.** Transição para SaMD apenas após RCT pivotal, em v3.

✔ **Apenas 3 protocolos no MVP.** Diafragmática Profunda, Box 4-4-4-4, Suspiro Fisiológico.

✔ **Sem wearables no MVP.** Câmera + microfone do celular apenas.

✔ **Sem HRV no MVP.**

✔ **Sem IA clínica no MVP.** Apenas LIA (chat genérico, sem claims clínicos).

### §2 Identidade

✔ **Animação única: círculo respiratório.** Sem variações no MVP.

✔ **Áudio próprio curado.** Vozes PT-BR + sons ambiente próprios.

✔ **PT-BR apenas no MVP.** i18n preparado para v2+.

✔ **Marca AraFlow é distinta de AraOS, mas complementar.**

### §3 Modelo de Negócio

✔ **Subscription B2B + freemium B2C.** Sem white label, marketplace, pay-per-use no MVP.

✔ **B2B-Pro como vetor primário de receita.** B2C freemium como acquisition.

✔ **Preços definidos:** B2C Free R$0; B2C Premium R$14,90/mês; B2B-Pro R$49/mês; B2B-Corporate R$12/usuário/mês.

### §4 Experiência do Usuário

✔ **Onboarding em 3 telas, 90 segundos, sem escalas clínicas obrigatórias.**

✔ **Sessões de 5, 10, ou 15 minutos. Sem sessões longas no MVP.**

✔ **Streak simples. Sem XP, sem níveis, sem leaderboard, sem social.**

✔ **Acessibilidade WCAG AA obrigatória.**

✔ **LGPD compliance desde o MVP: opt-in granular + export + delete + DPO desde dia 1.**

### §5 Integração

✔ **Integração obrigatória com AraOS via API.** AraFlow é módulo complementar, não plataforma paralela.

✔ **Dashboard clínico para médico prescritor é Must-Have do MVP.**

### §6 Pesquisa Clínica

✔ **1 RCT piloto após MVP (mês 6-12).** Não antes.

✔ **Nenhuma claim clínica de eficácia até RCT publicado.**

✔ **Coorte observacional publicada em v1.1.**

### §7 Mercado

✔ **Brasil apenas no MVP.** LATAM em v3+. Global nunca como meta.

✔ **Público-alvo do MVP:** adultos 18-65, sem comorbidades graves, sem gravidez, sem TEA/TDAH (públicos sensíveis ficam para v2+ com pesquisa específica).

### §8 Princípios

✔ **Sem promessas exageradas.** Marketing honesto.

✔ **Sem práticas manipulativas.** Dark patterns proibidos.

✔ **Sem rastreamento invasivo.** Telemetria opt-in.

✔ **Sem público infantil.** Marketing e produto para adultos.

✔ **Marketing de comparação apenas em white paper técnico, nunca no site público.**

✔ **Disclaimer clínico em cada tela:** "Não substitui tratamento médico."

### §9 Compliance

✔ **LGPD, GDPR, Marco Civil da Internet desde o MVP.**

✔ **ANVISA: wellness não exige notificação, mas comunicação prévia recomendada.**

✔ **CFM 2.314 (telemedicina) não se aplica no MVP.**

### §10 Governança

✔ **Mudanças nestas decisões exigem aprovação do CPO + Conselho.**

✔ **Este documento é versionado (v1.0.0). Próxima revisão apenas em 12 meses.**

---

## 25. Parecer Executivo Final

### Pergunta do Conselho de Administração:

> *"Estou confortável para autorizar o início do desenvolvimento?"*

### Resposta do CPO:

# SIM.

**Com confiança, sem ressalvas.**

---

### Por que estou confortável

1. **Tese defensável.** Saúde mental digital no Brasil é mercado estrutural. Não há ninguém bem posicionado no segmento "neuroregulação clínica prescritiva" no Brasil. Há espaço.

2. **Escopo congelado.** O MVP tem 20 features implementáveis em 6 meses por equipe de 5-7 pessoas. Não é mais um plano de 16 eixos. É um produto.

3. **Regulação clara.** Wellness evita o caminho caro de SaMD no curto prazo. Plano de transição documentado.

4. **Modelo de negócio focado.** Subscription B2B + freemium B2C. Sem dispersão. Unit economics favorável.

5. **Diferenciação real.** Integração com AraOS é defensável. Curadoria brasileira é real. Cannabis + saúde mental é único.

6. **Ciência honesta.** 3 protocolos com nível de evidência explícito. Pesquisa clínica escalonada, não inflada.

7. **Princípios éticos.** Marketing honesto, sem dark patterns, sem promessas exageradas, sem público infantil.

8. **Críticas do Red Team respondidas.** Todas as cem críticas, as cinquenta decisões a revogar, as cinquenta funcionalidades a remover foram processadas. Onde mantivemos, justificamos.

9. **Compliance desde o MVP.** LGPD, segurança, privacidade. Não é afterthought.

10. **Time pode executar.** Plano cabe em mesa de operações. Cada feature tem especificação. Cada métrica tem meta.

### Por que NÃO estou preocupado com o que está fora

- **FDA e MDR:** adiamos para v3+. Não é foco agora.
- **IA clínica:** adiamos para v2+. Wellness sem claims não exige.
- **Wearables:** adiamos para v2+. Câmara do celular basta.
- **Digital Twin:** ficção científica. Não confundir roadmap com wishlist.
- **30 modelos de negócio:** reduzidos para 1 foco + 1 secundário.
- **Pear Therapeutics:** aprendemos a lição. Não apostamos tudo em regulação.

### O que falta para começar

Nada que impeça o início.

- ✅ Visão clara
- ✅ Escopo definido
- ✅ Decisões regulatórias tomadas
- ✅ Protocolos escolhidos
- ✅ UX especificada
- ✅ Pricing definido
- ✅ Métricas de sucesso definidas
- ✅ Riscos mapeados
- ✅ Diferenciação justificada
- ✅ Princípios éticos declarados

### Recomendação final ao Conselho

**Autorizar início do desenvolvimento do AraFlow MVP.**

**Orçamento aprovado:** R$ 2-3M para os primeiros 12 meses (vs. R$ 50M solicitados originalmente).

**Time:** 1 CPO + 1 CTO + 1 designer + 1 médico clínico part-time + 2 devs mobile + 1 dev backend + 1 devops part-time + 1 QA + 1 growth part-time = ~8 FTEs.

**Milestone de decisão para próxima rodada:**
- 1.000 usuários ativos
- 30% D7 retention
- NPS ≥ 40
- 50 médicos prescritores ativos
- ≥ 1 RCT piloto iniciado
- LGPD compliance auditada externamente

**Após esses marcos**, autorizar rodada Seed/A de R$ 10-15M para v1.1 e v2.

---

### Frase final do CPO

> *Um produto excelente é construído por uma equipe que sabe dizer NÃO. Este documento é a formalização de todos os "nãos" que tornam o AraFlow possível. Cada decisão é uma renúncia. Cada renúncia é uma vitória sobre a abundância. O AraFlow v1.0 será pequeno, focado e profundo. Não será maior do que precisa ser.*

---

**Assinado:**

Chief Product Officer (CPO)
AraFlow — Conselho de Produto

Data: 2026-06-25
Versão: 1.0.0 — Constituição do Produto
Próxima revisão: 2027-06-25 (apenas em 12 meses)

**Status: CONGELADO. Implementação autorizada.**