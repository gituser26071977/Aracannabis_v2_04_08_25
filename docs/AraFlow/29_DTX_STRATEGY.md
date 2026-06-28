# AraFlow — Estratégia de Digital Therapeutics (DTx)

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Status:** Fase 0.5 — Product Strategy
> **Autoria:** Diretor Clínico · Pesquisa Clínica · Estratégia · Diretor Técnico

> **Princípio orientador:** *Digital Therapeutics exige ciência, regulação, evidência e respeito — não apenas código.*

---

## Sumário

1. O que é DTx
2. Posicionamento AraFlow no ecossistema DTx
3. Roadmap de certificação
4. Requisitos científicos
5. Estudos clínicos necessários
6. Métricas de eficácia
7. Como convencer hospitais
8. Como convencer planos de saúde
9. Como convencer médicos
10. Reembolso
11. Barreiras e mitigação
12. Vantagens competitivas
13. Casos de uso prioritários
14. Parcerias estratégicas
15. Risco regulatório
16. Cronograma
17. Investimento necessário
18. Métricas de sucesso

---

## 1. O que é DTx

> *Status: CONSENSO.*

### 1.1 Definição (DTA — Digital Therapeutics Alliance)

> *"Software terapêutico que previne, gerencia ou trata uma condição médica. Pode ser usado sozinho ou em combinação com medicamentos, dispositivos ou outras terapias."*

### 1.2 Características essenciais

| Característica | Detalhe |
|----------------|---------|
| **Indicação clínica específica** | Não genérico. |
| **Evidência clínica robusta** | RCT, idealmente meta-análise. |
| **Regulação sanitária** | ANVISA / FDA / MDR. |
| **Prescrição (muitas vezes)** | Não obrigatória em todos os modelos. |
| **Adesão monitorada** | Dados de uso. |
| **Desfechos medidos** | Clínicos, validados. |

### 1.3 Exemplos globais de referência

| Produto | Indicação | País | Status |
|---------|-----------|------|--------|
| **Pear Therapeutics (reSET, reSET-O)** | Transtorno por uso de substâncias | EUA | Aprovado FDA, depois faliu |
| **Akili (EndeavorRx)** | TDAH pediátrico | EUA | Aprovado FDA |
| **BlueStar (WellDoc)** | Diabetes tipo 2 | EUA | Aprovado FDA |
| **Sleepio (Big Health)** | Insônia | UK | NHS recomendado |
| **Deprexis** | Depressão | Alemanha | Aprovado |
| **HelloBetter** | Insônia, estresse | Alemanha | Aprovado |

> **Lição:** DTx é viável, mas exige caminho regulatório, evidência e modelo de negócio sustentável. Pear Therapeutics faliu em 2023 apesar da aprovação — o modelo de negócio importa tanto quanto o regulatório.

---

## 2. Posicionamento AraFlow no ecossistema DTx

> *Status: CONSENSO.*

### 2.1 Estágios regulatórios

| Estágio | Fase AraFlow | Característica |
|---------|--------------|----------------|
| **Wellness** | MVP (Fase 1) | Sem indicação clínica. Foco em bem-estar geral. |
| **Wellness + prescrição** | Fase 2 | Indicações amplas, com profissional prescritor. |
| **Dispositivo médico (SaMD) Classe I-II** | Fase 3 | Indicação clínica específica. Regulação ANVISA. |
| **Dispositivo médico Classe III** | Fase 4 (futuro) | Alto risco ou classe alta. |

### 2.2 Mapa de posicionamento

```
                Bem-estar genérico
                        ↓
                   Wellness app
                        ↓
                Wellness com protocolo
                        ↓
              Wellness com profissional  ← AraFlow MVP
                        ↓
                  SaMD Classe I-II  ← AraFlow Fase 3
                        ↓
                SaMD Classe III  ← AraFlow Fase 4 (futuro)
```

### 2.3 Indicações prioritárias candidatas a SaMD

> *Status: HIPÓTESE — a ser validado com pesquisa clínica.*

| Indicação | Justificativa | Tamanho do mercado |
|-----------|---------------|-------------------|
| **Insônia** | Evidência forte, mercado grande, baixa complexidade. | ~73M brasileiros. |
| **Ansiedade** | Evidência moderada, mercado imenso. | ~85M brasileiros. |
| **Burnout ocupacional** | Mercado B2B forte. | ~30% dos trabalhadores. |
| **Dor crônica** | Evidência forte, desfechos claros. | ~60M brasileiros. |
| **Pré-operatório** | Curto e mensurável, B2B claro. | ~4M cirurgias/ano. |

### 2.4 Indicações que **não** serão candidatas a SaMD no MVP

| Indicação | Por que não |
|-----------|-------------|
| **TEA** | Complexidade alta, público sensível, requer equipe específica. |
| **TDAH em adultos** | Requer evidência robusta, regulação específica. |
| **TEPT** | População vulnerável, requer equipe específica. |
| **Depressão maior** | Alto risco, requer supervisão intensa. |
| **Suicídio** | Fora de escopo. |

---

## 3. Roadmap de certificação

### 3.1 Fases

> *Status: CONSENSO.*

#### Fase 1 — Wellness (MVP, 2026-2027)

- Classificação: app de bem-estar.
- Indicação: genérica (bem-estar, estresse, sono).
- Marketing: sem claims clínicos.
- Regulação: nenhuma formal (mas compliance LGPD obrigatório).

#### Fase 2 — Wellness com supervisão clínica (2027-2028)

- Classificação: wellness, mas com protocolo de supervisão clínica.
- Indicação: "ferramenta complementar ao cuidado profissional".
- Marketing: "prescrita por profissionais".
- Regulação: nenhuma formal (ainda wellness).

#### Fase 3 — SaMD Classe I ou II (2028-2030)

- Classificação: SaMD.
- Indicação: específica (ex.: "adjuvante no manejo da insônia").
- Marketing: claims clínicos específicos permitidos.
- Regulação: ANVISA (RDC 751/2022 e correlatas), FDA (opcional), MDR (opcional).
- Evidência: pelo menos 2 RCTs próprios + revisão sistemática.

#### Fase 4 — DTx consolidado (2030+)

- Múltiplas indicações SaMD.
- Reembolso por convênios.
- Prescrição médica formal.
- Possível expansão para Classe III em indicações específicas.

### 3.2 Marcos regulatórios

| Marco | Quando | Responsabilidade |
|-------|--------|------------------|
| **Estruturar QMS (ISO 13485)** | 2027 | Diretor Técnico + Qualidade. |
| **Design History File (DHF)** | 2027-2028 | Eng. Clínica. |
| **Submissão ANVISA** | 2028-2029 | Regulação. |
| **Submissão FDA (opcional)** | 2029-2030 | Regulação. |
| **Submissão MDR (opcional)** | 2030+ | Regulação. |

---

## 4. Requisitos científicos

> *Status: CONSENSO.*

### 4.1 Pré-clínico

- Literatura revisada por pares para cada protocolo.
- Mecanismo fisiológico documentado.
- Risco analisado formalmente.

### 4.2 Clínico

- **Estudo piloto** (coorte pequena, 30-50 participantes).
- **Estudo principal** (RCT, ≥100 participantes por braço).
- **Replicação independente** (parceria universitária).
- **Estudo pós-mercado** (farmacovigilância-like).

### 4.3 Documentação

- Clinical Evaluation Report (CER) — contínuo.
- Post-Market Surveillance (PMS) — contínuo.
- Resumo de segurança e desempenho.
- Plano de gerenciamento de risco (ISO 14971).

### 4.4 Comitê científico

> *Status: CONSENSO.*

Comitê científico independente com 5-7 membros:
- 1 médico intensivista ou internista.
- 1 psiquiatra.
- 1 médico do sono.
- 1 psicólogo clínico.
- 1 neurocientista.
- 1 metodologista / estatístico.
- 1 representante de paciente.

---

## 5. Estudos clínicos necessários

> *Status: PLANO — a ser refinado.*

### 5.1 Estudo 1 — Piloto de viabilidade e segurança

- **Objetivo:** confirmar segurança e aceitabilidade.
- **Desenho:** coorte prospectiva.
- **Amostra:** 50 participantes.
- **Duração:** 8 semanas.
- **Desfecho:** taxa de eventos adversos; taxa de adesão; aceitabilidade.

### 5.2 Estudo 2 — RCT piloto de eficácia

- **Objetivo:** estimar efeito.
- **Desenho:** RCT paralelo, 2 braços (AraFlow vs. controle ativo).
- **Amostra:** 100-150 por braço.
- **Duração:** 12 semanas.
- **Desfecho primário:** mudança em GAD-7 / PHQ-9 / ISI conforme indicação.

### 5.3 Estudo 3 — RCT multicêntrico pivotal

- **Objetivo:** confirmar eficácia para SaMD.
- **Desenho:** RCT multicêntrico, 3-5 centros brasileiros.
- **Amostra:** 200-300 por braço.
- **Duração:** 16-24 semanas.
- **Desfecho primário:** mudança em escala validada.
- **Desfecho secundário:** qualidade de vida, adesão, custo-efetividade.

### 5.4 Estudo 4 — Estudo qualitativo

- **Objetivo:** compreender experiência do usuário.
- **Desenho:** entrevistas semiestruturadas + análise temática.
- **Amostra:** 20-30 participantes.
- **Público:** pacientes + profissionais prescritores.

### 5.5 Estudo 5 — Estudo de implementação

- **Objetivo:** avaliar implementação em contexto real.
- **Desenho:** estudo híbrido tipo 2 (efetividade + implementação).
- **Amostra:** 5-10 clínicas parceiras.

### 5.6 Cronograma de estudos

| Estudo | Início | Conclusão | Custo estimado |
|--------|--------|-----------|----------------|
| **1 — Piloto** | 2027 Q1 | 2027 Q4 | R$ 200-400k |
| **2 — RCT piloto** | 2028 Q1 | 2028 Q4 | R$ 800k-1.5M |
| **3 — RCT pivotal** | 2029 Q1 | 2030 Q2 | R$ 3-5M |
| **4 — Qualitativo** | 2027 Q3 | 2028 Q2 | R$ 100-200k |
| **5 — Implementação** | 2030 Q1 | 2031 Q1 | R$ 1-2M |

---

## 6. Métricas de eficácia

> *Status: CONSENSO.*

### 6.1 Desfechos primários (por indicação)

| Indicação | Escala | MCID (mudança mínima clinicamente importante) |
|-----------|--------|REDACTED|
| **Ansiedade** | GAD-7 | Redução ≥ 4 pontos |
| **Depressão** | PHQ-9 | Redução ≥ 5 pontos |
| **Insônia** | ISI | Redução ≥ 7 pontos |
| **Burnout** | MBI / PSS-10 | Redução ≥ 10% no escore total |
| **Dor** | EVA | Redução ≥ 2 pontos |
| **Qualidade de vida** | EQ-5D-5L | Melhoria ≥ 0,1 no índice |

### 6.2 Desfechos secundários

- Adesão (sessões/semana, dropout).
- Satisfação (CSAT, NPS).
- Segurança (taxa de eventos adversos).
- Custo-efetividade (QALY incremental).
- Uso real (engajamento, retenção).

### 6.3 Biomarcadores (exploratórios)

- HRV (quando wearable disponível).
- Cortisol salivar (em subgrupos).
- Actigrafia (em subgrupos).

---

## 7. Como convencer hospitais

> *Status: HIPÓTESE (a ser validado).*

### 7.1 Argumentos centrais

1. **Redução de custo**: ansiedade pré-operatória reduz tempo de internação e uso de sedativos.
2. **Desfechos**: melhorar desfechos de recuperação.
3. **Escalabilidade**: ferramenta digital atinge muitos pacientes sem custo marginal alto.
4. **Compliance**: ferramenta rastreável, integrada ao prontuário.
5. **Segurança**: evento adverso raro e gerenciado.

### 7.2 Públicos

| Público | Argumento | Canal |
|---------|-----------|-------|
| **Diretor clínico** | Desfechos + segurança. | Apresentação + white paper. |
| **Diretor financeiro** | ROI + redução de custo. | Análise de impacto orçamentário. |
| **Médicos prescritores** | Evidência + facilidade. | Visita médica + workshops. |
| **Equipe de enfermagem** | Facilidade + suporte ao cuidado. | Treinamento + piloto. |
| **TI** | Integração + segurança. | Demonstração técnica. |

### 7.3 Piloto hospitalar

- Implementar em 1-2 alas/unidades.
- Medir impacto em 3-6 meses.
- Publicar case study.
- Escalar.

---

## 8. Como convencer planos de saúde

> *Status: HIPÓTESE.*

### 8.1 Argumentos centrais

1. **Redução de sinistralidade**: menos internações psiquiátricas, menos consultas de emergência.
2. **Adesão a tratamento**: saúde mental é problema de adesão; AraFlow amplia alcance.
3. **Diferenciação**: poucas operadoras oferecem saúde mental digital estruturada.
4. **Dados**: métricas de uso e desfecho.
5. **Compliance**: LGPD + auditoria.

### 8.2 Modelo de negócio para convênios

| Modelo | Quando |
|--------|--------|
| **B2B-Enterprise** | Por vida/ano (R$ X/beneficiário/ano). |
| **Pay-for-performance** | Parte fixa + parte variável por desfecho. |
| **Bônus por redução de sinistralidade** | Compartilhamento de risco. |
| **White label** | Para operadora que quer oferecer como seu. |

### 8.3 Passos para abordar operadoras

1. **Piloto pequeno** (1 plano, 500-1000 vidas).
2. **Análise de impacto** (3-6 meses).
3. **Case study** publicado.
4. **Expansão** para outras áreas do plano.
5. **Conversão** para contrato plurianual.

---

## 9. Como convencer médicos

> *Status: HIPÓTESE.*

### 9.1 Argumentos por especialidade

| Especialidade | Argumento central |
|---------------|-------------------|
| **Psiquiatra** | Adjuvante ao tratamento, monitora adesão, escala o cuidado. |
| **Clínico geral** | Primeira linha em queixas psicossomáticas, sem medicalizar. |
| **Cardiologista** | Manejo de estresse como parte do cuidado cardiovascular. |
| **Oncologista** | Suporte em ansiedade pré-procedimento, fadiga. |
| **Pediatra** | Versão para adolescentes (ansiedade escolar, TDAH leve). |
| **Médico do trabalho** | Burnout, qualidade de vida. |
| **Ginecologista/obstetra** | Ansiedade gestacional, preparação parto. |
| **Anestesista** | Ansiedade pré-operatória. |

### 9.2 Canais

- **Educação médica continuada**: workshops, webinars.
- **Congressos médicos**: sessões satélites, posters.
- **Literatura revisada**: white papers, articles.
- **Visita médica**: time dedicado.
- **Casos clínicos**: demonstrativos.
- **Rede de Key Opinion Leaders (KOLs)**: 5-10 médicos influenciadores.

### 9.3 Barreiras

| Barreira | Mitigação |
|----------|-----------|
| **Ceticismo** | Evidência revisada, casos reais. |
| **Tempo** | Prescrição em 30s; app simples. |
| **Medo de substituição** | Posicionar como adjuvante, não substituto. |
| **Custo para paciente** | Modelo de cobertura. |
| **Privacidade** | Compliance LGPD explícito. |

---

## 10. Reembolso

### 10.1 Cenário atual no Brasil

- Reembolso de DTx ainda incipiente.
- ANS não tem código TUSS específico para DTx.
- Algumas operadoras reembolsam como "programa de saúde".

### 10.2 Caminhos possíveis

| Caminho | Viabilidade |
|---------|-------------|
| **Incluir em programa de saúde corporativa** | ✅ Alta. |
| **Reembolso via código de consulta + tecnologia** | ⚠️ Média. |
| **Reembolso como terapia complementar** | ⚠️ Média. |
| **Reembolso direto por DTx SaMD** | ❌ Baixa no curto prazo. |
| **Cobertura por saúde suplementar com rol** | ⚠️ Média-longo prazo. |

### 10.3 Estratégia

1. **Curto prazo:** incluir em programa B2B (auto-incorporação).
2. **Médio prazo:** convencer operadoras a incluir em programa estruturado.
3. **Longo prazo:** lobby para código TUSS específico.

---

## 11. Barreiras e mitigação

> *Status: CONSENSO.*

| Barreira | Probabilidade | Impacto | Mitigação |
|----------|---------------|---------|-----------|
| **Regulação lenta** | Alta | Alto | Eng. regulatória dedicada desde Fase 2. |
| **Eventos adversos graves** | Baixa-média | Alto | Triagem + screening. |
| **Baixa adesão em MVP** | Média | Médio | Gamificação leve, design cuidadoso. |
| **Concorrência grande (Headspace)** | Alta | Médio | Diferenciação clínica + Brasil. |
| **Falta de evidência robusta** | Média | Alto | Estudo clínico desde Fase 2. |
| **Ceticismo médico** | Alta | Médio | Educação + KOLs. |
| **Crise reputacional** | Baixa | Alto | Compliance + comunicação transparente. |
| **Vazamento de dados** | Baixa | Altíssimo | Segurança + auditoria. |
| **Mudança regulatória desfavorável** | Baixa | Alto | Lobby + adaptação. |

---

## 12. Vantagens competitivas

> *Status: CONSENSO.*

| Vantagem | Detalhe |
|----------|---------|
| **Contexto brasileiro** | Equipe local, cultura, idioma. |
| **Integração com AraOS** | Prontuário + ecossistema clínico. |
| **Curadoria clínica** | Equipe multidisciplinar. |
| **Pesquisa clínica em curso** | Gera evidência própria. |
| **Compliance LGPD** | Desde MVP. |
| **Modelo B2B estruturado** | Não apenas B2C. |
| **Populações especiais** | Gestantes, TEA, cannabis. |
| **Custo acessível** | Preço competitivo para LATAM. |

---

## 13. Casos de uso prioritários

### 13.1 Para SaMD inicial (Fase 3)

> *Status: HIPÓTESE — refinar com pesquisa.*

| Indicação | Caso de uso | Justificativa |
|-----------|-------------|---------------|
| **Insônia** | Adjuvante à TCC-I. | Mercado grande, desfecho claro. |
| **Ansiedade** | Adjuvante ao tratamento. | Mercado imenso. |
| **Burnout ocupacional** | Programa corporativo. | B2B claro. |
| **Dor crônica** | Adjuvante. | Evidência forte. |
| **Ansiedade pré-operatória** | Hospital-dia. | Curto, mensurável. |

### 13.2 Critérios de seleção

- Evidência prévia robusta (RCT existente na literatura).
- Desfecho mensurável.
- Mercado significativo.
- Viabilidade técnica.
- Aceitabilidade do público.

---

## 14. Parcerias estratégicas

> *Status: HIPÓTESE.*

| Tipo | Parceiro potencial | Ganho |
|------|--------------------|-------|
| **Acadêmica** | USP, UNIFESP, UFRGS, UFMG | Pesquisa clínica, credibilidade. |
| **Hospitalar** | Hospital Israelita, Sírio, Moinhos | Piloto, implementação. |
| **Operadora** | Unimed, Amil, Bradesco Saúde | Distribuição, cobertura. |
| **Indústria** | Hypera, Eurofarma | Co-marketing, distribuição. |
| **Wearables** | Polar, Garmin, Apple | Integração HRV. |
| **Saúde corporativa** | TotalPass, Gympass | Distribuição B2B. |
| **Associação médica** | ABP, AMSB | KOLs, recomendação. |
| **Reguladora** | ANVISA, ANPD | Compliance, alinhamento. |
| **ONG** | CVV, Instituto Vita | Triagem, escalabilidade social. |

---

## 15. Risco regulatório

> *Status: ANÁLISE.*

### 15.1 Riscos

| Risco | Probabilidade | Impacto |
|-------|---------------|---------|
| **Classificação inadequada** | Média | Alto |
| **Mudança regulatória** | Baixa | Alto |
| **Multa ANPD** | Baixa-média | Alto |
| **Recall regulatório** | Baixa | Altíssimo |
| **Bloqueio ANVISA** | Baixa | Alto |
| **Demanda judicial** | Baixa-média | Médio |

### 15.2 Mitigação

- Equipe regulatória dedicada desde Fase 2.
- QMS ISO 13485 desde 2027.
- Auditorias internas semestrais.
- Acompanhamento de legislação.
- Consultoria jurídica especializada em saúde digital.

---

## 16. Cronograma

| Ano | Fase | Marcos |
|-----|------|--------|
| **2026** | Fase 1 — Wellness MVP | Lançamento do MVP. |
| **2027** | Fase 2 — Wellness + Clínica | Estudo piloto; QMS; equipe regulatória. |
| **2028** | Fase 2 → 3 transição | RCT piloto; CER inicial; submissão pré-ANVISA. |
| **2029** | Fase 3 — SaMD | RCT pivotal; submissão ANVISA. |
| **2030** | Fase 3 — SaMD aprovado | Aprovação ANVISA; comercialização como SaMD. |
| **2031+** | Fase 4 — DTx consolidado | Múltiplas indicações; reembolso; FDA/MDR opcional. |

---

## 17. Investimento necessário

> *Status: ESTIMATIVA.*

| Item | Valor estimado |
|------|----------------|
| **Pesquisa clínica (5 estudos)** | R$ 5-8M (5 anos) |
| **QMS + Certificação ISO 13485** | R$ 300-500k |
| **Equipe regulatória** | R$ 1.5-2M/ano (a partir de 2027) |
| **Submissão ANVISA** | R$ 200-400k |
| **Submissão FDA (opcional)** | R$ 1-2M |
| **Manutenção pós-mercado** | R$ 500k-1M/ano |
| **Marketing e educação médica** | R$ 1-2M/ano |

> **Total 5 anos:** ~R$ 15-25M para chegar à aprovação ANVISA como SaMD.

---

## 18. Métricas de sucesso

> *Status: CONSENSO.*

### 18.1 Curto prazo (2026-2027)

| KPI | Meta |
|-----|------|
| **Downloads** | 100k+ |
| **Usuários ativos mensais** | 30k+ |
| **Adesão (≥3 sessões/semana)** | ≥ 40% |
| **NPS** | ≥ 50 |
| **Eventos adversos** | < 0,5% |

### 18.2 Médio prazo (2028-2030)

| KPI | Meta |
|-----|------|
| **Estudos concluídos** | 3 (piloto, RCT piloto, qualitativo) |
| **Publicações peer-reviewed** | ≥ 3 |
| **Médicos prescritores** | 1.000+ |
| **Hospital parceiro** | ≥ 3 |
| **Operadora parceira** | ≥ 1 |

### 18.3 Longo prazo (2030+)

| KPI | Meta |
|-----|------|
| **Aprovação ANVISA** | ✅ |
| **Indicações SaMD** | ≥ 2 |
| **Cobertura por convênio** | ≥ 5M vidas |
| **Publicações totais** | ≥ 10 |
| **Market share Brasil em DTx saúde mental** | ≥ 15% |

---

*Digital Therapeutics é maratona, não corrida. Faça com ciência, respeito e persistência.*