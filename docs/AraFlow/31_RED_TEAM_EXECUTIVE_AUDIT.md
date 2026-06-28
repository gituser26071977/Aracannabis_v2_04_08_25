# AraFlow — Red Team Executive Audit (Technical Due Diligence)

> **Versão:** 2.0.0
> **Data:** 2026-06-25
> **Status:** Fase 0.75 — Technical Due Diligence
> **Natureza:** Auditoria independente contratada por fundo internacional de VC para análise pré-investimento de R$ 50M.
> **Mandato:** *Encontrar tudo o que está errado. Não proteger nada. Não defender nada.*

> **Princípio:** *Não somos pagos para ser gentis. Somos pagos para impedir investimentos ruins. Se o AraFlow merece investimento, diremos. Se não merece, diremos com a mesma firmeza.*

---

## Sumário

1. Executive Summary
2. Score Executivo (21 dimensões)
3. TOP 100 Riscos
4. TOP 100 Oportunidades
5. TOP 50 Decisões a Revogar
6. TOP 50 Funcionalidades a Remover
7. TOP 50 Funcionalidades Ausentes
8. O que cada empresa faria diferente (13 players)
9. O que um Hospital Privado exigiria
10. O que uma Operadora de Saúde exigiria
11. O que a ANVISA questionaria
12. O que o FDA exigiria
13. O que impediria certificação como SaMD
14. O que faria um Investidor desistir
15. O que faria um Médico nunca prescrever
16. O que faria um Paciente desinstalar
17. Funcionalidades que parecem excelentes mas ninguém usará
18. Funcionalidades de alto custo e baixo valor
19. Funcionalidades que deveriam entrar imediatamente
20. Funcionalidades que deveriam ser adiadas para v2.0
21. O MVP está grande demais?
22. Maior erro estratégico
23. Maior diferencial competitivo
24. R$ 2M e 12 meses — plano radical
25. Conclusão Executiva

---

## 1. Executive Summary

### Veredicto

> # NÃO
>
> **Este projeto, na forma atual, NÃO seria aprovado para investimento de R$ 50M.**

### Justificativa detalhada

O AraFlow apresenta uma tese de mercado defensável — saúde mental digital no Brasil é mercado estruturalmente desassistido, com déficit de profissionais, e há espaço real para um produto brasileiro sério com curadoria clínica. Até aqui, há tese.

A documentação existente revela uma equipe que **sabe escrever** sobre saúde digital com competência rara. A revisão crítica dos 12 protocolos (28) é corajosa. A separação LGPD/GDPR é tecnicamente precisa. O design system tem bom gosto. O manifesto de marketing é literariamente honesto. Tudo isso é mérito.

Mas **competência em documentar não é competência em executar**. E é aqui que o projeto desmorona.

**Os 10 motivos centrais pelos quais o AraFlow seria recusado:**

1. **Pear Therapeutics faliu em abril de 2023** após aprovação FDA, evidência robusta para reSET/reSET-O, prescrição formal em mais de 200 mil pacientes e partnership com a Novartis — o mercado de DTx **não pagou o suficiente, rápido o bastante**. O AraFlow ignora essa lição. Quem não aprende com fracasso recente está condenado a repeti-lo.

2. **Akili Interactive viu seu valuation despencar de US$ 1B para menos de US$ 50M** após lançamento comercial de EndeavorRx (aprovado pelo FDA em 2020). Mesmo com aprovação regulatória, prescrição médica e evidência robusta em TDAH pediátrico, a tração comercial foi medíocre. O AraFlow propõe modelo de negócio similar com capital menor.

3. **Headspace e Calm cortaram 15-20% de seus quadros em 2023**. O mercado de wellness digital está saturado. Headspace Health (fusão 2021) teve valuation privado de US$ 3B revertido para valuation muito menor em rodadas subsequentes. **A bolha estourou.**

4. **Não existe tração mínima descrita**. Zero usuários ativos. Zero sessões realizadas. Zero médicos prescritores. Zero estudos clínicos publicados. **30 documentos de planejamento e zero evidência empírica.** Isso é, em si, sinal de risco altíssimo.

5. **A documentação mistura wellness e SaMD como se fossem escolhas intercambiáveis**. Reguladores odeiam isso. Wellness escapa da regulação sanitária mas limita claims; SaMD permite claims clínicos mas exige QMS, IEC 62304, ISO 14971, IEC 62366, ISO 13485, evidência robusta e anos de processo. **Não se transita de um para o outro sem plano explícito — que o AraFlow não tem.**

6. **12 modelos de negócio analisados em paralelo, com recomendação final "híbrido em camadas"**. Esta é exatamente a decisão que uma equipe toma quando não consegue priorizar. Vendas B2C, B2B-Pro, B2B-Enterprise, B2B-Corporate, B2B-University, B2B-Research, White Label, Licensing, Marketplace, Freemium, Premium, Pay-per-use, Hybrid — **treze personas de venda** para um MVP que ainda não existe.

7. **Pesquisa clínica custa R$ 5-8M para 5 estudos em 5 anos**. Em uma rodada de R$ 50M, isso consome 10-16% do capital em **5 anos de burn** sem receita garantida. Quem financia isso? Investidor de VC tem horizonte de 7-10 anos e precisa de **crescimento de tração visível**, não papers acadêmicos.

8. **Promessa de 16 eixos de produto em 10 anos** (IA, wearables, HRV, EEG, respiração automática, personalização, Digital Twin, medicina preventiva, longevidade, cannabis medicinal, sono, dor, saúde mental, reabilitação, telemedicina, pesquisa clínica) — para uma equipe que ainda **não escreveu uma linha de código**. Roadmap bom cabe em mesa de operações. Este cabe em ficção científica.

9. **A integração com AraOS é simultaneamente a maior força e a maior vulnerabilidade**. Dependência de outra plataforma interna cria risco de governança, priorização conflitiva, e potencial conflito de acionistas. A documentação **não discute mitigação**.

10. **O Brasil tem Risco País elevado para capital de VC em 2026**: câmbio volátil, juros altos (Selic 12-14%), regulação sanitária em transição. Investidor internacional exige **prêmio de risco alto** para investir aqui — o que significa que o AraFlow precisa entregar **muito mais resultado por real investido** do que um competidor americano.

### Recomendação ao Comitê

**Recusar R$ 50M.**

**Considerar — condicionalmente — uma rodada Seed/A de R$ 5-10M** mediante:

1. **Redução de 60-70% no escopo do MVP** — mantendo 3 protocolos, removendo wearables, voice, avatar 3D, marketplace, comunidade, white label, e 8 dos 12 modelos de negócio.
2. **Integração AraOS como feature**, não como produto paralelo.
3. **Decisão regulatória explícita**: wellness puro **OU** SaMD. Não ambos.
4. **Tração mínima comprovada** antes de qualquer rodada > R$ 10M: 1.000 usuários ativos, 30% D7 retention, NPS ≥ 50, 50 médicos prescritores ativos.
5. **1 RCT piloto iniciado e em curso**, não 5 estudos planejados.
6. **Time com co-founder técnico** com experiência prévia em healthtech. A documentação não revela a composição completa do time, o que é sinal de governance fraca.

**Se essas condições forem aceitas, a tese volta a ser discutível.** Sem elas, o AraFlow é mais uma apresentação de seed deck inflada pós-bolha.

---

## 2. Score Executivo (21 dimensões)

> *Notas de 0 (péssimo) a 10 (excelente). Cada nota é a média entre especialistas da mesa redonda.*

### Visão — **5/10**

**Justificativa:** A visão de 10 anos é poeticamente competente, com 16 eixos aspiracionais — mas carece de credibilidade técnica. Promete Digital Twin, smart textiles, IA multimodal, estimulação elétrica fraca. Cada item demandaria uma startup dedicada e R$ 50-200M cada. **Visão boa deve ser aspiracional mas crível. Esta é fantasiosa para uma equipe em estágio pré-MVP.**

### Produto — **4/10**

**Justificativa:** O "produto AraFlow" é, na verdade, **três produtos distintos** embalados como um: (a) app wellness B2C, (b) plataforma clínica prescritiva B2B, (c) DTx SaMD regulado. Cada um exige stacks, equipe, métricas, ciclos regulatórios e de capital diferentes. A documentação lista features sem hierarquia clara de prioridade. Falta uma **matriz de trade-offs** entre escopo, tempo, capital e risco.

### Diferenciação — **4/10**

**Justificativa:** Os cinco PODs propostos (prescrição clínica, evidência, integração AraOS, LGPD, Brasil) são frágeis: Headspace Health tem prescrição formal em mercados selecionados; BetterHelp (Teladoc) tem prescrição; Calm Health visa o mesmo; a integração AraOS é local; LGPD é obrigação legal; "Brasil" não é diferencial defensável. **O único POD verdadeiramente defensável é a integração nativa com AraOS — e o documento não a explora tecnicamente.**

### UX — **5/10**

**Justificativa:** Documentação de UX é volumosa mas com sinais de overengineering: avatares 3D customizáveis, animações em três níveis de detalhe, micro-interações em cada toque. **Em healthtech, clareza ganha de espetáculo.** O onboarding proposto (7 telas com escalas clínicas) é receita para drop-off de 70%+. Não há dado de teste com usuário real que sustente as decisões de UX.

### UI — **6/10**

**Justificativa:** O design system (06_DESIGN_SYSTEM.md) tem identidade visual coerente: verde-azulado calmo, tipografia clara, movimento orgânico, paleta suave. Mas o sistema é **estético, não validado com usuários**. Ausência de testes de protótipo com populações-alvo (gestantes, idosos, TDAH). Falta discussão sobre estados emocionais extremos (crise de pânico não permite UI minimalista).

### Fluxo — **4/10**

**Justificativa:** Os fluxos detalhados (onboarding, sessão, pós-sessão) são internamente consistentes, mas há sinais de overengineering: triagem clínica complexa no onboarding, fluxos paralelos para B2C e B2B, e-CRFs elaborados. **Fluxos bons resolvem um problema por vez. Estes tentam resolver cinco.**

### Design System — **6/10**

**Justificativa:** O design system é detalhado e tem bom gosto. Documentação de tokens, componentes, motion, estados. **Mas não menciona acessibilidade WCAG AA/AAA explicitamente**, não discute leitura por leitor de tela (VoiceOver/TalkBack), não trata daltonismo. Em produto de saúde para adultos 60+, isso é grave.

### Arquitetura — **6/10**

**Justificativa:** Decisão monolito modular é tecnicamente defensável. Separação de domínios por bounded contexts é coerente. Eventos assíncronos bem justificados. **Mas faltam**: análise de custo de cloud em escala, plano de disaster recovery concreto, threat model de segurança, estratégia de cache para latência em wearables, plano de testes de carga, e plano de observabilidade (logging, métricas, tracing).

### Escalabilidade — **5/10**

**Justificativa:** Arquitetura está tecnicamente preparada para escala horizontal de **tecnologia**. Mas escala **clínica** é diferente: como escalar suporte humano 24/7 com equipe multidisciplinar? Como treinar 1.000 novos médicos prescritores por ano? Como manter qualidade regulatória com 5M de usuários? **Escalar um SaMD é exponencialmente mais difícil que escalar um SaaS B2C.**

### Segurança — **6/10**

**Justificativa:** Documentação LGPD/GDPR é robusta. Mas há lacunas graves: (1) ausência de threat model documentado; (2) ausência de discussão sobre criptografia em repouso vs. em trânsito; (3) ausência de plano de resposta a incidentes; (4) ausência de pentest externo; (5) ausência de discussão sobre segregação de dados sensíveis (saúde mental é categoria especial LGPD art. 11); (6) ausência de bug bounty.

### Ciência — **6/10**

**Justificativa:** A revisão crítica (28) é o ponto mais alto do projeto. Força a equipe a confrontar a evidência com honestidade. Tummo removido, Wim Hof condicionado, Buteyko direcionado a nicho. **Mas a revisão mistura níveis de evidência de forma inconsistente** — protocolos mantidos com nível C e B sem critério claro de corte. Onde está o protocolo metodológico que sustentou essas decisões?

### Protocolos Clínicos — **7/10**

**Justificativa:** O documento 28 é metodologicamente sólido: GRADE aplicado, riscos por protocolo, contraindicações explícitas. **É o documento mais maduro do projeto.** Mas ainda mantém 9 protocolos no MVP com evidência predominantemente B/C — sem critério explícito de por que esses 9 e não outros.

### Regulação — **3/10**

**Justificativa:** **É a dimensão mais fraca do projeto.** O documento 24 tenta abraçar Brasil, EUA e Europa simultaneamente — uma receita para fazer tudo mal. A posição "começamos como wellness e depois viramos SaMD" é exatamente o que reguladores mais fiscalizam: empresas que jogam no campo regulatório mais frouxo até serem pegas. **A documentação não discute o que acontece se a ANVISA classificar AraFlow retroativamente como SaMD durante o MVP wellness** — incluindo implicações de recall, eventos adversos retrospectivos e responsabilidade civil.

### Estratégia — **4/10**

**Justificativa:** 30 documentos, 16 eixos de longo prazo, 13 modelos de negócio analisados — **estratégia boa cabe em uma página de execução. Esta cabe em enciclopédia.** Falta clareza sobre: ICP único, proposta de valor mensurável, unidade de sucesso primária, critérios de pivotagem, gatilhos de decisão.

### Modelo de Negócio — **4/10**

**Justificativa:** "Híbrido em camadas" não é modelo de negócio — é ausência de modelo. Os preços propostos (R$ 29,90/mês B2C, R$ 79-199/mês B2B-Pro) não têm validação de willingness to pay. Não há benchmark competitivo explícito para CAC. Não há clareza sobre payback period. **Em healthtech brasileira, CAC médio é R$ 100-300 por usuário B2C e R$ 1.000-5.000 por clínica B2B. Com esses CACs e os preços propostos, unit economics não fecham.**

### Monetização — **3/10**

**Justificativa:** Documento 26 lista 12+ modelos e recomenda "híbrido em camadas". Isso é o que uma equipe faz quando **não tem coragem de matar opções**. Não há clareza sobre qual modelo financia qual fase. Não há validação de que o mercado paga os preços propostos. Não há cálculo de LTV por persona.

### Pesquisa Clínica — **5/10**

**Justificativa:** Protocolo de pesquisa (25) é metodologicamente sólido: desenho de estudos, escalas validadas, plano estatístico. **Mas o investimento (~R$ 5-8M para 5 estudos em 5 anos) é incompatível com a tese de investimento.** R$ 50M precisam financiar produto, equipe e go-to-market. Quem financia pesquisa clínica quando se precisa de tração comercial? **A documentação não resolve este conflito central.**

### Roadmap — **4/10**

**Justificativa:** Roadmap propõe, em 10 anos: 5 SaMDs, FDA, MDR, IA multimodal, Digital Twin, smart textiles. **Roadmap bom é o que cabe na mesa de operações. Este cabe apenas em ficção científica.** Não há milestones trimestrais claros, não há critérios de go/no-go por fase, não há gatilhos de pivotagem.

### Marketing — **5/10**

**Justificativa:** Documento 27 está entre os melhores do projeto. Tem manifesto, voz, tom, comparação com concorrentes, linguagem proibida e preferida. **Mas erra ao subestimar CAC em saúde digital no Brasil** (R$ 50-200/usuário B2C é comum) e ao propor comparação agressiva com Headspace/Calm em estágio pré-MVP. Marketing honesto é bom; marketing de combate é cedo.

### Execução — **3/10**

**Justificativa:** **Documentação abundante não é execução. 90% das healthtechs documentais morrem na fase "documentação abundante".** A documentação descreve 32 documentos, 16 eixos, 13 modelos, 12 protocolos — mas não há evidência de capacidade de execução: nenhuma release, nenhum usuário beta, nenhum estudo piloto, nenhum protótipo testado, nenhuma métrica real.

### Potencial Internacional — **5/10**

**Justificativa:** Mercado brasileiro é grande mas não é global. A documentação menciona expansão LATAM (México, Colômbia, Argentina) e global — mas não discute barreiras linguísticas, culturais, regulatórias (México tem COFEPRIS, Argentina tem ANMAT, etc.). LATAM é viável em 5-7 anos; global é fantasia em 10 anos sem tração comprovada primeiro.

### **Média ponderada: 4,6/10**

> **Tese discutível. Execução proposta medíocre. Decisão de investimento: NÃO na forma atual.**

---

## 3. TOP 100 Riscos

> *Ordenados por criticidade (Probabilidade × Impacto × Urgência). P = probabilidade (A=alta, M=média, B=baixa). I = impacto (A=alto, M=médio, B=baixo). U = urgência (A=imediato, M=12 meses, B=24+ meses).*

### Críticos (ação imediata)

| # | Risco | P | I | U | Mitigação |
|---|-------|---|---|---|-----------|
| 1 | **Pear Therapeutics 2.0**: construir DTx aprovado e descobrir que mercado não paga o suficiente. | M | A | A | Pivotar para B2B puro com ROI demonstrado antes de buscar aprovação regulatória. |
| 2 | **Time-to-market inflado**: 3-5 anos para SaMD; capital se esgota antes. | A | A | A | Submissão regulatória só após tração mínima validada. |
| 3 | **Headspace/Calm compra startup brasileira e entra agressivamente**. | M | A | M | Construir defensibilidade clínica que marcas globais não conseguem replicar. |
| 4 | **Médicos não prescrevem**: baixa adoção prescritiva. | A | A | A | Validar com 50 médicos antes de investir em B2B-Pro. |
| 5 | **Pacientes abandonam em 7 dias**: baixa retenção. | A | A | A | Redesenhar onboarding para reduzir atrito a 90s. |
| 6 | **Equipe multidisciplinar cara consome runway**: nutricionistas, psicólogos, neurocientistas. | A | M | A | Contratar sob demanda (consultores) e não como equipe fixa. |
| 7 | **LGPD muda interpretação durante operação**: jurisprudência. | M | A | M | DPO desde dia 1 + consultoria jurídica permanente. |
| 8 | **Estudos clínicos falham em mostrar eficácia**: RCTs nulos. | M | A | A | Desenhar estudos com desfechos realistas, não overpromise. |
| 9 | **Aprovação ANVISA não gera prescrição**: regulação ≠ tração. | M | A | M | Marketing médico ativo antes de regulação. |
| 10 | **Integração AraOS vira amarra**: dependência de plataforma interna. | M | A | M | Manter AraFlow utilizável standalone. |
| 11 | **CAC B2C alto demais para unit economics funcionar**: R$ 100-300 por usuário. | A | A | A | Pivotar para B2B puro. |
| 12 | **Wearables mudam rápido**: integração vira obsoleta em 18 meses. | A | M | M | Abstração de camada de integração. |
| 13 | **Reembolso por planos de saúde não acontece**: mercado não está pronto. | A | A | M | Não basear tese em reembolso. |
| 14 | **Eventos adversos graves**: hiperventilação, síncope, convulsão. | B | A | A | Triagem rigorosa + protocolo de emergência no app + seguro. |
| 15 | **Crise reputacional por marketing exagerado**: artigo investigativo. | M | A | M | Marketing honesto + compliance review em cada peça. |
| 16 | **Mudança regulatória ANVISA**: novas RDCs. | M | M | M | Eng. regulatória dedicada + monitorar agenda. |
| 17 | **Investidor entra e sai em 18 meses**: pressão por exit prematuro. | M | A | M | Investidores com horizonte 7-10 anos (Seed/A), não growth. |
| 18 | **Conflito de interesse AraFlow/AraOS**: priorização interna conflitiva. | M | A | M | Estrutura societária independente + SLA entre empresas. |
| 19 | **Falta de evidência robusta para cannabis + respiração**: literatura escassa. | A | M | A | Pesquisa clínica específica antes de claims. |
| 20 | **Coorte pediátrica (TEA, TDAH) com evento adverso grave**: risco ético. | B | A | M | Comité independente de segurança + seguro de pesquisa + exclusão de menores no MVP. |

### Altos (ação em 90 dias)

| # | Risco | P | I | U | Mitigação |
|---|-------|---|---|---|-----------|
| 21 | **ANVISA exige estudos locais**: tempo dobrado. | M | A | M | Iniciar pesquisa clínica no ano 1. |
| 22 | **FDA exige De Novo**: anos de processo. | B | A | M | FDA opcional; LATAM primeiro. |
| 23 | **MDR europeu exige Notified Body cara e demorada**. | B | A | M | Não mirar Europa nos primeiros 5 anos. |
| 24 | **Cibersegurança falha**: vazamento de dados de saúde mental. | B | A | A | Pentests externos + bug bounty + DPO. |
| 25 | **Vendor de cloud tem incidente**: dependência crítica. | B | A | M | Multi-cloud + DR documentado + backups offline. |
| 26 | **Médicos prescritores não treinados em DTx**: baixa literacia. | A | M | M | Educação médica contínua via CRM. |
| 27 | **Pacientes confundem wellness com tratamento**: expectativas erradas. | A | M | M | Disclaimer explícito em cada tela clínica. |
| 28 | **Planos de saúde não veem ROI em 6 meses**: churn B2B. | M | M | M | Contratos plurianuais + ROI documentado. |
| 29 | **Big Health (Sleepio) entra no Brasil**: concorrente com evidência NHS. | M | M | M | Foco em cannabis como diferencial. |
| 30 | **SUS/equoterapia/yoga/práticas tradicionais oferecem alternativa gratuita**. | A | B | M | Diferenciação por evidência + prescrição formal. |
| 31 | **SUS oferece TCC gratuita**: SUS absorve parte do mercado. | A | M | M | Foco em adjuvância + acessibilidade + cannabis. |
| 32 | **Apps gratuitos saturam**: competição de preço. | A | M | M | Modelo B2B estruturado com switching cost alto. |
| 33 | **Inflação médica**: custo de equipe multidisciplinar sobe. | M | M | M | Terceirizar onde possível. |
| 34 | **Dificuldade de contratar estatístico clínico no Brasil**: talento escasso. | M | M | M | Contrato com CRO ou universidade (USP, UFMG). |
| 35 | **Comitê científico vira "rubber stamp"**: governance falha. | M | M | M | Renovação bienal de membros; atas públicas. |
| 36 | **Pacientes mentem em escalas autorrelatadas**: dado de baixa qualidade. | A | M | M | Triangulação com wearables + profissional. |
| 37 | **IA generativa alucina**: responde coisa errada em momento crítico. | B | A | M | Limites estritos de IA + revisão humana obrigatória. |
| 38 | **Wearables sub-ótimos em peles escuras**: viés de algoritmo. | A | M | M | Calibração com amostras racialmente diversas. |
| 39 | **LGPD esquece**: equipe ignora privacy by design. | A | A | M | DPO desde o MVP + auditorias trimestrais. |
| 40 | **Custo regulatório**: R$ 200-400k ANVISA sem garantia. | M | M | M | Decisão faseada após tração. |
| 41 | **Custo de ISO 13485**: R$ 300-500k. | M | M | M | Decisão faseada. |
| 42 | **Suicídio**: paciente em crise durante uso do app. | B | A | A | Detecção + redirecionamento CVV + equipe. |
| 43 | **Litígio**: paciente processa por evento adverso. | B | A | M | Seguro de responsabilidade civil + termos claros. |
| 44 | **Pressão dos investidores por growth**: sacrifica ciência. | M | A | M | Contratos com cláusulas de proteção ética. |
| 45 | **Recrutamento de equipe multidisciplinar de elite**: difícil em Brasil. | A | M | M | Stock options generosas + missão clara. |
| 46 | **Captable inflada**: fundadores perdem controle. | M | A | M | Rodadas disciplinadas; pool limitado a 10-15%. |
| 47 | **Aquisição por Big Tech que mata a tese**: Google/Apple compram e canibalizam. | B | M | M | Manter independência; recusar offers hostis. |
| 48 | **Open source de respiração**: protocolo vira commodity. | M | B | M | Marca + evidência + curadoria brasileira. |

### Médios (ação em 6-12 meses)

| # | Risco | P | I | U | Mitigação |
|---|-------|---|---|---|-----------|
| 49 | **Médicos prescritores viram "blogueiros" vendendo AraFlow**. | M | B | M | Compliance de marketing médico (CFM 2.336). |
| 50 | **Influencers vendem治愈**: promessas falsas. | M | M | M | Compliance + moderação de conteúdo. |
| 51 | **Reclame Aqui viraliza**: NPS negativo em massa. | M | M | M | Suporte humano de qualidade + monitoramento. |
| 52 | **Paciente fica "dependente" do app**: uso excessivo. | M | B | M | Limite diário + alerta de uso. |
| 53 | **App store rejeita por claim de saúde**. | B | M | M | Compliance editorial (Apple Guideline 1.4, Google). |
| 54 | **Concorrente nacional cresce com VC local**. | M | M | M | Defensibilidade técnica via pesquisa clínica. |
| 55 | **SUS incorpora app similar**: público migra. | B | M | M | Posicionamento premium + cannabis. |
| 56 | **Investidor quer IA em tudo**: sacrifica ciência por hype. | M | M | M | Compromissos contratuais explícitos. |
| 57 | **Freemium tem 99% grátis, 1% paga**: unit economics não fecha. | A | M | M | Estudar benchmark antes de fixar preços. |
| 58 | **Onboarding longo (>3 telas)**: drop-off de 70%+. | A | M | M | Redesenhar para 2 telas + escalas após 1ª sessão. |
| 59 | **Compliance de cannabis medicinal**: AraFlow atrai fiscalização. | M | M | M | Compliance reforçado + Due diligence ANVISA. |
| 60 | **Custo de pesquisa clínica sobe com inflação**. | M | M | M | Lock-in de contratos com CROs. |
| 61 | **Mídia expõe "cura digital"**: backlash público. | B | A | M | Compliance editorial rigoroso. |
| 62 | **Pacientes sem smartphone**: exclusão digital. | A | B | M | Versão para telefone básico (parceria com operadora). |
| 63 | **TDAH em adultos**: protocolo pode não funcionar. | M | M | M | Pesquisa específica + adaptação. |
| 64 | **TEA adulto**: protocolo pode ser aversivo. | M | M | M | Adaptação sensorial + pesquisa. |
| 65 | **Gestantes**: médico não prescreve por cautela. | M | M | M | Estudos específicos em obstetrícia. |
| 66 | **Idosos**: usabilidade cai drasticamente. | A | M | M | UX simplificada + testes com 60+. |
| 67 | **População LGBTQ+**: app não é inclusivo. | M | B | M | Pesquisa de UX com a comunidade. |
| 68 | **Pacientes em surto psicótico**: app não detecta, app piora. | B | A | M | Triagem + bloqueio de uso + encaminhamento. |
| 69 | **Marketing em escolas**: antiético + regulatório. | M | M | M | Política de não-marketing para <18. |
| 70 | **Hospital público sem internet**: piloto falha. | M | M | M | Versão offline robusta. |
| 71 | **Enfermagem sobrecarregada**: não adota. | A | M | M | Treinamento + simplicidade radical. |
| 72 | **Médicos com burn-out próprio**: céticos. | M | M | M | Marketing empático + ciência. |
| 73 | **Médicos com barreiras tecnológicas**: baixa adoção. | A | M | M | Interface WhatsApp + voz. |
| 74 | **Mindfulness puro sem respiração**: paciente prefere. | M | B | M | Oferecer ambos no MVP. |
| 75 | **App nativo iOS melhor que Android**: metade do mercado. | M | B | M | Paridade rigorosa iOS/Android. |
| 76 | **iOS 19 muda APIs de saúde**: quebra integração. | M | M | M | Abstração + testes de regressão. |
| 77 | **Wearables da Samsung incompatíveis**: falha UX. | M | B | M | Suporte progressivo. |
| 78 | **Custo de SMS/WhatsApp Business API**: alto. | M | M | M | Acordos com operadores. |
| 79 | **Latência de notificação**: paciente em crise não recebe alerta. | M | A | M | Testes de stress + fallback. |
| 80 | **Pesquisador brasileiro publica estudo negativo**: reputação. | M | A | M | Transparência; publicar negativos também. |
| 81 | **Trial clínico mal desenhado**: FDA rejeita. | B | A | M | Consultoria FDA em desenho + Pre-Submission. |
| 82 | **Endpoint substituto inadequado**: FDA rejeita. | B | A | M | Discussão com FDA pre-submission. |
| 83 | **Cartilha de cannabis medicinal muda**: framework regulatório. | M | M | M | Acompanhar ANVISA + ANPD + CFM. |
| 84 | **Plantão 24h de profissional**: custo operacional. | A | M | M | Modelo híbrido (bot + humano). |
| 85 | **Manual de uso para profissionais**: ninguém lê. | A | M | M | Treinamento presencial + certificação. |
| 86 | **Telemedicina tem regulamentação específica**: portaria muda. | M | M | M | Monitorar CFM + ANVISA. |
| 87 | **Custo de Cloud escalando**: burn rate explode. | M | M | M | Cost monitoring + alçadas de aprovação. |
| 88 | **Servidor brasileiro vs gringo**: dado sensível fora do país. | M | M | M | Servidor no Brasil (LGPD). |
| 89 | **Dependência de API de IA externa (OpenAI)**: custo variável. | A | M | M | Plano de modelos próprios + fallback. |
| 90 | **Modelo de IA com viés**: respostas ruins para minorias. | M | A | M | Auditoria de viés contínua. |
| 91 | **Teste A/B mal feito**: decisão errada de UX. | M | M | M | Estatística robusta + revisão. |
| 92 | **Analytics tracking excessivo**: LGPD multa. | M | A | M | Privacy by design + opt-in granular. |
| 93 | **Decisão de não investir em MDR**: limitação futura. | M | B | M | Decisão faseada + reavaliação em 2030. |
| 94 | **Founder burnout**: equipe chave sai. | M | A | M | Stock options + plano de sucessão. |
| 95 | **Captable complexa**: rodada futura dilui fundadores. | M | M | M | Pool limitado + advisor shares definidos. |
| 96 | **Equity grant para equipe sênior**: dilution excessiva. | M | M | M | Política de grants disciplinada. |
| 97 | **Mercado brasileiro de healthtech é pequeno**: TAM limitado. | M | M | M | Foco B2B alto valor + LATAM futuro. |
| 98 | **Inflação brasileira**: equipe custa mais por ano. | M | M | M | Política salarial indexada. |
| 99 | **Risco cambial**: investimento em USD, receita em BRL. | M | M | M | Hedge cambial parcial. |
| 100 | **Concorrente internacional lança versão PT-BR com marca local**. | M | A | M | Defensibilidade via AraOS + cannabis + clínica. |

---

## 4. TOP 100 Oportunidades

> *O que a equipe não enxerga — ou enxerga mal.*

### Mercado e posicionamento

| # | Oportunidade | Por quê |
|---|--------------|---------|
| 1 | **SUS como cliente**: integrar AraFlow à atenção primária do SUS (75M+ potenciais usuários). | Mercado gigante com orçamento público. |
| 2 | **Programa corporativo B2B único**: foco em saúde ocupacional reduz CAC, aumenta LTV. | ROI direto para empregador. |
| 3 | **B2B2C via plano de saúde**: planos oferecendo AraFlow como benefício diferenciado. | Mais palatável que reembolso direto. |
| 4 | **Onboarding em consultório**: médico prescreve e paciente baixa ali mesmo. | Conversão altíssima. |
| 5 | **Versão offline para hospitais públicos** com internet limitada. | Mercado SUS acessível. |
| 6 | **Versão para escola**: programa de saúde mental adolescente (com cuidado). | Mercado bilionário global. |
| 7 | **Versão para terceira idade**: apps são hostis a 60+; quem fizer bem ganha mercado subexplorado. | Envelhecimento populacional. |
| 8 | **Versão para presidiários**: saúde mental em sistema prisional é mercado governamental real. | Programa nacional. |
| 9 | **Versão para militares / policiais**: alto estresse ocupacional. | Orçamento federal garantido. |
| 10 | **Mercado veterinário de cães**: HRV canino para manejo de estresse. | Nicho curioso mas real. |

### Clínico (novas indicações)

| # | Oportunidade | Por quê |
|---|--------------|---------|
| 11 | **Coorte brasileira de longo prazo**: não existe coorte robusta de saúde mental digital brasileira. | Quem fizer primeiro publica. |
| 12 | **Validação clínica de cannabis medicinal + respiração**: tema pioneiro mundial. | Diferenciação global. |
| 13 | **HRV como biomarcador regulatório ANVISA**: ser o primeiro a validar HRV como desfecho reconhecido. | Marca pioneira. |
| 14 | **Pesquisa em mulheres / minorias**: dados desagregados por sexo, raça, classe. | Inclusão + publicação. |
| 15 | **Adolescentes com ansiedade escolar**: coorte específica. | Mercado escolar. |
| 16 | **Manejo de asma em adulto jovem**: parceria com pneumologista. | Doença respiratória tem evidência clara. |
| 17 | **DPOC**: programa de reabilitação respiratória com biofeedback. | Doença respiratória crônica. |
| 18 | **Reabilitação pós-AVC**: fonoaudiologia + respiração. | Indicação clínica clara. |
| 19 | **Parkinson**: distúrbios respiratórios do sono. | Indicação neurológica. |
| 20 | **Alzheimer**: regulação autonômica em declínio cognitivo. | Indicação neurológica. |
| 21 | **TEA adulto**: mercado subatendido. | População adulta TEA. |
| 22 | **TDAH adulto**: mercado em explosão. | População adulta TDAH. |
| 23 | **Lúpus, fibromialgia, Sjögren**: doenças autoimunes com fadiga e dor. | Bem mapeadas para AraFlow. |
| 24 | **Oncologia**: ansiedade pré-quimio, fadiga. | Suporte integrado. |
| 25 | **Cardiologia**: reabilitação cardíaca é mercado de R$ 1B+ no Brasil. | Indicação clínica robusta. |
| 26 | **Endocrinologia**: diabetes com componente emocional. | Adjuvante. |
| 27 | **Insuficiência cardíaca**: programa de autogestão. | Indicação clínica. |
| 28 | **Hipertensão**: manejo comportamental. | Adjuvante. |
| 29 | **Obesidade**: regulação autonômica + compulsão alimentar. | Mercado B2C imenso. |
| 30 | **Tabagismo**: cessação com respiração. | Indicação clínica clara. |
| 31 | **Álcool**: craving com respiração + mindfulness. | Indicação clínica. |
| 32 | **Jogo patológico**: regulação emocional. | Indicação nova. |
| 33 | **Compulsão por telas**: jovens. | Indicação emergente. |
| 34 | **Burnout em professores**: mercado educacional. | B2B claro. |
| 35 | **Burnout em profissionais de saúde**: irony mas mercado real. | Pós-pandemia. |
| 36 | **Burnout em cuidadores**: subexplorado. | Submercado. |
| 37 | **Estresse de imigrantes**: comunidade brasileira nos EUA. | Diaspora. |
| 38 | **Síndrome do impostor**: adultos jovens. | Indicação emergente. |
| 39 | **Ansiedade de performance em atletas**: esporte. | Performance atlética. |
| 40 | **Síndrome pré-menstrual e dismenorreia**: saúde feminina. | Mercado feminino. |
| 41 | **Menopausa**: ondas de calor + ansiedade. | Mercado feminino 50+. |
| 42 | **Infertilidade**: estresse do tratamento. | Submercado. |
| 43 | **Pós-parto**: depressão + ansiedade. | Indicação clínica clara. |
| 44 | **Puerpério**: suporte ao sono do bebê. | Submercado. |
| 45 | **Pais de crianças com TEA**: estresse parental. | Submercado. |
| 46 | **Cuidadores de idosos**: suporte. | Submercado. |
| 47 | **Doenças raras**: comunidade isolada + ansiedade. | Submercado. |
| 48 | **Reabilitação pós-COVID longa**: fadiga, dispneia, ansiedade. | Indicação emergente. |
| 49 | **Reabilitação pós-UTI**: TEPT pós-UTI é prevalente. | Indicação clínica. |
| 50 | **Reabilitação pós-cirurgia bariátrica**: suporte emocional. | Indicação clínica. |

### Tecnologia

| # | Oportunidade | Por quê |
|---|--------------|---------|
| 51 | **Voice biomarker**: análise de voz para detecção de humor. | Área em explosão. |
| 52 | **Computer vision facial**: detecção de fadiga por câmera. | Tecnologia emergente. |
| 53 | **Tato háptico respiratório**: pulseira que vibra no ritmo respiratório. | UX imersiva. |
| 54 | **Smart shirt**: tecido com sensor respiratório. | Wearable emergente. |
| 55 | **Máscara com sensor**: medição contínua. | Wearable emergente. |
| 56 | **Integração com Apple HealthKit**: ser o app referência em saúde respiratória. | Diferenciação técnica. |
| 57 | **Integração com Google Fit**: similar. | Mesma estratégia. |
| 58 | **Integração com Samsung Health**: similar. | Mesma estratégia. |
| 59 | **API aberta para pesquisadores**: posição única. | Posicionamento científico. |
| 60 | **Open source parcial de protocolos**: posição de liderança. | Liderança técnica. |
| 61 | **Plataforma de pesquisa clínica white label**: universidades. | Receita B2B nova. |
| 62 | **Pacote de dados anonimizados para pesquisas**: monetização secundária. | Receita adicional. |
| 63 | **Modelo de IA próprio**: diferencial técnico defensável. | IP defensável. |
| 64 | **Modelo de biofeedback personalizado**: diferencial técnico. | IP defensável. |
| 65 | **Algoritmo de detecção de crise**: patente. | IP defensável. |
| 66 | **Algoritmo de personalização de protocolo**: patente. | IP defensável. |
| 67 | **Painel para pesquisador**: ferramenta de análise. | Diferenciação. |
| 68 | **Painel para médico prescritor**: dashboard clínico. | Diferenciação. |
| 69 | **Painel para familiar/cuidador**: peace of mind. | Adesão. |
| 70 | **Painel para operadora**: ROI. | B2B. |
| 71 | **Painel para ANS/governo**: saúde populacional. | Governo. |
| 72 | **Integração com PEP nacional**: diferencial. | Diferenciação técnica. |
| 73 | **Versão para smartwatch dedicado**: Galaxy Watch, Apple Watch. | UX dedicada. |
| 74 | **Versão CarPlay/Android Auto**: sessão no trânsito. | UX diferenciada. |
| 75 | **Voice-first / Alexa / Google Home**: idosos + cegos. | Acessibilidade. |
| 76 | **Telemetria de wearables**: integração com 30+ dispositivos. | Cobertura. |
| 77 | **Gamificação suave**: streaks sem dependência. | UX positiva. |
| 78 | **Mensagens contextuais no WhatsApp**: distribuição B2C. | Canal brasileiro. |
| 79 | **Modo offline robusto**: SUS. | Mercado público. |
| 80 | **Sync via Bluetooth com estetoscópio digital**: clínicos. | Diferenciação técnica. |

### Parcerias e canais

| # | Oportunidade | Por quê |
|---|--------------|---------|
| 81 | **Parceria com Cruz Vermelha**: programa de saúde mental em desastres. | Mercado humanitário. |
| 82 | **Parceria com Defesa Civil**: TEPT pós-desastre. | Mercado governamental. |
| 83 | **Parceria com Igreja**: saúde mental em comunidade religiosa (com cuidado). | Mercado subexplorado. |
| 84 | **Parceria com sindicatos**: saúde do trabalhador. | B2B claro. |
| 85 | **Parceria com confederações esportivas**: atletas. | Esporte. |
| 86 | **Parceria com OAB**: saúde mental de advogados. | Mercado profissional. |
| 87 | **Parceria com CRM**: educação médica. | Adoção médica. |
| 88 | **Parceria com CFF**: farmacêuticos como ponto de cuidado. | Canal. |
| 89 | **Parceria com fenacor / corretores de seguros**: canal B2B. | Canal. |
| 90 | **Parceria com varejo farmacêutico**: Drogaria Onofre, Pacheco, Pague Menos. | Canal B2C. |
| 91 | **Parceria com academias de ginástica**: complemento. | Canal. |
| 92 | **Parceria com apps de nutrição**: ecossistema. | Canal. |
| 93 | **Parceria com apps de ciclo menstrual**: público feminino. | Canal. |
| 94 | **Parceria com apps de gravidez**: gestantes. | Canal. |
| 95 | **Parceria com apps de pediatria**: mães. | Canal. |
| 96 | **Parceria com apps de sono**: complementar. | Canal. |
| 97 | **Parceria com apps de dor**: complementar. | Canal. |
| 98 | **Parceria com apps de diabetes**: complementar. | Canal. |
| 99 | **Co-marketing com produtor de cannabis medicinal**: ecossistema AraOS. | Diferenciação. |
| 100 | **Marketplace de protocolos**: outros pesquisadores publicarem no AraFlow. | Plataforma aberta. |

---

## 5. TOP 50 Decisões a Revogar

> *Decisões tomadas que merecem ser revisitadas. Para cada: erro + alternativa + impacto.*

### Decisões arquiteturais

| # | Decisão atual | Por que erro | Alternativa melhor | Impacto positivo |
|---|---------------|--------------|---------------------|------------------|
| 1 | **Construir AraFlow como módulo separado do AraOS**. | Aumenta complexidade, dilui foco. | Começar como feature do AraOS; extrair AraFlow só se justificar. | Redução de 30% no escopo inicial. |
| 2 | **MVP com 9+ protocolos simultâneos**. | Sobrecarrega onboarding. | Lançar com 3 protocolos. Adicionar depois com base em uso. | Aumento de conversão de 40-60%. |
| 3 | **Suportar wearables no MVP**. | Custo de desenvolvimento alto, valor incerto. | Lançar só com câmera + microfone do celular. | Redução de 20% no time de desenvolvimento. |
| 4 | **Customização de avatar no MVP**. | Distrai do valor principal. | Avatar fixo + nome customizável. | Redução de 15% no escopo de design. |
| 5 | **Animações complexas em três níveis**. | Custo de design + dev, sem dado de que melhora adesão. | Animação única bem polida. | Redução de 30% no tempo de design. |
| 6 | **Onboarding com 7 telas + escalas clínicas**. | Conversão cai drasticamente. | Onboarding com 3 telas; escalas após 1ª sessão. | Aumento de retenção de 50%+. |
| 7 | **Documentação em 32 arquivos**. | Sinal de overplanning. | Documentação lean + decisões em ferramentas ágeis. | Aumento de velocidade de execução. |
| 8 | **Versão web do app no MVP**. | Custo alto, mercado secundário. | Mobile-first; web só em Fase 3. | Foco de recursos. |
| 9 | **Telemetria detalhada por padrão**. | LGPD art. 11. | Opt-in granular desde o MVP. | Compliance desde dia 1. |
| 10 | **Suporte a landscape e iPad otimizado**. | Saúde é vertical. | Foco em iPhone/Android portrait. | Foco de recursos. |

### Decisões de modelo de negócio

| # | Decisão atual | Por que erro | Alternativa melhor | Impacto positivo |
|---|---------------|--------------|---------------------|------------------|
| 11 | **12 modelos de negócio analisados em paralelo**. | Sem foco. | B2B-Pro + B2B-Corporate apenas no MVP. | Foco de vendas. |
| 12 | **B2C freemium como pilar**. | Unit economics desfavorável. | B2B-first; B2C como derivado. | LTV unitário sustentável. |
| 13 | **B2B-Corporate + B2B-Enterprise + B2B-University + B2B-Research simultâneo**. | Força de vendas sobrecarregada. | Uma persona de cada vez. | Eficiência de vendas. |
| 14 | **White Label como prioridade**. | Dilui marca AraFlow. | AraFlow marca única. | Brand equity preservado. |
| 15 | **R$ 29,90/mês como preço B2C**. | Competição com Calm (R$ 35/mês) com marca fraca. | R$ 14,90/mês ou gratuito + B2B subsidiando. | Conversão de 3-5x maior. |
| 16 | **R$ 79-199/mês B2B-Pro**. | Médicos têm baixa disposição a pagar. | R$ 29,90/mês + modelo per-seat. | Adoção ampliada. |
| 17 | **R$ 25-50/usuário/mês Enterprise**. | Complexidade de venda. | R$ 10-20/usuário/mês em contrato anual. | Sales cycle menor. |
| 18 | **Pay-per-use como opção**. | Modelo desalinhado com saúde. | Só assinatura. | Previsibilidade de receita. |
| 19 | **Marketplace de protocolos**. | Distância do core. | Fechado no MVP. | Foco. |
| 20 | **Acreditar que planos de saúde reembolsarão**. | Mercado não está pronto. | Não basear tese em reembolso. | Tese defensável. |

### Decisões clínicas

| # | Decisão atual | Por que erro | Alternativa melhor | Impacto positivo |
|---|---------------|--------------|---------------------|------------------|
| 21 | **Manter Nadi Shodhana com evidência C**. | Risco regulatório futuro. | Remover até ter evidência B. | Redução de risco regulatório. |
| 22 | **Manter Box 4-4-4-4 sem meta-análise específica**. | Defesa regulatória fraca. | Adicionar meta-análise antes de submeter ANVISA. | Robustez regulatória. |
| 23 | **Wim Hof como protocolo**. | Risco desproporcional. | Excluir; trilha avançada separada. | Redução de risco de evento adverso. |
| 24 | **Não incluir 4-7-8 com screening obrigatório**. | Risco cardiovascular. | Adicionar triagem. | Segurança clínica. |
| 25 | **Manter Buteyko no MVP**. | Indicação é asma (nicho). | Remover; parceria específica. | Foco de escopo. |
| 26 | **Documentar cannabis medicinal sem evidência específica**. | Reclamações regulatórias. | Adiar claims até pesquisa. | Compliance. |
| 27 | **Citar HeartMath como origem sem ressalva**. | Conflito de interesse. | Citar com neutralidade. | Integridade científica. |
| 28 | **"Substitui meditação"** em algum lugar. | Antiético. | Garantir que toda copy diga "complementa". | Compliance ético. |
| 29 | **Permitir personalização livre de tempo respiratório**. | Risco de hiperventilação. | Limites hard + alerta. | Segurança. |
| 30 | **Incluir populações vulneráveis no MVP**. | Risco ético + regulatório. | Validar primeiro em adultos. | Redução de risco. |

### Decisões regulatórias

| # | Decisão atual | Por que erro | Alternativa melhor | Impacto positivo |
|---|---------------|--------------|---------------------|------------------|
| 31 | **Tentar wellness E SaMD simultaneamente**. | Confusão regulatória. | Escolher um; documentar transição. | Clareza regulatória. |
| 32 | **Mirar FDA + MDR + ANVISA simultaneamente**. | Recursos esgotados. | ANVISA apenas no MVP. | Foco de recursos. |
| 33 | **Não contratar DPO desde o MVP**. | Multas LGPD. | DPO dedicado desde dia 1. | Compliance. |
| 34 | **Acreditar que wellness escapa de regulação**. | ANVISA está apertando. | Documentar limites. | Compliance. |
| 35 | **Não discutir cibersegurança com profundidade**. | Vazamento = morte da empresa. | Pentest externo + threat model. | Segurança. |

### Decisões de produto

| # | Decisão atual | Por que erro | Alternativa melhor | Impacto positivo |
|---|---------------|--------------|---------------------|------------------|
| 36 | **Voice journal no MVP**. | NLP + privacidade complexos. | Remover para Fase 2. | Foco de escopo. |
| 37 | **Detecção facial no MVP**. | Viés + privacidade. | Remover. | Foco de escopo. |
| 38 | **Avatar customizado 3D**. | Custo + distância de valor. | Foto estática ou ilustração fixa. | Foco de escopo. |
| 39 | **Sistema de pontos XP complexo**. | Pode gerar uso excessivo. | Streak simples + opt-in. | UX saudável. |
| 40 | **Notificações push intrusivas**. | Afasta pacientes. | Limite + opt-in estrito. | Retenção. |
| 41 | **Suportar 3 idiomas no MVP**. | Custo de localização. | PT-BR apenas. | Foco. |
| 42 | **Telemetria detalhada por padrão**. | LGPD. | Opt-in granular. | Compliance. |

### Decisões de equipe

| # | Decisão atual | Por que erro | Alternativa melhor | Impacto positivo |
|---|---------------|--------------|---------------------|------------------|
| 43 | **Neurocientista em tempo integral**. | Caro e raro. | Consultor + comissão. | Redução de custo fixo. |
| 44 | **Estatístico clínico em tempo integral**. | Subutilizado no MVP. | CRO parceiro. | Redução de custo fixo. |
| 45 | **Médico do sono em tempo integral**. | Sobreposição. | Compartilhar com AraOS. | Redução de custo fixo. |
| 46 | **Equipe de pesquisa clínica interna**. | Custo fixo alto. | Universidade parceira. | Redução de custo fixo. |
| 47 | **Board multidisciplinar de 10+ pessoas**. | Lento. | 5 pessoas com peso real. | Velocidade de decisão. |

### Decisões de marketing

| # | Decisão atual | Por que erro | Alternativa melhor | Impacto positivo |
|---|---------------|--------------|---------------------|------------------|
| 48 | **Manifesto literário no site**. | Marketing B2B não compra manifesto. | Versão técnica + emocional. | Conversão B2B. |
| 49 | **Comparação agressiva com Headspace/Calm**. | Distrai do próprio valor. | Comparação em white paper técnico. | Foco. |
| 50 | **Prometer "resultado mensurável" sem pesquisa**. | Reclamações. | Garantir 1 RCT antes de claim. | Compliance. |

---

## 6. TOP 50 Funcionalidades a Remover

> *Funcionalidades que agregam complexidade sem retorno claro.*

### Visual e UX

| # | Funcionalidade | Justificativa técnica |
|---|----------------|-----------------------|
| 1 | **Custom avatar 3D** | Custo de design e render; sem evidência de que avatar melhora adesão. |
| 2 | **Animações em 3 níveis de detalhe** | Custo de produção sem ganho mensurável. |
| 3 | **Microinterações em cada toque** | Ruim para acessibilidade; distrai. |
| 4 | **Modo escuro customizável** | Tema fixo basta. |
| 5 | **Suporte a landscape** | Saúde é vertical. |
| 6 | **Splash screen longa** | Atrito. |
| 7 | **Customização de cores** | Identidade de marca é fixa. |
| 8 | **Tutorial animado longo** | Usuário de saúde quer começar logo. |

### Produto

| # | Funcionalidade | Justificativa técnica |
|---|----------------|-----------------------|
| 9 | **Voice journal no MVP** | NLP, privacidade, custo. |
| 10 | **Detecção facial de humor** | Viés, privacidade, LGPD. |
| 11 | **Detecção de postura por câmera** | Precisão baixa, custo de bateria. |
| 12 | **Questionários adaptativos complexos** | Complexidade desnecessária. |
| 13 | **Gamificação XP / níveis** | Pode gerar uso excessivo. |
| 14 | **Sistema de conquistas** | Distrai do objetivo. |
| 15 | **Leaderboard social** | Saúde mental não é competição. |
| 16 | **Compartilhamento social** | Vazamento de dado sensível. |
| 17 | **Chat com IA no MVP** | Custo + risco de alucinação. |
| 18 | **Comunidade de usuários** | Custo de moderação + risco. |
| 19 | **Marketplace de conteúdo** | Distância de core. |
| 20 | **Loja de avatares** | Antiético em saúde. |

### Clínico

| # | Funcionalidade | Justificativa técnica |
|---|----------------|-----------------------|
| 21 | **12+ protocolos no MVP** | Sobrecarrega. |
| 22 | **Wim Hof como protocolo acessível** | Risco elevado. |
| 23 | **Tummo (avançado)** | Sem evidência para novatos. |
| 24 | **Modo SOS de 30 segundos** | Crise requer humano, não app. |
| 25 | **Avaliação de risco automática por IA** | Substitui profissional; risco. |
| 26 | **Sugestão automática de protocolo** | Profissional deve prescrever. |
| 27 | **Detecção de ideação suicida** | Muito sensível; requer profissional. |
| 28 | **Auto-ajuste de dose baseado em IA** | Antiético sem supervisão. |

### Técnico

| # | Funcionalidade | Justificativa técnica |
|---|----------------|-----------------------|
| 29 | **Suporte a 30+ wearables no MVP** | Custo de manutenção. |
| 30 | **Telemetria detalhada** | LGPD. |
| 31 | **Múltiplos temas de UI** | Marca fixa. |
| 32 | **Suporte offline robusto** | Custo de manutenção. |
| 33 | **Integração com calendário nativo** | Privacy. |
| 34 | **Integração com contatos** | Privacy. |
| 35 | **Push notifications personalizadas por IA** | Risco de uso excessivo. |
| 36 | **Versionamento de protocolo no MVP** | Complexidade prematura. |
| 37 | **Feature flags por usuário** | Complexidade prematura. |
| 38 | **Modo Picture-in-Picture** | Distrai. |
| 39 | **Widget para home screen** | Atrito visual. |
| 40 | **Suporte a Apple Pencil / S-Pen** | Overengineering. |

### Conteúdo

| # | Funcionalidade | Justificativa técnica |
|---|----------------|-----------------------|
| 41 | **Biblioteca de artigos de 100+ posts** | Custo editorial sem retorno claro. |
| 42 | **Podcasts no MVP** | Custo de produção. |
| 43 | **Webinars frequentes** | Recursos. |
| 44 | **Newsletter segmentada por 4 personas** | Complexidade. |
| 45 | **Conteúdo por idade** | Foco em adulto. |
| 46 | **Conteúdo por gênero** | Risco de estereotipar. |
| 47 | **Conteúdo religioso** | Antiético em app clínico. |
| 48 | **Conteúdo infantil** | Risco regulatório. |
| 49 | **E-commerce de produtos** | Distância de core. |
| 50 | **Programa de afiliados** | Compliance. |

---

## 7. TOP 50 Funcionalidades Ausentes

> *O que está faltando — e que deveria existir.*

### Clínico

| # | Funcionalidade | Por que é importante |
|---|----------------|----------------------|
| 1 | **Painel para médico prescritor**: lista de pacientes, adesão, desfechos. | Sem isso, profissional não prescreve. |
| 2 | **Exportação de relatório em PDF** para prontuário. | Integração clínica. |
| 3 | **Triagem clínica validada** (PHQ-9, GAD-7, ISI) com flag de risco. | Segurança. |
| 4 | **Red flag automático** para ideação suicida. | Segurança. |
| 5 | **Botão de pânico** que conecta a CVV ou SAMU. | Segurança. |
| 6 | **Integração com prescrição eletrônica** do AraOS. | Operacional. |
| 7 | **Avaliação de efeitos adversos** pós-sessão. | Segurança. |
| 8 | **Algoritmo de estratificação de risco**. | Personalização segura. |
| 9 | **Programa de titulação** (começa devagar, sobe dose). | Segurança em protocolos intensos. |
| 10 | **Modo de uso mínimo** para iniciantes (10 min/dia). | Acessibilidade. |

### Técnico

| # | Funcionalidade | Por que é importante |
|---|----------------|----------------------|
| 11 | **Acessibilidade AA/AAA**: contraste, leitor de tela, tamanho de fonte. | Inclusão + legislação. |
| 12 | **VoiceOver / TalkBack nativo**. | Acessibilidade. |
| 13 | **Modo de uso com baixo pacote de dados**. | SUS + 4G fraco. |
| 14 | **Sincronização offline + retry**. | Hospitais com internet instável. |
| 15 | **Autenticação de dois fatores obrigatória**. | Segurança. |
| 16 | **Biometria para login** (Face ID, digital). | UX + segurança. |
| 17 | **Logs de auditoria** (quem acessou o quê). | LGPD + clínico. |
| 18 | **Exportação de dados do paciente** (LGPD art. 18). | Compliance. |
| 19 | **Exclusão de conta** com confirmação + soft delete + hard delete após 30 dias. | LGPD. |
| 20 | **Política de retenção** clara por tipo de dado. | LGPD. |
| 21 | **Telemetria opt-in** com granularidade. | LGPD. |
| 22 | **Criptografia em repouso** (AES-256). | LGPD. |
| 23 | **Criptografia em trânsito** (TLS 1.3). | LGPD. |
| 24 | **Backups criptografados** com rotação de chaves. | LGPD. |
| 25 | **Plano de disaster recovery** documentado. | LGPD + operacional. |
| 26 | **Pareamento com Apple Health / Google Fit** real. | UX. |
| 27 | **Suporte a WHOOP, Garmin, Polar, Apple Watch, Fitbit, Oura, Samsung**. | UX. |
| 28 | **Métrica de HRV** específica e exibida ao usuário. | Diferencial. |
| 29 | **Modo "sessão rápida"** (3 min, 5 min, 10 min). | Aderência. |
| 30 | **Sessão offline salva local**. | UX. |

### Produto

| # | Funcionalidade | Por que é importante |
|---|----------------|----------------------|
| 31 | **Lembrete personalizado** baseado em agenda. | Aderência. |
| 32 | **Ritual de "antes de dormir"** automático. | UX. |
| 33 | **Integração com alarme do celular**. | UX. |
| 34 | **Respiração com vibração** em smartwatch. | UX. |
| 35 | **Modo família** com até 4 perfis. | Aderência familiar. |
| 36 | **Compartilhamento com familiar/cuidador** opt-in. | Adesão. |
| 37 | **Onboarding em vídeo de 60s**. | Conversão. |
| 38 | **FAQ dentro do app**. | Suporte. |
| 39 | **Botão de feedback rápido** pós-sessão. | UX. |
| 40 | **Modo "dúvida rápida"** para esclarecimento. | UX. |

### Operacional

| # | Funcionalidade | Por que é importante |
|---|----------------|----------------------|
| 41 | **Painel de运营 para AraFlow ops**: NPS, churn, adesão. | Decisão. |
| 42 | **Customer success playbook** documentado. | B2B. |
| 43 | **Suporte via WhatsApp Business** com SLA. | B2B. |
| 44 | **FAQ em vídeo** para prescritores. | Adoção. |
| 45 | **Programa de ambassador** médico. | Marketing. |
| 46 | **Comunidade de prática** para prescritores (fechada). | Adoção. |
| 47 | **Newsletter semanal** para prescritores. | Adoção. |
| 48 | **Calculadora de ROI** para hospitais. | B2B. |
| 49 | **Calculadora de ROI** para operadoras. | B2B. |
| 50 | **Case studies** com métricas reais. | Marketing. |

---

## 8. O que cada empresa faria diferente

### Apple Health

> *Visão de um Product Lead Apple Health.*

1. **Restrição brutal de features**: 3 protocolos, animações mínimas, foco obsessivo em uma única coisa que funciona perfeitamente.
2. **Onboarding em 90 segundos**, sem escalas clínicas.
3. **HealthKit como pilar**: AraFlow como app complementar, não plataforma independente.
4. **Privacidade como marketing**: "o que acontece no AraFlow fica no iPhone" como headline.
5. **Sessões curtas como default**: 5 min, não 20.
6. **Sem comunidade, sem social**: foco em uso individual silencioso.
7. **Pesquisa mínima publicada com dados reais**: 1 paper, não 5.
8. **Integração com Apple Watch como vantagem técnica**: HRV, frequência respiratória.
9. **Sem conteúdo longo**: biblioteca mínima, curada.
10. **Sem B2B no MVP**: focar no consumidor final primeiro.

### Headspace

> *Visão de UX Director Headspace.*

1. **Conteúdo como pilar**: 1.000+ sessões guiadas com vozes diferentes.
2. **Marca emocional forte**: o app tem personalidade, não é "ferramenta".
3. **Onboarding leve, sem jargão**: "como você está se sentindo?" em vez de "escala PHQ-9".
4. **Personas múltiplas**: para ansioso, para dormidor, para atleta.
5. **Foco em meditação + mindfulness**, não em respiração técnica.
6. **Sessões de 10 min**: aderir é mais importante que aprofundar.
7. **Conteúdo para crianças** com personagens (até 12 anos com supervisão).
8. **Programa "Wake Up" diário** com áudio curto: ~5 min.
9. **Coach humano** como upsell.
10. **Marca colaborativa**: personagens conhecidos, séries originais.

### Calm

> *Visão de UX Director Calm.*

1. **Sleep stories como assinatura**: voz calma conta histórias.
2. **Visual cinematográfico**: paisagens, natureza.
3. **Música original** licenciada.
4. **Premium positioning**: R$ 50/mês, não R$ 30.
5. **Conteúdo diário novo**: pressão de retenção.
6. **Integração com Apple Watch, mas opcional**.
7. **Foco em bedtime**: sono como categoria principal.
8. **Daily Calm de 10 min** com novo tema todo dia.
9. **Masterclasses com especialistas famosos**.
10. **Programa "Calm Health"** como extensão clínica.

### Breathwrk

> *Visão de UX Director Breathwrk.*

1. **Foco obsessivo em respiração**: a palavra "meditação" não aparece.
2. **Animações centrais**: a respiração visual é o produto, não decoração.
3. **Coach em vídeo**: rosto humano que conduz.
4. **Exercícios nomeados e memoráveis**: "Respire Like This", "Power Breath".
5. **Comunidade de streak**: 30 dias, 100 dias.
6. **Programa "Today's Breath"** diário com novo padrão.
7. **Performance e energia**: "para te dar mais energia", não "reduzir ansiedade".
8. **Integração com Apple Watch** completa.
9. **Coach humano premium** ($200/mês).
10. **Conteúdo curto e didático**: 3-5 min máximo.

### Whoop

> *Visão de Product Lead Whoop.*

1. **Wearables como core**, não como acessório.
2. **HRV como métrica principal**, exibida em tempo real.
3. **Strain, Recovery, Sleep** como framework.
4. **Coaching humano + algoritmo** (não só algoritmo).
5. **Assinatura premium** com hardware incluso (ou vendido).
6. **Comunidade fechada** de usuários.
7. **Foco em performance atlética** antes de saúde geral.
8. **Dados do usuário como ativo** (anonimizados para pesquisa).
9. **Coach dedicado** para high-value users.
10. **Integração profunda** com HealthKit, Google Fit, Strava.

### Notion

> *Visão de Product Manager Notion.*

1. **Sistema modular**: cada bloco é independente, componível.
2. **Customização infinita**: poder do usuário.
3. **Templates**: começar é fácil.
4. **Sync em tempo real** entre dispositivos.
5. **Busca poderosa** por conteúdo e histórico.
6. **Versionamento** de protocolos.
7. **AI embutido** em todo lugar.
8. **Colaboração opcional**: compartilhar protocolo com profissional.
9. **API aberta** para desenvolvedores.
10. **Personalidade minimalista**: espaço em branco é produto.

### OpenAI

> *Visão de OpenAI.*

1. **Personalização por modelo de linguagem**: conversa natural.
2. **Memória contínua**: lembra do contexto emocional do usuário.
3. **Adaptação dinâmica**: protocolo muda conforme contexto.
4. **Multimodal**: texto + voz + imagem.
5. **Tool use**: integra com outros sistemas.
6. **Reasoning explícito**: explica por que sugeriu isso.
7. **Treinamento contínuo**: melhora com uso.
8. **Safety primeiro**: filtros de segurança robustos.
9. **Human in the loop** em decisões críticas.
10. **Open research**: publica papers.

### Microsoft (Health)

> *Visão de Microsoft Health.*

1. **Cloud-first**: Azure como backbone.
2. **Integração com Microsoft 365**: Outlook, Teams.
3. **Enterprise sales**: B2B estruturado.
4. **Compliance como pilar**: HIPAA, GDPR, LGPD.
5. **Power Platform**: extensibilidade para enterprise.
6. **Viva**: saúde dentro do Teams.
7. **Glueware**: integra com tudo que já existe.
8. **Documentação técnica** extensiva.
9. **Suporte 24/7** global.
10. **Trust**: marca corporativa responsável.

### Google Health

> *Visão de Google Health.*

1. **Search-first discovery**: SEO como canal.
2. **Fitbit integration**: wearable próprio.
3. **AI multimodal**: áudio, vídeo, texto.
4. **Health Connect**: padrão Android.
5. **Research collaborations**: com Stanford, Harvard.
6. **YouTube como canal de educação** em saúde.
7. **Open source**: contribuir para comunidade.
8. **Dados em escala**: modelo de dados único.
9. **Cloud Healthcare API**: integração com prontuários.
10. **Lens e Voice**: acessibilidade.

### Mayo Clinic

> *Visão de Mayo Clinic Digital.*

1. **Clínica primeiro**: tecnologia serve ao cuidado.
2. **Validação clínica em hospital próprio**: testar antes de lançar.
3. **Pubmed-indexed research**: publicar tudo.
4. **Paciente no centro**: jornada, não feature.
5. **Médicos como co-designers**: cada feature passa por clínico.
6. **Comitê ético**: toda feature revisada.
7. **Integração com Epic**: prontuário Mayo é Epic.
8. **Discharge planning**: alta inclui AraFlow.
9. **Continuidade de cuidado**: hospital → ambulatório → casa.
10. **Accountable care**: medimos desfecho real.

### Cleveland Clinic

> *Visão de Cleveland Clinic Innovations.*

1. **Innovation hub**: spin-offs internos.
2. **Validation studies**: RCTs próprios antes de qualquer claim.
3. **Clinical champions**: médicos embaixadores internos.
4. **Patient reported outcomes**: PROMs como métrica.
5. **Real-world evidence**: pós-mercado rigoroso.
6. **Multidisciplinary**: cada feature tem 5+ especialistas revisando.
7. **Health system integration**: EHR nativo.
8. **Population health**: foco em subgrupos.
9. **Equity**: acesso a populações desassistidas.
10. **Stewardship**: custo-efetividade documentada.

### Massachusetts General Hospital (MGH)

> *Visão de MGH Digital Health.*

1. **Academic rigor**: Harvard Medical School affiliated.
2. **Research-grade evidence**: cada feature tem paper.
3. **Clinical trial infrastructure**: MGH tem CRO interno.
4. **Specialty focus**: cada protocolo tem especialista revisor.
5. **Data science**: modelagem estatística rigorosa.
6. **Open data**: contribuições para ciência aberta.
7. **Bioethics**: revisão ética de cada feature.
8. **Pharma collaboration**: integrar com pesquisa clínica.
9. **Education**: treinar residentes e fellows.
10. **Global health**: pensar em escala global desde dia 1.

---

## 9. O que um Hospital Privado exigiria

> *Visão de Diretor Clínico + Diretor Financeiro Hospitalar.*

1. **Integração com PEP/HIS**: HL7 FHIR R4 obrigatório.
2. **Single Sign-On (SSO)** com LDAP/AD/SAML.
3. **Conformidade com LGPD + ANVISA + CFM**.
4. **Auditoria completa** com logs imutáveis.
5. **Suporte 24/7 com SLA** de 1h para crítico, 4h para alto.
6. **Documentação em português** com responsável técnico local.
7. **Treinamento presencial** da equipe (mínimo 4h).
8. **ROI demonstrado** com case studies publicados.
9. **Seguro de responsabilidade civil** com cobertura > R$ 5M.
10. **Plano de disaster recovery** com RPO < 4h, RTO < 24h.
11. **Compatibilidade com infraestrutura existente** (servidor on-premise? nuvem?).
12. **Customização limitada** (white label leve).
13. **Atualizações controladas** sem breaking changes.
14. **Compliance com acreditações** (ONA, JCI, HIMSS).
15. **Validação clínica em hospital** antes de escalar.
16. **Termo de consentimento integrado** com PEP.
17. **Gestão de identidade**: nome social, dados demográficos completos.
18. **Telemetria operacional** para BI hospitalar.
19. **Suporte a múltiplos idiomas** se hospital atende estrangeiros.
20. **Conformidade com CFM 2.314** (telemedicina).

---

## 10. O que uma Operadora de Saúde exigiria

> *Visão de Operadora de Plano de Saúde.*

1. **Estudos de custo-efetividade** próprios ou de parceiros acadêmicos.
2. **ROI demonstrável em 12 meses**: redução de sinistralidade, readmissões, consultas.
3. **Compliance com ANS**: cobertura suplementar.
4. **Integração com sistema de autorização** da operadora.
5. **Auditoria de uso**: quem usa, quanto, com quais desfechos.
6. **Relatórios padronizados**: mensais, trimestrais, anuais.
7. **Painel de gestão** para área de saúde populacional.
8. **LGPD compliance com DPA** (Data Processing Agreement).
9. **Sub-processadores listados**.
10. **Certificações**: ISO 27001, ISO 27701 desejável.
11. **Suporte a ANS TISS**: padrão de troca de informação.
12. **Modelo de pagamento flexível**: per capita, fee-for-service, compartilhamento de risco.
13. **Programa de doença**: psicossomática, dor crônica, ansiedade, burnout.
14. **Evidência clínica publicada**: ANS exige isso.
15. **Manual do beneficiário**: como acessar.
16. **Termo de consentimento integrado** com a operadora.
17. **Gestão de crise**: como lidar com paciente em surto.
18. **Indicadores de qualidade**: adesão, desfecho, satisfação.
19. **Capacidade de expansão** para toda a carteira.
20. **Roadmap claro** com marcos regulatórios.

---

## 11. O que a ANVISA questionaria

> *Visão de Especialista ANVISA + Farmacêutico.*

1. **Qual o enquadramento regulatório?** Software como dispositivo médico?
2. **Classe de risco?** I, II, III, IV conforme RDC 185/2001 e RDC 657/2022?
3. **Notificação ou registro?** Depende da classe.
4. **Quais indicações clínicas claims?**
5. **Quais evidências sustentam cada indicação?**
6. **Plano de gerenciamento de risco** (ISO 14971)?
7. **QMS implementado** (ISO 13485)?
8. **Processo de design e desenvolvimento** (IEC 62304)?
9. **Usabilidade** (IEC 62366)?
10. **Software de aplicação médica** (RDC 185/2001)?
11. **Software embarcado** (RDC 657/2022)?
12. **Rotulagem** conforme legislação.
13. **Instruções de uso**.
14. **Plano de pós-mercado**.
15. **Notificação de eventos adversos**.
16. **Recall process**.
17. **Responsável técnico** (farmacêutico ou engenheiro clínico).
18. **Comprovação de eficácia clínica**.
19. **Segurança e desempenho**.
20. **Interoperabilidade com outros sistemas**.
21. **Plano de gestão de mudanças**.
22. **Plano de cibersegurança**.
23. **Política de atualizações**.
24. **Compatibilidade declarada**.
25. **Restrições de uso**.

---

## 12. O que o FDA exigiria

> *Visão de Especialista FDA.*

1. **Software function**: o que ele faz exatamente?
2. **Disease state**: para qual doença?
3. **Risk to patient**: o que acontece se falhar?
4. **Predetermined change control plan**: como vai evoluir?
5. **SaMD category**: I, II, III, IV (per IMDRF)?
6. **510(k) pathway** vs. **De Novo** vs. **PMA**?
7. **Predicate device**: existe equivalente?
8. **Substantial equivalence**: como demonstrou?
9. **Clinical evidence**: qual o nível de evidência?
10. **Real-world evidence**: tem?
11. **Total product lifecycle**: como vai monitorar pós-mercado?
12. **Cybersecurity**: plano documentado (FDA Cybersecurity Guidance 2023).
13. **Interoperability**: HL7/FHIR?
14. **Labeling**: o que o usuário lê?
15. **Intended use**: claro?
16. **Indications for use**: específicas?
17. **Contraindications**: documentadas?
18. **Warnings**: documentadas?
19. **Adverse events reporting**: como (MedWatch)?
20. **Quality system**: 21 CFR Part 820 + ISO 13485.
21. **Design Controls**: 21 CFR 820.30.
22. **Software Lifecycle**: IEC 62304.
23. **Risk Management**: ISO 14971.
24. **Usability**: IEC 62366 + FDA HFE Guidance.
25. **Predicate Device Comparison**: detalhado.

---

## 13. O que impediria certificação como SaMD

> *Cenários onde a certificação não viria.*

1. **Não ter QMS ISO 13485 implementado antes do Design Freeze.**
2. **Não ter processo de Risk Management documentado (ISO 14971) desde o início do desenvolvimento.**
3. **Não ter processo de Software Lifecycle (IEC 62304) com SOUP catalogado.**
4. **Não ter Usabilidade (IEC 62366) documentada com testes formativos e somativos.**
5. **Não ter Clinical Evaluation Report (CER) atualizado continuamente.**
6. **Não ter Post-Market Surveillance (PMS) plan desde antes da submissão.**
7. **Não ter Indications for Use claras e específicas.**
8. **Não ter Intended Use Environment definido.**
9. **Não ter Beneficence/Risk Analysis favoravelmente documentada.**
10. **Não ter Cybersecurity documentation (FDA 2023 Guidance + IEC 81001-5-1).**
11. **Não ter Interoperability documentation.**
12. **Não ter Labeling conforme 21 CFR 801.**
13. **Não ter responsável técnico qualificado.**
14. **Não ter Clinical Evidence robusta: pelo menos 2 RCTs pivotais publicados.**
15. **Não ter Real-World Evidence planejada.**
16. **Não ter predições sobre pós-mercado (PMS/PMPF).**
17. **Não ter recall process documentado.**
18. **Não ter processo de notificação de eventos adversos.**
19. **Não ter gestão de供应链 qualificada (ISO 13485 cláusula 7).**
20. **Não ter processo de design controls (Design Input → Design Output → Verification → Validation → Transfer).**
21. **Não ter processo de CAPA (Corrective and Preventive Action).**
22. **Não ter Document Control robusto.**
23. **Não ter treinamento documentado de todos os envolvidos.**
24. **Não ter processo de gestão de mudanças (Change Control).**
25. **Não ter auditoria interna do QMS antes da auditoria regulatória.**

---

## 14. O que faria um Investidor desistir

> *Visão de Sócio Sequoia + a16z.*

1. **Tese ambiciosa demais** sem foco.
2. **Sem tração** (usuários, receita, retenção).
3. **Sem métrica de product-market fit**.
4. **Time sem experiência** em healthtech ou DTx.
5. **Fundadores únicos** sem co-founder técnico.
6. **Modelo de negócio confuso** (13 opções).
7. **Mercado saturado** (Headspace, Calm, Breathwrk, Sleepio).
8. **CAC estimado alto** sem LTV correspondente.
9. **Burn rate alto** sem clareza de quando acaba.
10. **Regulação cara** sem validação clínica prévia.
11. **Pesquisa clínica cara** sem funding garantido.
12. **Dependência de AraOS** (conflito potencial).
13. **Sem proteção IP** (patentes).
14. **Cap table bagunçada**.
15. **Sem advisor relevante** em saúde ou DTx.
16. **Marketing com promessas exageradas**.
17. **Ausência de exit strategy** clara.
18. **Mercado TAM inflado** sem justificativa.
19. **Risco Brasil** (cambial, regulatório, político).
20. **Equity round dilutiva** sem milestones.
21. **Burnout de founder**: sinais de esgotamento.
22. **Problemas pessoais de fundadores**.
23. **Conflito interno não resolvido**.
24. **Documentação inflada sem execução**: 30+ documentos sem MVP.
25. **Falta de clareza sobre cap table, vesting, advisors**.

---

## 15. O que faria um Médico nunca prescrever

> *Visão de Médico Prescritor + Psiquiatra.*

1. **Sem evidência clínica** publicada.
2. **Sem indicação clara** ("para quê?").
3. **Sem contraindicações claras** ("quando não?").
4. **Sem protocolo explícito** ("qual sessão para qual paciente?").
5. **Sem métrica de desfecho** ("como sei se está funcionando?").
6. **Sem integração com prontuário** ("como documento?").
7. **Sem dashboard de adesão** ("o paciente está usando?").
8. **Sem alertas de risco** ("ele teve ideação suicida?").
9. **Custo para o paciente** ("quanto custa?").
10. **Sem suporte ao paciente** ("e se ele tiver problema?").
11. **Sem selo de qualidade** ("é sério?").
12. **Sem comitê científico** visível.
13. **Sem revisão por pares** da literatura.
14. **Sem estudos clínicos brasileiros**.
15. **Marca desconhecida** ("nunca ouvi falar").
16. **App cheio de popups** e marketing.
17. **Sem disclaimer ético** ("isso não substitui terapia").
18. **Promessas exageradas** ("cura ansiedade").
19. **Sem rede de apoio** se paciente piorar.
20. **Falta de transparência** sobre dados.

---

## 16. O que faria um Paciente desinstalar

> *Visão de Pacientes (Ansiedade, Insônia, Dor, AH/SD, TEA).*

1. **Onboarding longo demais** (>2 min).
2. **Pedir dados sensíveis** sem explicação clara.
3. **Telas de escalas clínicas** no primeiro uso.
4. **Notificações excessivas**.
5. **Popups de avaliação de app** toda semana.
6. **Popups de upsell** constantes.
7. **Animações que travam** em celular antigo.
8. **Sem offline** quando precisa.
9. **Custo após trial** não comunicado.
10. **Não ver resultado** em 1 semana.
11. **Sentir que não entende** o que está fazendo.
12. **Receber notificação** durante crise.
13. **App pedir senha** com frequência.
14. **App travar** no meio de sessão.
15. **Não funcionar com fone bluetooth**.
16. **Não ter opção de 5 minutos**.
17. **Voz irritante**.
18. **Visual feio**.
19. **Letra pequena**.
20. **Idioma inglês** em parte do app.

---

## 17. Funcionalidades que parecem excelentes mas provavelmente nunca serão utilizadas

> *Features que parecem boas no papel mas têm baixo uso real.*

| # | Funcionalidade | Por que ninguém vai usar |
|---|----------------|---------------------------|
| 1 | **Avatar 3D customizado** | Usuário não personaliza, quer começar logo. |
| 2 | **Biblioteca de 100+ artigos** | Ninguém lê. |
| 3 | **Comunidade de usuários** | Custo de moderação + risco de mágoa entre pacientes. |
| 4 | **Marketplace de conteúdo** | Conteúdo de qualidade é caro; quantidade atrai medíocre. |
| 5 | **Sistema de pontos XP** | Pode gerar uso excessivo, não é mais saudável. |
| 6 | **Leaderboard social** | Saúde mental não é competição. |
| 7 | **Compartilhamento social** | Vazamento de dado sensível. |
| 8 | **Voice journal** | Falar em voz alta é constrangedor. |
| 9 | **Detecção facial de humor** | Viés + privacidade + bateria. |
| 10 | **Animações em 3 níveis** | Primeira animação já basta. |
| 11 | **Customização de cores** | Identidade de marca é fixa. |
| 12 | **Loja de avatares** | Antiético. |
| 13 | **Programa de afiliados** | Compliance + distração. |
| 14 | **Conteúdo infantil** | Risco regulatório. |
| 15 | **Modo SOS de 30 segundos** | Crise requer humano. |
| 16 | **Chat com IA no MVP** | Alucina; custo alto. |
| 17 | **E-commerce** | Distância de core. |
| 18 | **Telemetria detalhada** | LGPD art. 11. |
| 19 | **Versão web** | Saúde é mobile. |
| 20 | **Suporte a 30+ wearables** | Suporte real a 2-3 apenas. |

---

## 18. Funcionalidades de alto custo e baixo valor

> *Custo de manutenção e desenvolvimento alto; valor gerado incerto.*

| # | Funcionalidade | Custo estimado | Valor real |
|---|----------------|----------------|------------|
| 1 | **Custom avatar 3D** | R$ 200-400k | Baixo |
| 2 | **Animações em 3 níveis** | R$ 100-200k | Baixo |
| 3 | **Suporte a 30+ wearables** | R$ 500k-1M | Médio |
| 4 | **Voice journal com NLP** | R$ 300-600k | Médio |
| 5 | **Detecção facial de humor** | R$ 200-400k | Baixo |
| 6 | **Marketplace de conteúdo** | R$ 400-800k | Baixo |
| 7 | **Comunidade de usuários** | R$ 500k-1M (moderação) | Baixo |
| 8 | **Biblioteca de 100+ posts** | R$ 100-300k (editorial) | Médio |
| 9 | **Telemetria detalhada** | R$ 100-200k (compliance) | Baixo |
| 10 | **Versão web do app** | R$ 300-500k | Baixo |
| 11 | **Suporte a 3 idiomas** | R$ 200-400k | Baixo |
| 12 | **Integração com calendário nativo** | R$ 100-200k | Baixo |
| 13 | **Modo offline robusto** | R$ 200-400k | Médio |
| 14 | **Suporte a Apple Pencil** | R$ 50-100k | Baixo |
| 15 | **Widget para home screen** | R$ 50-100k | Baixo |
| 16 | **Modo Picture-in-Picture** | R$ 50-100k | Baixo |
| 17 | **Suporte a landscape** | R$ 100-200k | Baixo |
| 18 | **Customização de cores** | R$ 50-100k | Baixo |
| 19 | **Microinterações em cada toque** | R$ 200-400k | Baixo |
| 20 | **Splash screen longa animada** | R$ 50-100k | Baixo |

---

## 19. Funcionalidades que deveriam entrar imediatamente

> *Alto valor, baixo custo. MVP.*

| # | Funcionalidade | Por que é prioritária |
|---|----------------|----------------------|
| 1 | **Onboarding em 90 segundos, sem escalas clínicas** | Conversão. |
| 2 | **3 protocolos clínicos validados**: Diafragmática, Box 4-4-4-4, Coerência 5.5. | Foco. |
| 3 | **Sessões de 5, 10 e 15 minutos** | Adesão. |
| 4 | **Tracking de humor e energia (1-5) pré e pós** | Desfecho. |
| 5 | **Acessibilidade AA** | Inclusão. |
| 6 | **LGPD compliance com opt-in granular** | Compliance. |
| 7 | **Autenticação biométrica** (Face ID, digital) | UX + segurança. |
| 8 | **Logs de auditoria** | LGPD + clínico. |
| 9 | **Política de retenção** clara | LGPD. |
| 10 | **Exportação de dados do paciente** | LGPD art. 18. |
| 11 | **Exclusão de conta** completa | LGPD art. 18. |
| 12 | **FAQ dentro do app** | Suporte. |
| 13 | **Botão de feedback rápido** pós-sessão | UX. |
| 14 | **Lembrete diário** configurável | Aderência. |
| 15 | **Sessão offline salva local** | UX. |

---

## 20. Funcionalidades que deveriam ser adiadas para v2.0

> *Valor alto mas custo alto demais para o MVP.*

| # | Funcionalidade | Por que adiar |
|---|----------------|----------------|
| 1 | **Integração com wearables** (Apple Watch, Whoop, Garmin) | Custo de manutenção. |
| 2 | **HRV como métrica principal** | Requer hardware. |
| 3 | **IA multimodal** (texto, voz, vídeo) | Custo computacional. |
| 4 | **Voice journal com NLP** | Privacidade + custo. |
| 5 | **Detecção facial de humor** | Viés + privacidade. |
| 6 | **Comunidade de usuários** | Moderação cara. |
| 7 | **Marketplace de conteúdo** | Distância de core. |
| 8 | **Marketplace de protocolos** | Distância de core. |
| 9 | **White label** | Dilui marca. |
| 10 | **Telemedicina integrada** | CFM 2.314 + complexidade. |
| 11 | **Múltiplos idiomas** | Custo de localização. |
| 12 | **Integração com Apple Health/Google Fit** | Custo de manutenção de APIs. |
| 13 | **Programa de afiliados** | Compliance. |
| 14 | **E-commerce de produtos** | Distância de core. |
| 15 | **Modo offline robusto** | Custo de sincronização. |

---

## 21. O MVP está grande demais?

> # SIM.
>
> O MVP proposto é grande demais em pelo menos 5 dimensões.

### Dimensões onde está inflado

1. **Protocolos**: 9+ no MVP deveria ser 3.
2. **Funcionalidades**: ~80 features deveria ser ~20.
3. **Modelos de negócio**: 13 deveria ser 2.
4. **Wearables**: 0 deveria ser 0 (removido completamente).
5. **Conteúdo**: 100+ artigos deveria ser 0 (só depois da tração).
6. **Eixos de longo prazo**: 16 deveria ser 1 (foco).

### MVP enxuto proposto

#### Protocolos
- 3 protocolos apenas: Diafragmática Profunda, Box 4-4-4-4, Coerência 5.5.

#### Funcionalidades
- Onboarding em 90s.
- Sessões de 5, 10, 15 min.
- Tracking pré/pós de humor/energia (1-5).
- Streak simples (dias consecutivos).
- Lembrete diário configurável.
- LGPD: opt-in granular + exportação + exclusão.
- Acessibilidade AA.
- Autenticação biométrica.
- FAQ.
- Botão de feedback rápido.

#### Modelos de negócio
- B2C freemium (5 sessões grátis, depois paywall).
- B2B-Pro (assinatura mensal de médico para prescrever e acompanhar pacientes).

#### Stack
- iOS + Android nativo (paridade rigorosa).
- Backend único (Node + Postgres).
- Cloud AWS São Paulo (LGPD).
- Sem wearables.

#### Equipe
- 1 founder técnico.
- 1 designer UX/UI.
- 1 médico clínico (part-time).
- 1 CTO/backend.
- 2 devs mobile.
- 1 growth/ops.

#### Timeline
- 4 meses para MVP funcional.
- 2 meses para beta com 100 usuários.
- 6 meses para tração mínima (1.000 usuários ativos).

#### Budget
- R$ 1,5-2M para 12 meses.

---

## 22. Maior erro estratégico

> **A documentação propõe uma plataforma DTx integrada, prescritiva, regulada, com evidência clínica, integração hospitalar, marketplace de protocolos, comunidade de pacientes, IA multimodal, Digital Twin, suporte a wearables, white label e modelo B2B multi-canal — tudo em 10 anos, com equipe multidisciplinar, investimento de R$ 50M, sem tração prévia. Isso não é ambição; é falta de priorização. A tese real do AraFlow é simples: ajudar pessoas com ansiedade, insônia e dor a regular o sistema nervoso com respiração estruturada, prescrito por profissional, integrado ao AraOS, validado por evidência. Tudo o que não serve a esse núcleo deve ser cortado.**

---

## 23. Maior diferencial competitivo

> **A integração nativa com AraOS é o único ativo verdadeiramente defensável. Nenhum competidor global (Headspace, Calm, Breathwrk, Sleepio) tem prontuário clínico brasileiro integrado. Nenhum DTx brasileiro tem ecossistema cannabis + saúde mental + clínico em uma plataforma. Se AraFlow for executado como módulo do AraOS — e não como produto paralelo — com curadoria clínica brasileira honesta, fluxo B2B centrado em prescritores e evidência publicada, existe um caminho real. Sem essa integração, AraFlow é só mais um app de respiração com boas intenções.**

---

## 24. R$ 2 milhões e 12 meses — plano radical

> *Plano alternativo executável, com chance real de tração.*

### Premissa

> **R$ 2M é capital para validar uma tese, não para construir uma empresa. Toda decisão deve ser reversível em 6 meses.**

### O que fazer

#### Meses 1-3 — Enxugar radicalmente

- Manter 3 protocolos: Diafragmática Profunda, Box 4-4-4-4, Coerência 5.5.
- Remover wearables do MVP.
- Remover voice journal, detecção facial, gamificação complexa.
- Remover marketplace, comunidade, social.
- Redesenhar onboarding em 90 segundos.
- Lançar app mínimo iOS + Android.

#### Meses 3-6 — Validar tração B2C enxuta

- Lançar para 1.000 usuários beta.
- Medir: D1, D7, D30 retention, NPS, sessões/semana, dropout.
- Meta: 30% D7 retention, NPS ≥ 50, ≥ 3 sessões/semana em 40%+.
- Decisão go/no-go no mês 6.

#### Meses 6-9 — Se tração OK, adicionar B2B-Pro

- Dashboard simples para médico prescritor.
- Exportação PDF para prontuário.
- Integração com AraOS para prescrição.
- 50 médicos prescritores beta.
- Medir: nº prescrições, adesão de pacientes prescritos.

#### Meses 9-12 — Se B2B-Pro OK, decisão clínica

- Iniciar 1 estudo piloto com CRO ou universidade (R$ 200-400k).
- Iniciar dossiê regulatório ANVISA (R$ 100k).
- Decidir wellness ou SaMD formalmente.
- Iniciar QMS ISO 13485 (parcial).
- Buscar R$ 5-10M Seed/A com tração.

### O que remover

- 9+ dos 12+ protocolos.
- Wearables.
- Voice journal.
- Avatar 3D.
- Marketplace.
- Comunidade.
- White label.
- B2B-Enterprise / Corporate / University / Research.
- Planos internacionais.
- Animações em 3 níveis.
- 7 dos 32 documentos de planejamento.

### O que adiar

- Submissão FDA.
- Submissão MDR.
- IA multimodal.
- Digital Twin.
- Programa de pesquisa clínica amplo.
- White label.
- Expansão LATAM.
- Cannabis medicinal.

### O que acelerar

- LGPD compliance com DPO.
- Integração AraOS profunda.
- 1 RCT piloto.
- Dossiê regulatório ANVISA inicial.
- Customer success com 50 médicos.

### Métricas de saída dos 12 meses

| Métrica | Meta |
|---------|------|
| **Usuários ativos mensais** | 5.000+ |
| **D7 retention** | ≥ 30% |
| **NPS** | ≥ 50 |
| **Médicos prescritores ativos** | 50+ |
| **Pacientes prescritos** | 500+ |
| **Estudo clínico iniciado** | Sim |
| **Dossiê regulatório iniciado** | Sim |
| **Burn rate mensal** | < R$ 200k |
| **Runway pós-12 meses** | ≥ 6 meses |

### O que não fazer de jeito nenhum

- Contratar neurocientista, estatístico, médico do sono em tempo integral.
- Lançar white label.
- Tentar FDA.
- Aceitar R$ 50M sem tração.
- Mudar de tese a cada trimestre.
- Ignorar LGPD.
- Marketing com promessas.

---

## 25. Conclusão Executiva

### Recomendação

> **Recusar R$ 50M. Recomendar reescrita radical com escopo 60-70% menor.**

### Parecer detalhado

O AraFlow é um projeto **com tese razoável e execução proposta medíocre**. A documentação é extensa e competente em muitos trechos — revisão crítica dos protocolos, separação LGPD/GDPR, design system, manifesto de marketing. **Mas competência em documentar não é competência em executar.**

A força do projeto está na **clareza de princípios éticos**, na **coragem da revisão crítica de protocolos**, e na **integração com AraOS**. A fraqueza está na **inflação de escopo**, na **ausência de priorização**, na **mistura perigosa de wellness e SaMD**, e na **presunção de que 16 eixos de produto podem coexistir em uma startup precoce**.

A equipe **conhece o domínio**. Conhece LGPD, conhece regulação, conhece clínica. Mas **confundiu conhecimento com execução**.

O mercado brasileiro de saúde mental digital é **estrutural**. Não vai embora. Não está saturado. Há espaço real para um produto brasileiro sério, com curadoria clínica, integrado a ecossistemas clínicos, com evidência. Mas o AraFlow na forma proposta vai morrer de indigestão antes de chegar ao mercado.

A comparação que importa não é Headspace ou Calm. **É Pear Therapeutics** — empresa com aprovação FDA, evidência robusta, prescrição formal, partnership com Novartis — que faliu em abril de 2023. **A lição é clara: evidência clínica + regulação sanitária não garantem viabilidade econômica.** O AraFlow precisa aprender essa lição antes de buscar R$ 50M.

### Top 5 problemas que precisam ser resolvidos

1. **Priorização.** 13 modelos de negócio é ausência de modelo. 16 eixos é ausência de eixo. A equipe precisa escolher 1 modelo e 1 eixo, respectivamente, e se comprometer.
2. **Decisão regulatória.** Wellness OU SaMD. Não ambos sem plano explícito de transição. E mesmo com plano, é arriscado.
3. **Tração mínima.** Sem 1.000 usuários ativos, 30% D7 retention, NPS ≥ 50, qualquer rodada > R$ 10M é irresponsável para ambos os lados.
4. **Integração AraOS.** Não como paralelo — como feature. AraFlow é AraOS+, não AraFlow-como-AraOS.
5. **Foco clínico.** Um RCT piloto, não cinco. Um comitê científico enxuto, não dez. Uma decisão regulatória, não duas.

### Top 5 sinais verdes que merecem ser preservados

1. **A coragem da revisão crítica dos 12 protocolos** — não é comum em healthtech brasileira.
2. **A separação LGPD/GDPR técnica** — está no nível de grandes healthtechs globais.
3. **A clareza de princípios éticos** — manifesto, voice, tom são honestos.
4. **A decisão de integrar com AraOS** — único POD defensável.
5. **A curadoria clínica multidisciplinar** — desde que enxuta.

### O que fazer agora

1. **Destruir 60-70% da documentação.** Manter apenas o que serve a um MVP enxuto.
2. **Recortar a equipe.** Consultores sob demanda, não CLT.
3. **Recortar o produto.** 3 protocolos. Sem wearables. Sem IA generativa. Sem voice.
4. **Recortar o modelo de negócio.** B2B-Pro + B2C enxuto. Só.
5. **Construir tração.** 1.000 usuários ativos antes de qualquer rodada > R$ 5M.
6. **Validar cientificamente.** 1 RCT piloto, não 5 estudos.
7. **Decidir regulatório.** Wellness puro OU SaMD, não ambos.
8. **Aprofundar integração AraOS.** Não construir paralelo; ser parte.
9. **Buscar R$ 5-10M em Seed/A**, não R$ 50M em Series A.
10. **Reapresentar para a próxima rodada com tração real, não slides bonitos.**

### A frase final

> *O AraFlow pode existir. Mas não como está. O que existe hoje é um conjunto excelente de princípios éticos, um esqueleto de documentação brilhante em muitos trechos, e um plano de execução inflado que vai quebrar a empresa antes de ela chegar ao mercado. Destruam a maioria. Mantenham o melhor. Reconstruam com foco. Aí, talvez, exista um AraFlow que mereça ser investido.*

---

**Compromissos desta auditoria:**

- ✅ Ciência — avaliada com rigor.
- ✅ Segurança do paciente — avaliada com rigor.
- ✅ Excelente experiência do usuário — avaliada com rigor.
- ✅ Sustentabilidade financeira — avaliada com rigor.
- ✅ Escalabilidade — avaliada com rigor.
- ✅ Diferenciação competitiva — avaliada com rigor.
- ✅ Viabilidade regulatória — avaliada com rigor.
- ✅ Excelência em engenharia de produto — avaliada com rigor.

**Não temos compromissos com:**

- ❌ Os sentimentos da equipe.
- ❌ As decisões previamente tomadas.
- ❌ A defesa de qualquer ideia por estar documentada.

*Esta auditoria foi realizada por um Conselho Executivo Independente. Seu compromisso é com a verdade técnica e a proteção do capital do investidor.*