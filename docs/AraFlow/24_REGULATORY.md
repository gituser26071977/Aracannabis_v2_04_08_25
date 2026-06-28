# AraFlow — Análise Regulatória

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Status:** Fase 0.5 — Clinical Validation
> **Autoria:** Equipe jurídica + Especialista SaMD + DPO + Diretor Clínico

> **Importante:** Este documento é **educacional**, não constitui aconselhamento jurídico formal. Decisões finais devem ser tomadas com **advogado especializado em saúde digital** em cada jurisdição.

---

## Sumário

1. Contexto regulatório
2. O AraFlow é Software como Dispositivo Médico (SaMD)?
3. Classificação no Brasil (ANVISA)
4. Classificação nos EUA (FDA)
5. Classificação na Europa (MDR / IVDR)
6. Quando o AraFlow deixa de ser wellness?
7. Riscos regulatórios por mercado
8. Como permanecer como wellness no MVP
9. Requisitos para futura certificação SaMD
10. Estratégia regulatória por fase
11. Comparação entre jurisdições
12. Compliance com LGPD / GDPR / HIPAA
13. Marketing e publicidade
14. Responsabilidades pós-mercado
15. Roadmap regulatório
16. Questões em aberto
17. Recomendações finais

---

## 1. Contexto regulatório

> *Status: CONSENSO.*

### 1.1 Por que isso importa

- **Risco legal:** classificar incorretamente pode gerar responsabilização.
- **Risco reputacional:** sanções administrativas e perda de confiança.
- **Risco de mercado:** produtos não-certificados podem ser proibidos.
- **Risco clínico:** produtos não-validados podem causar dano.

### 1.2 Princípio orientador

> **Quando há dúvida, classificamos como mais rigoroso.**

### 1.3 Linha do tempo regulatória

| Período | Status esperado |
|---------|-----------------|
| **MVP (2027-Q1)** | Wellness device (não-SaMD). |
| **Fase 2 (2027-Q3)** | Wellness + início de validação clínica. |
| **Fase 3 (2028-Q2)** | Submissão regulatória SaMD (se indicado). |
| **Fase 3+ (2029+)** | SaMD certificado em ≥ 1 jurisdição. |

---

## 2. O AraFlow é Software como Dispositivo Médico (SaMD)?

### 2.1 Definição (IMDRF / FDA)

> "Software intended for one or more medical purposes that perform these purposes without being part of a hardware medical device."

Em outras palavras:
- É SaMD **se** for usado para **finalidade médica** (diagnóstico, tratamento, prevenção, etc.).
- **Não** é SaMD se for apenas bem-estar geral sem finalidade médica específica.

### 2.2 Análise para o AraFlow

> *Status: ANÁLISE — diverge conforme jurisdição.*

| Critério | Análise | Implicação |
|----------|---------|-----------|
| **Finalidade declarada** | Bem-estar, regulação autonômica, suporte terapêutico. | Limítrofe. |
| **Indicação clínica específica** | Tratamento adjuvante de ansiedade, insônia, dor. | Tende a SaMD. |
| **Prescrição médica** | Sim, opcional. | Peso a favor de SaMD. |
| **Resultados medidos** | Escalas clínicas, aderência, padrões de uso. | Peso a favor de SaMD. |
| **Substitui tratamento** | Não. | Peso a favor de wellness. |
| **Algoritmo decide tratamento** | Não; profissional decide. | Peso a favor de wellness. |
| **IA personaliza protocolo** | Sim (Fase 2). | Peso a favor de SaMD. |
| **Biofeedback ajusta em tempo real** | Sim (Fase 3). | Peso forte a favor de SaMD. |
| **Comercializado para saúde** | Sim (parcial). | Peso a favor de SaMD. |
| **Reivindica benefício terapêutico** | Sim (no marketing). | Peso a favor de SaMD. |

### 2.3 Conclusão (multidisciplinar)

> **CONSENSO:**
> - **MVP (wellness)**: classificação defensável se não reivindicar finalidade médica específica. Comunicação cuidadosa.
> - **Fase 2 (com IA e escalas)**: zona cinza. **Início de preparação regulatória** recomendado.
> - **Fase 3 (biofeedback + personalização forte)**: **provavelmente SaMD**. Submissão regulatória provavelmente necessária.

### 2.4 Riscos da classificação errada

| Erro | Consequência |
|------|--------------|
| Classificar como wellness mas funcionar como SaMD | Sanções por venda de dispositivo não registrado; recall; multa. |
| Classificar como SaMD sem ter submetido | Igual acima. |
| Submeter cedo demais sem evidência | Custos altos, possibilidade de recusa, retrabalho. |
| Submeter tarde demais | Bloqueio de mercado, sanções. |

---

## 3. Classificação no Brasil (ANVISA)

### 3.1 Marco regulatório

- **RDC 751/2022** — Dispõe sobre a classificação de softwares como dispositivos médicos.
- **RDC 36/2015** — Boas práticas de fabricação.
- **RDC 67/2009** — Registro de produtos.
- **RDC 185/2001** — Registro de produtos para saúde.
- **LGPD** — Lei Geral de Proteção de Dados.

### 3.2 Classificação RDC 751/2022

A ANVISA classifica SaMD em **4 classes** (I, II, III, IV) baseado em:

| Dimensão | Avaliação |
|----------|-----------|
| **Finalidade** | Diagnóstico, monitoramento, terapia, etc. |
| **Estado da condição de saúde** | Crítica, séria, não-séria. |
| **Tipo de profissional** | Não-profissional, profissional, especialista. |

### 3.3 Análise para o AraFlow

> **Status: HIPÓTESE — análise jurídica formal é necessária.**

| Cenário | Classe provável |
|---------|----------------|
| **MVP (wellness, sem indicação clínica)** | Fora do escopo SaMD. |
| **Com prescrição + indicação clínica adjuvante** | **Classe I ou II** (baixo risco). |
| **Com biofeedback e ajuste terapêutico** | **Classe II** (médio risco). |
| **Com IA autônoma que ajusta doses** | **Classe III** (alto risco). |

### 3.4 Requisitos para registro SaMD (Brasil)

| Requisito | Descrição |
|-----------|-----------|
| **CBF (Certificado de Boas Práticas)** | Conforme RDC 36/2015. |
| **QMS** | Sistema de qualidade documentado. |
| **Dossiê técnico** | Descrição, finalidade, evidências, riscos. |
| **Avaliação clínica** | Estudos clínicos ou evidência equivalente. |
| **Rotulagem** | Em português. |
| **Manual do usuário** | Em português. |
| **Vigilância pós-mercado** | Plano de farmacovigilância-like. |
| **LGPD** | RIPD atualizado. |

### 3.5 Timeline estimado para registro

| Etapa | Duração estimada |
|-------|------------------|
| **Preparação de dossiê** | 6-12 meses |
| **Validação clínica** | 6-18 meses |
| **Submissão + análise ANVISA** | 3-12 meses |
| **Total** | **15-42 meses** |

---

## 4. Classificação nos EUA (FDA)

### 4.1 Marco regulatório

- **21st Century Cures Act (2016)** — excluiu do FDA alguns softwares.
- **FDA Guidance "Software as a Medical Device" (2013)**.
- **FDORA (2022)** — atualizações.
- **FDA Pre-cert program** (em reformulação).
- **HIPAA** — proteção de dados.

### 4.2 Categorias FDA

| Categoria | Descrição |
|-----------|-----------|
| **Wellness** | Promoção de bem-estar geral; **fora do FDA**. |
| **Medical Device Data System (MDDS)** | Não regula. |
| **Clinical Decision Support (CDS)** | Regras específicas para isenção. |
| **SaMD** | Regulado pelo FDA. |

### 4.3 Análise para o AraFlow

| Cenário | Categoria FDA |
|---------|---------------|
| **MVP wellness** | Wellness (fora). |
| **CDS para profissional** | Possível isenção (com critérios). |
| **SaMD classe I/II** | 510(k) necessário. |
| **SaMD classe III** | PMA (Preamarket Approval). |

### 4.4 Critérios para "wellness" (FDA)

- **Finalidade:** bem-estar geral (não tratamento de doença específica).
- **Risco baixo.**
- **Sem alegação médica específica.**

> *FDA Guidance: General Wellness: Policy for Low-Risk Devices.*

### 4.5 Requisitos para 510(k)

- Dossiê técnico.
- Avaliação de equivalência (predicate device).
- Software documentation (IEC 62304).
- Risk management (ISO 14971).
- Cybersecurity documentation.
- Testes (V&V).

### 4.6 Timeline estimado (FDA)

| Etapa | Duração |
|-------|---------|
| **Preparação** | 6-12 meses |
| **Submissão 510(k)** | 3-6 meses de análise |
| **Total** | **9-18 meses** |

---

## 5. Classificação na Europa (MDR / IVDR)

### 5.1 Marco regulatório

- **MDR 2017/745** — substituiu a MDD em maio 2021.
- **IVDR 2017/746** — para diagnósticos in vitro.
- **GDPR** — proteção de dados.
- **MDCG Guidance** — orientações da Comissão Europeia.

### 5.2 Classificação MDR (Anexo VIII)

Baseada em:
- Duração (transitório, curto prazo, longo prazo).
- Invasibilidade.
- Tipo de contato.
- Tipo de energia.
- Local de uso.
- Risco para paciente.

### 5.3 Análise para o AraFlow

| Cenário | Classe MDR |
|---------|------------|
| **Wellness (informação)** | Fora do escopo MDR. |
| **Software terapêutico sem contato direto** | **Classe I** (mais comum). |
| **Com ajuste terapêutico** | **Classe IIa** (médio risco). |
| **Com decisão crítica** | **Classe IIb ou III**. |

### 5.4 Requisitos MDR

- **QMS ISO 13485.**
- **Avaliação de conformidade** (via notified body se > classe I).
- **Documentação técnica** completa.
- **Avaliação clínica** (clinical evaluation report).
- **PMS** (Post-Market Surveillance).
- **PSUR** (Periodic Safety Update Report).
- **EUDAMED** (registro).
- **UDI** (Unique Device Identification).
- **Pessoa responsável** (Person Responsible for Regulatory Compliance — PRRC).
- **Representante europeu** (se aplicável).

### 5.5 Timeline estimado (MDR)

| Etapa | Duração |
|-------|---------|
| **Preparação** | 9-18 meses |
| **Avaliação por Notified Body** | 6-12 meses |
| **Total** | **15-30 meses** |

---

## 6. Quando o AraFlow deixa de ser wellness?

### 6.1 Critérios que tiram da categoria wellness

> *Baseado em FDA, ANVISA, MDR.*

| Critério | Peso |
|----------|------|
| **Reivindicar diagnóstico de doença** | Fortíssimo — vira SaMD. |
| **Reivindicar tratamento de doença** | Fortíssimo — vira SaMD. |
| **Prescrição por profissional** | Forte. |
| **Alegação de benefício clínico específico** | Forte. |
| **Medição de desfechos clínicos** | Moderado. |
| **Personalização por IA** | Moderado. |
| **Biofeedback em tempo real** | Forte (Fase 3). |
| **Algoritmo que ajusta dose** | Fortíssimo. |
| **Marketing para profissionais de saúde** | Moderado. |
| **Integração com prontuário como ferramenta clínica** | Forte. |
| **Recomendação por sociedades médicas** | Moderado. |

### 6.2 Linha de corte (sugestão multidisciplinar)

> **O AraFlow deixa de ser "wellness puro" no momento em que:**
> 1. Reivindica benefício terapêutico específico, **OU**
> 2. Faz ajuste automatizado baseado em biomarcador, **OU**
> 3. Recomenda dose por IA, **OU**
> 4. Profissional o prescreve como monoterapia.
>
> **Em qualquer desses casos, é SaMD.**

---

## 7. Riscos regulatórios por mercado

### 7.1 Brasil

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| ANVISA classificar como SaMD não registrado | Média (Fase 2+) | Alto | Submissão voluntária preventiva. |
| LGPD não conformidade | Baixa (com cuidado) | Muito alto | DPO desde MVP. |
| Propaganda irregular | Média | Médio | Revisão jurídica de todo marketing. |

### 7.2 EUA

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| FDA enforcement por marketing off-label | Média | Alto | Revisão de claims. |
| Classificação como SaMD sem 510(k) | Média (Fase 2+) | Alto | Submissão voluntária. |
| HIPAA violation | Baixa | Alto | Privacy by design. |

### 7.3 Europa

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| MDR enforcement | Alta (pós-2025) | Alto | Notified Body desde cedo. |
| GDPR violation | Baixa (com cuidado) | Muito alto | DPO + auditoria. |
| Notified Body backlog | Alta | Alto | Engajar cedo. |

---

## 8. Como permanecer como wellness no MVP

### 8.1 Regras de comunicação

> *Status: CONSENSO. Obrigatório no MVP.*

| Permitido | Proibido |
|-----------|----------|
| "Ferramenta de apoio" | "Trata ansiedade" |
| "Pode ajudar a relaxar" | "Reduz ansiedade clinicamente" |
| "Baseado em evidências" | "Comprovado por estudos clínicos do AraFlow" |
| "Consulte seu profissional" | "Substitui medicação" |
| "Bem-estar" | "Tratamento" |
| "Para sua rotina de cuidado" | "Para tratamento de..." |

### 8.2 Decisões de produto (MVP)

1. **Sem prescrição formal** — apenas sugestão.
2. **Sem reivindicação clínica específica.**
3. **Disclaimer em toda sessão.**
4. **Marketing cuidadoso.**
5. **LGPD compliance completo.**
6. **Logs de segurança.**

### 8.3 Quando começar a tratar como SaMD

Recomendação do painel:
> **Iniciar processo regulatório quando:**
> 1. Adotar prescrição formal, **OU**
> 2. Lançar IA preditiva em produção, **OU**
> 3. Adicionar biofeedback em tempo real.

> *Estimativa: Fase 2 (2027-Q3).*

---

## 9. Requisitos para futura certificação SaMD

### 9.1 Sistema de Qualidade (QMS)

- **ISO 13485** — base para a maioria das jurisdições.
- Documentação: políticas, procedimentos, registros.
- Auditoria interna + externa.

### 9.2 Gestão de risco

- **ISO 14971** — risk management process.
- Risk management plan.
- Risk analysis (FMEA, FTA).
- Risk evaluation, control, monitoring.

### 9.3 Desenvolvimento de software

- **IEC 62304** — software lifecycle processes.
- Classificação de segurança do software (A, B, C).
- Documentação de arquitetura, design, testes.

### 9.4 Cybersecurity

- **IEC 81001-5-1** (em desenvolvimento).
- NIST CSF.
- Threat modeling.
- SBOM, SAST, DAST.

### 9.5 Usabilidade

- **IEC 62366-1** — usability engineering.
- Testes com usuários representativos.
- Análise de tarefas críticas.

### 9.6 Avaliação clínica

- Literatura clínica relevante.
- Estudos clínicos próprios (quando necessário).
- Clinical Evaluation Report (CER).

### 9.7 Pós-mercado

- PMS plan.
- PSUR.
- Vigilância ativa.
- Customer feedback.

---

## 10. Estratégia regulatória por fase

### 10.1 MVP (Fase 1) — Wellness

| Ação | Status |
|------|--------|
| Classificar como wellness | ✅ |
| Comunicação sem claims clínicos | ✅ |
| LGPD compliance | ✅ |
| Logs clínicos | ✅ |
| Disclaimer em todo lugar | ✅ |
| Marketing review | ✅ |

### 10.2 Fase 2 — Início de SaMD

| Ação | Status |
|------|--------|
| ISO 13485 setup | 🔄 |
| Risk management file | 🔄 |
| Avaliação clínica inicial | 🔄 |
| Consulta com ANVISA (pré-submissão) | 🔄 |
| Consulta com FDA (Q-Sub) | 🔄 |
| Classificação de risco formal | 🔄 |

### 10.3 Fase 3 — Submissão SaMD

| Ação | Status |
|------|--------|
| Validação clínica completa | ⏳ |
| Submissão ANVISA | ⏳ |
| Submissão FDA 510(k) | ⏳ |
| Engajamento Notified Body (MDR) | ⏳ |
| Estabelecer PMS plan | ⏳ |

---

## 11. Comparação entre jurisdições

| Aspecto | Brasil (ANVISA) | EUA (FDA) | Europa (MDR) |
|---------|-----------------|-----------|--------------|
| **Velocidade de aprovação** | Média | Rápida (510k) | Lenta |
| **Custo estimado** | Médio | Médio | Alto |
| **Certeza regulatória** | Alta | Alta | Alta (mas complexo) |
| **Estudos clínicos exigidos** | Às vezes | Às vezes | Quase sempre |
| **Notified Body** | Não | Não | Sim (classe II+) |
| **Pessoa responsável local** | Sim | Sim | Sim |
| **Aceitação internacional** | LATAM | Global | Global |
| **Risco reputacional** | Médio | Alto | Alto |

---

## 12. Compliance com LGPD / GDPR / HIPAA

### 12.1 LGPD (Brasil)

> Detalhamento completo em `15_SECURITY.md`.

- DPO obrigatório.
- RIPD obrigatório.
- Consentimento granular.
- Direitos do titular (acesso, correção, exclusão).
- ANPD como regulador.

### 12.2 GDPR (Europa)

- DPO obrigatório.
- DPIA (Data Protection Impact Assessment).
- Consentimento explícito.
- Privacy by design.
- Direito ao esquecimento.
- EDPB como regulador.

### 12.3 HIPAA (EUA — se entrar nesse mercado)

- PHI (Protected Health Information).
- Privacy Rule + Security Rule.
- BAA (Business Associate Agreement).
- HHS/OCR como regulador.

### 12.4 Diferenças práticas

| Aspecto | LGPD | GDPR | HIPAA |
|---------|------|------|-------|
| **DPO obrigatório** | Sim (se alto volume) | Sim (em muitos casos) | Não (Privacy Officer) |
| **Consentimento granular** | Sim | Sim | Opt-in / opt-out varia |
| **Direito ao esquecimento** | Sim | Sim | Limitado |
| **Transferência internacional** | Permitida com garantias | Adequacy decision | BAA |
| **Multa máxima** | 2% faturamento | 4% faturamento global | $1.9M / ano |

---

## 13. Marketing e publicidade

### 13.1 Princípios

> *Status: CONSENSO.*

1. **Sem alegações falsas ou exageradas.**
2. **Sem promessas de cura.**
3. **Sem uso de depoimentos que violem regulação.**
4. **Sempre com disclaimer.**
5. **Revisão jurídica de todo material.**
6. **Compliance com CDC/CONAR** (no Brasil).

### 13.2 Templates aprovados

> *Sempre usar templates aprovados pelo jurídico.*

- Claims genéricos de bem-estar: permitidos.
- Claims de benefício clínico específico: **apenas** com base em estudo publicado.
- Depoimentos: com disclaimer de "resultado individual pode variar".
- Antes/depois: **proibido** para SaMD em muitas jurisdições.

### 13.3 Categorias de claims

| Categoria | Exemplo | Permitido em MVP? |
|----------|---------|-------------------|
| **Genérica** | "Promova bem-estar" | ✅ |
| **Educacional** | "Estudos sugerem que respiração lenta pode ajudar" | ✅ |
| **Clínica específica** | "Reduz ansiedade em 50%" | ❌ (até validação) |
| **Comparativa** | "Melhor que X" | ❌ |
| **Depoimento** | "Carlos melhorou" | ⚠️ Com disclaimer |

---

## 14. Responsabilidades pós-mercado

### 14.1 Vigilância pós-comercialização

- **Coleta sistemática** de eventos adversos.
- **Análise periódica** de tendências.
- **Investigação** de eventos graves.
- **Ações corretivas** (recall, alerta, update).
- **Relatórios** a autoridades.

### 14.2 Prazo

- **Vigilância contínua** ao longo de toda a vida do produto.

### 14.3 Responsabilidades específicas

| Responsabilidade | Dono |
|------------------|------|
| **Vigilância clínica** | Diretor clínico |
| **Vigilância de segurança** | DPO + Security Lead |
| **Vigilância técnica** | Tech Lead |
| **Vigilância regulatória** | Jurídico + RA (Regulatory Affairs) |

---

## 15. Roadmap regulatório

### 15.1 Marcos

| Marco | Fase | Data |
|-------|------|------|
| **R1 — Wellness classificado** | F1 | MVP |
| **R2 — LGPD compliance** | F1 | MVP |
| **R3 — ISO 13485 setup** | F2 | Q2 2027 |
| **R4 — Risk management file** | F2 | Q3 2027 |
| **R5 — Clinical evaluation report v1** | F2 | Q3 2027 |
| **R6 — Pré-submissão ANVISA** | F3 | Q1 2028 |
| **R7 — Submissão ANVISA SaMD** | F3 | Q2 2028 |
| **R8 — Submissão FDA 510(k)** | F3 | Q2 2028 |
| **R9 — Notified Body engagement** | F3 | Q2 2028 |
| **R10 — Certificação (primeira)** | F3+ | Q4 2028+ |

### 15.2 Investimento estimado

| Fase | Investimento regulatório |
|------|-------------------------|
| **MVP (wellness)** | Baixo |
| **Fase 2 (setup SaMD)** | Médio |
| **Fase 3 (submissão)** | Alto |
| **Total até certificação** | Significativo |

---

## 16. Questões em aberto

> *Decisões pendentes que requerem consulta jurídica formal.*

1. **Submissão simultânea ANVISA + FDA / sequencial?**
   - Recomendação: sequencial, começar Brasil.
2. **MDR classe IIa via auto-certificação ou Notified Body?**
   - Recomendação: Notified Body (mais seguro).
3. **Modelo de submissão para IA adaptativa?**
   - FDA tem guidance específico (PCCP).
4. **Aceitação em outros mercados LATAM?**
   - Cada país tem regra própria.
5. **Reivindicação de "suporte a cannabis medicinal"?**
   - Zona cinza. Cuidado redobrado.
6. **Classificação do modo infantil?**
   - Pode ser classificado separado.
7. **Integração com wearables — quem regula?**
   - Boundary regulation. Cuidado.

---

## 17. Recomendações finais

> *Status: CONSENSO.*

### 17.1 Para o MVP

1. **Permanecer como wellness** com comunicação cuidadosa.
2. **Engajar advogado especializado** em saúde digital.
3. **Documentar toda decisão clínica** (trilha de auditoria).
4. **Preparar terreno** para Fase 2 SaMD.
5. **Investir em QMS** desde cedo.

### 17.2 Para a Fase 2

1. **Iniciar QMS ISO 13485** o mais cedo possível.
2. **Engajar Notified Body** antes de precisar.
3. **Plano de validação clínica** robusto.
4. **Revisão contínua** de claims de marketing.

### 17.3 Para a Fase 3

1. **Submissão regulatória formal.**
2. **Pós-mercado robusto.**
3. **Revisão contínua** de novos biomarcadores (biofeedback).
4. **Atualização** com mudanças regulatórias.

### 17.4 Princípio geral

> **Em dúvida, subclassificar para mais rigoroso.** Custos extras de compliance são menores que custos de sanções.

---

## 18. Glossário regulatório

| Termo | Significado |
|-------|-------------|
| **SaMD** | Software as a Medical Device. |
| **510(k)** | Submissão FDA para classe II. |
| **PMA** | Pre-Market Approval (FDA classe III). |
| **MDR** | Medical Device Regulation (UE). |
| **MDD** | Medical Device Directive (UE, antigo). |
| **Notified Body** | Organismo notificado (UE). |
| **QMS** | Quality Management System. |
| **CER** | Clinical Evaluation Report. |
| **PMS** | Post-Market Surveillance. |
| **PSUR** | Periodic Safety Update Report. |
| **PRRC** | Person Responsible for Regulatory Compliance. |
| **UDI** | Unique Device Identification. |
| **EUDAMED** | European Database on Medical Devices. |
| **RIPD** | Relatório de Impacto à Proteção de Dados. |
| **DPIA** | Data Protection Impact Assessment (GDPR). |
| **PHI** | Protected Health Information (HIPAA). |
| **BAA** | Business Associate Agreement (HIPAA). |
| **CONAR** | Conselho Nacional de Autorregulamentação Publicitária. |

---

## 19. Atualização deste documento

- **Revisão trimestral** pela equipe jurídica + clínica.
- **Revisão extraordinária** se:
  - Mudança regulatória.
  - Evento adverso relevante.
  - Decisão de submissão.
  - Feedback de autoridades.

---

*Regulação é proteção. Respeite-a.*