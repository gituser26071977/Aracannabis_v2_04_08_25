# AraFlow — Features Futuras

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** Product Owner
>
> Este documento cataloga **todas as features planejadas para as Fases 2, 3 e além**. Está **claramente separado do MVP** (`18_MVP.md`). Nenhum item aqui entra no MVP.

---

## Sumário

1. Filosofia das features futuras
2. Fase 2 — Personalização e analytics clínico
3. Fase 3 — Biofeedback e IA avançada
4. Pós-Fase 3 — Visão de longo prazo
5. Features especulativas (low-confidence)
6. Features descartadas (com motivo)
7. Roadmap de validação

---

## 1. Filosofia das features futuras

> **Adicionar feature é fácil. Remover é difícil.** Por isso, cada feature futura precisa responder:

1. **Que valor clínico gera?**
2. **Que evidência sustenta?**
3. **Que risco regulatório traz?**
4. **Que complexidade técnica exige?**
5. **Como vamos medir sucesso?**

Se não responder a 4 de 5, **não vai para o backlog**.

---

## 2. Fase 2 — Personalização e analytics clínico

**Período:** 2027-Q2 → 2027-Q3.

### 2.1 Escalas clínicas

| Feature | Descrição | Valor clínico |
|---------|-----------|----------------|
| **GAD-7** | Ansiedade generalizada | Alto (validado) |
| **PHQ-9** | Depressão | Alto (validado) |
| **ISI** | Insônia | Alto (validado) |
| **PSS-10** | Estresse percebido | Médio |
| **EVA dor** | Intensidade de dor | Alto |
| **WHO-5** | Bem-estar | Médio |
| **MFI-20** | Fadiga | Médio |
| **ASRS-5** | Rastreio TDAH adulto | Médio |
| **EQ-5D-5L** | Qualidade de vida | Médio |

### 2.2 IA preditiva

| Feature | Descrição | Modelo |
|---------|-----------|--------|
| **Recomendação personalizada** | Próxima sessão ideal | Regressão + árvores |
| **Previsão de abandono** | Probabilidade de parar em 14d | Classificação binária |
| **Previsão de resposta** | Probabilidade de melhora clínica | Regressão |
| **Insights automáticos** | Correlações uso-desfecho | Estatísticas + narrativa |

### 2.3 Dashboard clínico

| Feature | Descrição |
|---------|-----------|
| Lista de pacientes com filtros avançados |
| Detalhe do paciente com séries temporais |
| Notas clínicas estruturadas |
| Alertas preditivos |
| Relatórios PDF |
| Comparação entre pacientes (anonimizada) |

### 2.4 Personalização avançada

| Feature | Descrição |
|---------|-----------|
| **Planta que cresce** | Avatar orgânico proporcional ao uso |
| **Missões semanais** | Sugestões de variedade |
| **Níveis e XP** | Progressão leve |
| **Selo compartilhável** | Imagem estática para redes |

### 2.5 Conteúdo expandido

| Feature | Descrição |
|---------|-----------|
| **40 trilhas de áudio** | Categorias completas |
| **+15 protocolos** | Variantes e nichos |
| **Pílulas sonoras** | Áudios curtos para pausas |
| **Conteúdo educativo** | Artigos sobre ciência da respiração |
| **Versão em inglês** | i18n |

### 2.6 UX expandida

| Feature | Descrição |
|---------|-----------|
| **Pulmão animado** | Visual didático |
| **Onda** | Modo sono |
| **Esfera** | Modo foco |
| **Mandala** | Mindfulness |
| **Partículas** | Energia |
| **Modo profundo expandido** | Sessão com mínima interface |

### 2.7 Integração AraOS

| Feature | Descrição |
|---------|-----------|
| Notas de sessão no prontuário | Registro automático |
| Visualização no prontuário | Timeline clínica |
| Sincronização de agenda | Contexto |
| Insights compartilhados | Plano integrado |

### 2.8 App nativo (opcional)

| Feature | Descrição |
|---------|-----------|
| **iOS nativo** | Swift, melhor performance |
| **Android nativo** | Kotlin, melhor integração |
| **Widgets** | Atalho na home |

---

## 3. Fase 3 — Biofeedback e IA avançada

**Período:** 2027-Q4 → 2028-Q2.

### 3.1 Biofeedback

| Feature | Descrição |
|---------|-----------|
| **HRV em tempo real** | PPG via smartwatch |
| **Coerência cardíaca visual** | Anel com cor por coerência |
| **Visual adaptativo** | Respiração guiada pelo HRV |
| **Áudio modulado** | Biofeedback sonoro |
| **GSR (sudorese)** | Estresse (Fase 3+) |
| **Temperatura** | Tendência periférica |
| **Pós-sessão analítico** | Relatório de coerência |

### 3.2 Wearables integrados

| Marca | Tipo | API |
|-------|------|-----|
| Apple Watch | PPG nativo | HealthKit |
| Garmin | PPG / ECG | Connect |
| Polar | ECG | Verity Sense |
| Oura | Tendências | Cloud API |
| Whoop | HRV + strain | Cloud API |
| Genéricos (BLE) | PPG | Padrão aberto |

### 3.3 IA generativa com guardrails

| Feature | Descrição |
|---------|-----------|
| **Narração personalizada** | Body scan com nome do paciente |
| **Acolhimento dinâmico** | Mensagens contextualizadas |
| **Insights em linguagem natural** | Texto acessível ao paciente |
| **Resumo clínico automático** | Para o profissional |
| **Tradução dinâmica** | Suporte multilíngue |

### 3.4 Edge AI

| Feature | Descrição |
|---------|-----------|
| **Modelos no dispositivo** | Privacidade |
| **Inferência offline** | Funciona sem rede |
| **Personalização local** | Aprende no cliente |

### 3.5 Pesquisa clínica

| Feature | Descrição |
|---------|-----------|
| **Consentimento específico** | Opt-in para pesquisa |
| **Dataset anonimizado** | Análise populacional |
| **Estudo clínico institucional** | Com universidades parceiras |
| **Publicação científica** | 1+ paper por ano |

### 3.6 Certificação regulatória

| Feature | Descrição |
|---------|-----------|
| **Classificação SaMD** | Avaliação ANVISA |
| **QMS ISO 13485** | Sistema de qualidade |
| **Validação clínica** | Estudo formal |
| **Submissão ANVISA** | Registro |
| **Pós-mercado** | Farmacovigilância-like |

### 3.7 Internacionalização (ES)

| Feature | Descrição |
|---------|-----------|
| **Espanhol** | Conteúdo e áudio |
| **Adaptações culturais** | Linguagem, referências |

### 3.8 Programa para clínicas

| Feature | Descrição |
|---------|-----------|
| **Multi-profissional** | Equipes |
| **Programas prontos** | Templates clínicos |
| **Treinamento da equipe** | Educação |
| **Relatórios institucionais** | Anonimizados |

---

## 4. Pós-Fase 3 — Visão de longo prazo (2028+)

> Estas features **não estão comprometidas**. Servem para inspiração e discussão.

### 4.1 Hardware próprio

| Feature | Descrição |
|---------|-----------|
| **AraFlow Band** | Pulseira com PPG dedicado |
| **Sensor de respiração** | Cinto torácico |
| **Integração nativa** | UX otimizada para hardware |

### 4.2 Pesquisa clínica multicêntrica

| Feature | Descrição |
|---------|-----------|
| **Estudo Fase III** | Validação multicêntrica |
| **Publicações Q1** | Journals de alto impacto |
| **Indicações clínicas** | Guidelines |

### 4.3 Modalidades complementares

| Feature | Descrição |
|---------|-----------|
| **Visualização VR** | Realidade virtual opcional |
| **Biofeedback multimodal** | PPG + EEG + GSR |
| **Treinamento de profissionais** | Certificação AraFlow |

### 4.4 Marketplace ético

| Feature | Descrição |
|---------|-----------|
| **Protocolos de especialistas** | Curados por comitê |
| **Conteúdo culturalmente adaptado** | Povos tradicionais |
| **Programas corporativos** | Burnout em empresas |
| **Programas educacionais** | Escolas |

### 4.5 IA multimodal

| Feature | Descrição |
|---------|-----------|
| **Análise de voz** | Marcadores de estresse (com cuidado) |
| **Análise facial** | Expressões (LGPD questionável) |
| **Detecção de padrão de digitação** | Engajamento |

### 4.6 Rede social terapêutica

| Feature | Descrição |
|---------|-----------|
| **Grupos por objetivo** | Comunidade moderada |
| **Mentoria por pares** | Pacientes expertos |
| **Conteúdo gerado por usuário** | Apenas texto, moderado |

### 4.7 Parcerias terapêuticas

| Feature | Descrição |
|---------|-----------|
| **Yoga e breathwork** | Conteúdo co-criado |
| **Programas de mindfulness secular** | MBSR, MBCT |
| **Terapia integrativa** | Combinações oficiais |

---

## 5. Features especulativas (low-confidence)

> Ideias a serem **validadas** com pesquisa clínica. **Não entram no backlog** sem evidência.

| Feature | Hipótese | Como validar |
|---------|----------|--------------|
| Realidade virtual para fobia | Exposição gradual | Estudo piloto |
| Sessões em grupo remotas | Co-regulação | Pesquisa qualitativa |
| IA que detecta pânico via voz | Intervenção precoce | Pesquisa técnica + clínica |
| Protocolos culturais específicos | Adesão por identificação | Estudo antropológico |
| Treinamento para profissionais de educação | Prevenção | RCT educacional |
| Integração com smart home | Ambiente regulado | Pesquisa comportamental |
| Sessões para Pets (!) | Co-regulação interespécies | Apenas se houver evidência sólida |

---

## 6. Features descartadas (com motivo)

> Documentadas para evitar re-apresentação.

| Feature | Motivo do descarte |
|---------|--------------------|
| Marketplace aberto de protocolos | Risco de má prática clínica |
| Compra de sessões extras | Conflita com prescrição |
| Compra de bens virtuais | Gamificação monetária viola princípios |
| Compartilhamento de progresso em redes sociais automaticamente | Privacidade |
| Login com redes sociais (Google, Facebook) | Não compatível com AraOS |
| Integração com smartwatches genéricos sem DPA | Risco regulatório |
| Versão kids com mascote comercial | Risco de marketing infantil |
| Análise de sentimento via voz | Privacidade + acurácia |
| Notificações push para "lembrar de respirar" | Intrusivo, anti-terapêutico |
| Vídeos longos de meditação guiada | Pode substituir psicoterapia |
| Chatbot terapêutico sem profissional | Risco clínico grave |
| Realidade virtual obrigatória | Acessibilidade |
| Integração com redes sociais (post automático) | Privacidade |
| Compra de conquistas (pay-to-win) | Anti-ético |
| Streak que "reseta" com som agressivo | Anti-terapêutico |
| Comentários públicos de outros pacientes | Risco social + LGPD |

---

## 7. Roadmap de validação

Antes de mover do backlog para o roadmap, cada feature precisa:

1. **Hipótese clara.**
2. **Métrica de sucesso.**
3. **Risco regulatório avaliado.**
4. **Complexidade estimada.**
5. **Sponsor (PM ou Tech Lead) dedicado.**

### 7.1 Processo

```
Ideia → Discovery → Spike → Validação → Backlog → Roadmap
```

- **Ideia:** listada em "features especulativas".
- **Discovery:** pesquisa + entrevistas.
- **Spike:** prova de conceito técnica (1–2 semanas).
- **Validação:** comitê clínico + DPO aprova.
- **Backlog:** priorizada com RICE.
- **Roadmap:** entra em fase específica.

### 7.2 Revisão

- Trimestral: revisar features especulativas.
- Anual: revisar backlog de features futuras.

---

## 8. Princípios para novas features

1. **Não criar dependência viciante.**
2. **Sempre oferecer caminho de saída.**
3. **Respeitar o profissional.**
4. **Respeitar a ciência.**
5. **Respeitar o tempo do paciente.**
6. **Respeitar a privacidade.**
7. **Não monetizar desfecho clínico.**
8. **Documentar evidência.**

---

## 9. Anti-patterns para evitar

| Anti-pattern | Por quê evitar |
|--------------|----------------|
| Feature que vicia | Anti-terapêutico. |
| Notificação que interrompe sono | Conflita com uso. |
| Streak com culpa | Aumenta abandono. |
| Comparação pública | Ansiedade. |
| Compra de vida extra | Monetização cruel. |
| Conteúdo que promete cura | Risco regulatório. |
| Compartilhamento automático | Privacidade. |
| Ranking competitivo | Ansiedade. |
| Tempo de tela como métrica | Anti-terapêutico. |
| Notificação "outros avançaram" | Comparação tóxica. |

---

## 10. Resumo executivo

| Fase | Quantidade estimada de features |
|------|-------------------------------|
| **MVP** | ~50 (em 24 épicos) |
| **Fase 2** | ~30 features novas |
| **Fase 3** | ~25 features novas |
| **Pós-Fase 3** | ~10–15 features especulativas |

---

*Futuro se constrói com cuidado. Cuide do que vem.*