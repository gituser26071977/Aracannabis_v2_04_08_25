# AraFlow — Protocolos de Segurança

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Status:** Fase 0.5 — Clinical Validation
> **Autoria multidisciplinar:** Médico Intensivista · Médico do Sono · Psiquiatra · Psicólogo · Neurocientista · Pesquisador Clínico · UX em Saúde

> **Princípio orientador:** *Primum non nocere.* Em caso de dúvida, **parar** é sempre a decisão mais segura.

---

## Sumário

1. Filosofia de segurança
2. Classificação de risco de eventos
3. Eventos adversos — visão geral
4. Resposta a eventos adversos individuais
5. Quando interromper automaticamente a sessão
6. Quando orientar procurar emergência
7. Quando apenas reduzir intensidade
8. Quando apenas acolher
9. Detecção de padrões preocupantes
10. Interrupção por comportamento de risco
11. Triagem de risco ao onboarding
12. Populações de risco especial
13. Sinais de alerta de ideação suicida
14. Resposta a crise em escala clínica (GAD-7, PHQ-9)
15. Procedimento de notificação ao profissional
16. Procedimento de notificação ao DPO (se evento grave)
17. Procedimento de farmacovigilância-like
18. Logs de segurança
19. Fluxogramas
20. Testes de stress de cenários adversos
21. Educação do usuário
22. Educação do profissional
23. Atualização deste documento

---

## 1. Filosofia de segurança

> *Status: CONSENSO.*

### 1.1 Princípios

1. **Segurança acima de engajamento.**
2. **Detecção precoce** > reação tardia.
3. **Interromper automaticamente** quando houver risco.
4. **Sempre fornecer caminho para ajuda humana.**
5. **Sem julgamento, sem culpabilização.**
6. **Logs clínicos** de qualquer evento.
7. **Profissional sempre visível** quando há risco.

### 1.2 Cultura de segurança

- **Speak up:** qualquer pessoa pode reportar risco.
- **No blame:** erros são oportunidades de aprendizado.
- **Transparency:** incidentes são documentados.
- **Continuous learning:** a cada evento, melhorar.

### 1.3 Hierarquia de decisões

| Nível | Decisão | Quem |
|-------|---------|------|
| **1** | Interromper sessão | Automático (app) |
| **2** | Acolher e continuar | App + texto clínico |
| **3** | Alertar profissional | App + sistema |
| **4** | Acionar emergência | App + tela + hotline |
| **5** | Reportar evento adverso | App + backend + DPO |

---

## 2. Classificação de risco de eventos

### 2.1 Por severidade

| Nível | Definição | Resposta |
|-------|-----------|----------|
| **1 — Leve** | Desconforto passageiro; autolimitado. | Acolher; continuar se quiser. |
| **2 — Moderado** | Sintoma persistente; precisa pausa; sem urgência. | Interromper; oferecer continuação reduzida. |
| **3 — Grave** | Risco à saúde; precisa atendimento. | Interromper; recomendar consulta. |
| **4 — Crítico** | Emergência médica. | Acionar 192 imediatamente. |

### 2.2 Por causalidade

| Relação | Significado |
|---------|-------------|
| **Certa** | Causado pela técnica (ex: hiperventilação direta). |
| **Provável** | Forte relação temporal e plausibilidade. |
| **Possível** | Relação temporal; causalidade incerta. |
| **Improvável** | Coincidência temporal; outra causa mais provável. |
| **Não relacionada** | Outra causa clara. |

> *Esta classificação é feita pelo médico responsável, não pelo app.*

### 2.3 Por frequência esperada

| Frequência | Exemplo |
|------------|---------|
| **Muito comum (> 10%)** | Tontura leve em 4-7-8 (1ª semana). |
| **Comum (1-10%)** | Formigamento em protocolos de intensidade moderada. |
| **Incomum (0,1-1%)** | Crise de pânico em pacientes predispostos. |
| **Raro (< 0,1%)** | Síncope em jovem saudável. |
| **Muito raro** | Arritmia grave desencadeada. |

---

## 3. Eventos adversos — visão geral

> *Status: CONSENSO.*

### 3.1 Lista de eventos monitorados

| Evento | Severidade típica | Monitoramento |
|--------|-------------------|---------------|
| Tontura / vertigem | 1-2 | Ativo |
| Hiperventilação | 1-2 | Ativo |
| Formigamento | 1-2 | Ativo |
| Crise de ansiedade durante sessão | 2-3 | Ativo |
| Crise de pânico | 3 | Ativo + alerta profissional |
| Dor torácica | 3-4 | Ativo + tela emergência |
| Dispneia | 3-4 | Ativo + tela emergência |
| Síncope / pré-síncope | 4 | Ativo + emergência |
| Convulsão | 4 | Ativo + emergência |
| Hipotensão | 2-3 | Ativo |
| Hipertensão aguda | 3 | Ativo |
| Náusea | 1-2 | Ativo |
| Cefaleia | 1-2 | Ativo |
| Pensamentos suicidas / autolesão | 4 | Ativo + alerta crítico |
| Agravamento de sintoma | 2-3 | Ativo |
| Crise asmática | 3-4 | Ativo + emergência |
| Reativação de trauma (TEPT) | 2-3 | Ativo |
| Despersonalização / desrealização | 2-3 | Ativo |
| Dissociação | 2-3 | Ativo |

---

## 4. Resposta a eventos adversos individuais

> *Status: CONSENSO. Cada evento tem conduta específica.*

### 4.1 Tontura / vertigem

**Causa provável:** hiperventilação leve, hipotensão, Valsalva.

**Resposta do app:**
- Interromper sessão automaticamente (Nível 2).
- Tela: "Você sentiu tontura? Pare. Sente-se. Respire normalmente. Beba água."
- Sugestão de hidratação.
- Oferecer continuação reduzida (protocolo suave).
- Log do evento.

**Conduta do usuário:**
- Sentar ou deitar.
- Respirar normalmente.
- Hidratar.

**Encaminhamento:**
- Se recorrente: consultar médico.
- Se associado a outros sintomas: emergência.

### 4.2 Hiperventilação

**Sinais:** respiração rápida, formigamento, palpitações, tontura.

**Resposta do app:**
- Detectar padrão (via HRV na Fase 3; por autorrelato no MVP).
- Acionar tela: "Sua respiração parece rápida. Tente diminuir."
- Oferecer pausa.
- Log.

**Conduta do usuário:**
- Reduzir ritmo.
- Respirar pelo nariz.
- Se persistir, parar.

**Encaminhamento:**
- Se síncope ou dor torácica: emergência.

### 4.3 Crise de ansiedade durante a sessão

**Causa provável:** foco atencional no corpo pode aumentar percepção; técnica inadequada.

**Resposta do app:**
- Acolher: "Sentir ansiedade durante a prática pode acontecer. Não é falha sua."
- Oferecer pausar ou encerrar.
- Sugerir sessão mais suave.
- Log.
- Se recorrente, alerta ao profissional.

**Conduta do usuário:**
- Pausar ou parar.
- Respirar normalmente.
- Considerar técnica de grounding (5-4-3-2-1).

**Encaminhamento:**
- Se frequente: reavaliação clínica.

### 4.4 Crise de pânico

**Sinais:** medo intenso, sensação de morte, despersonalização, sudorese.

**Resposta do app:**
- Tela especial de acolhimento.
- Pausa automática.
- Linguagem calma, lenta.
- **Recomendar não continuar** sem suporte.
- Log + alerta profissional.
- Botão "Falar com profissional" visível.
- Botão de emergência sempre acessível.

**Conduta do usuário:**
- Parar.
- Respirar normalmente (não forçar).
- Procurar contato humano.
- Em pânico severo, ligar 192 ou ir a emergência.

**Encaminhamento:**
- **Sempre** acompanhamento psiquiátrico.

### 4.5 Dor torácica

**Causa possível:** desde musculoskeletal até IAM.

**Resposta do app:**
- **Interromper sessão IMEDIATAMENTE.**
- Tela de emergência:
  - "**Pare agora.** Dor torácica pode ser grave."
  - "Se persistir por mais de 5 minutos, **ligue 192 (SAMU)**."
  - Botão de ligação direta para 192.
- Log crítico.
- Alerta ao profissional.

**Conduta do usuário:**
- Parar.
- Sentar.
- Avaliar intensidade.
- Se intensa/prolongada: emergência.

**Encaminhamento:**
- **Sempre** avaliação médica presencial.

### 4.6 Dispneia (falta de ar)

**Sinais:** dificuldade para respirar, sensação de sufocamento.

**Resposta do app:**
- Interromper.
- Tela: "Pare agora. Respire normalmente. Se a falta de ar for intensa, ligue 192."
- Log.
- Alerta profissional.

**Conduta do usuário:**
- Parar.
- Sentar.
- Respirar lento.
- **Se intensa** ou com lábios arroxeados: emergência.

**Encaminhamento:**
- Avaliação médica.

### 4.7 Síncope (desmaio)

**Causa possível:** hipotensão, Valsalva, hiperventilação, hipoglicemia.

**Resposta do app:**
- Detectar inatividade + orientação do dispositivo (Fase 3).
- Tela: "Deite-se. Eleve as pernas. Beba água."
- Se não houver melhora em 5 min: "Ligue 192."
- Log crítico.
- Alerta profissional.

**Conduta do usuário / terceiros:**
- Deitar.
- Elevar pernas.
- Afrouxar roupa.
- Lateralizar se inconsciente.
- Não dar água se inconsciente.

**Encaminhamento:**
- **Sempre** emergência.

### 4.8 Convulsão

**Resposta do app:**
- Tela: "Você está tendo uma convulsão?"
- "Se sim: **não segure.** Lateralize. Ligue 192."
- Log crítico.

**Conduta de terceiros:**
- Lateralizar.
- Proteger cabeça.
- **Não** colocar nada na boca.
- Não restringir.
- Cronometrar duração.

**Encaminhamento:**
- **Sempre** emergência + neurologista.

### 4.9 Queda de pressão (hipotensão)

**Sinais:** tontura ao levantar, fraqueza, sudorese, palidez.

**Resposta do app:**
- Acolher.
- Recomendar sentar/deitar.
- Hidratação.
- Se recorrente, consultar médico.
- Log.

**Conduta do usuário:**
- Sentar ou deitar.
- Levantar devagar.
- Hidratar.
- Se反复: médico.

### 4.10 Hipertensão aguda (pico pressórico)

**Sinais:** cefaleia, visão turva, dor torácica, dispneia.

**Resposta do app:**
- Interromper.
- Tela: "Pare. Meça sua pressão. Se pressão > 180/120, procure emergência."
- Log.
- Alerta profissional.

**Encuta do usuário:**
- Sentar.
- Medir PA se tiver em casa.
- Se > 180/120: emergência.

### 4.11 Náusea

**Causa possível:** hiperventilação, ansiedade, posição.

**Resposta do app:**
- Acolher.
- Sugerir pausar.
- Hidratação.
- Log.

**Encaminhamento:**
- Se recorrente ou persistente: médico.

### 4.12 Cefaleia

**Causa possível:** hiperventilação, tensão muscular, desidratação.

**Resposta do app:**
- Acolher.
- Sugerir pausar.
- Hidratação.
- Log.

**Encaminhamento:**
- Se súbita, intensa, ou "pior cefaleia da vida": emergência.

### 4.13 Pensamentos suicidas ou de autolesão

> *Status: HIPÓTESE forte de CONSENSO — abordagem baseada em evidências de prevenção.*

**Sinais:**
- Relato direto.
- Padrão de uso estranho (muitos acessos curtos).
- Frases-chave em notas livres.
- Respostas em escalas indicando desesperança.

**Resposta do app:**
- **Tela de acolhimento com hotline CVV 188 visível imediatamente.**
- "Você não está sozinho. Ligue 188 (CVV) — funciona 24h, gratuito."
- Botão de ligação direta.
- **Não** minimizar.
- **Não** tentar "resolver".
- Log + alerta profissional Imediato.
- Marcação interna de "paciente em risco" (com proteção de privacidade).
- Recomendar não continuar uso sozinho.

**Conduta do profissional (alertado):**
- Contato em 24h.
- Avaliação presencial em 48h.
- Se risco iminente: emergência.

**Encaminhamento:**
- **Sempre** acompanhamento psiquiátrico.

### 4.14 Reativação de trauma (TEPT)

**Sinais:** flashbacks, medo intenso, dissociação, hipervigilância.

**Resposta do app:**
- Interromper.
- Acolher: "Você está tendo uma reação intensa. Você está seguro."
- Grounding (5-4-3-2-1) opcional.
- Log.
- Alerta profissional.
- Recomendar consulta especializada.

**Conduta:**
- Procurar terapeuta de TEPT.
- Não continuar uso sem supervisão.

### 4.15 Despersonalização / desrealização

**Sinais:** sentir-se "fora do corpo", mundo parecer irreal.

**Resposta do app:**
- Acolher.
- Recomendar pausar.
- Log.
- Alerta profissional.

**Encaminhamento:**
- Avaliação médica/psiquiátrica.

### 4.16 Crise asmática

**Sinais:** sibilos, falta de ar, aperto no peito.

**Resposta do app:**
- Interromper.
- "Pare agora. Use sua bombinha. Se não melhorar, ligue 192."
- Log.
- Alerta profissional.

**Conduta:**
- **Broncodilatador** (bombinha).
- Se sem melhora: emergência.

### 4.17 Agravamento de sintoma

**Sinais:** piora clara de ansiedade, sono, dor após início do AraFlow.

**Resposta do app:**
- Acolher.
- Sugerir pausar e consultar profissional.
- Log.
- Alerta profissional.

**Conduta:**
- Reavaliação clínica.
- Possível ajuste de protocolo.

---

## 5. Quando interromper automaticamente a sessão

> *Status: CONSENSO. Implementação obrigatória no MVP.*

| Evento | Ação do app |
|--------|-------------|
| Relato de evento adverso (qualquer) | Pausa + tela de acolhimento. |
| Relato de evento adverso grave (dor torácica, dispneia, síncope) | Encerramento + tela de emergência. |
| Frequência cardíaca muito alta (Fase 3) | Pausa + alerta. |
| Frequência cardíaca muito baixa (Fase 3) | Pausa + alerta. |
| Inatividade prolongada (60s) | Pergunta: "Você está aí?" |
| Movimento brusco (acelerômetro — Fase 3) | Pausa (possível queda). |

---

## 6. Quando orientar procurar emergência

> *Sinais que EXIGEM encaminhamento a emergência.*

- Dor torácica intensa ou prolongada.
- Dispneia intensa.
- Síncope.
- Convulsão.
- PA > 180/120 (suspeita).
- Confusão mental súbita.
- Hemiparesia / disartria / assimetria facial (AVC).
- Ideação suicida com plano.
- "Pior cefaleia da vida" (suspeita de HSA).

**Mensagem universal:**
> "**Procure um serviço de emergência agora.** Ligue 192 (SAMU) ou vá ao pronto-socorro mais próximo."

---

## 7. Quando apenas reduzir intensidade

> *Sinais que pedem ajuste, não parada.*

- Tontura leve após sessão.
- Ansiedade leve.
- Insônia inicial.
- Cefaleia leve.

**Resposta:** ajustar protocolo para versão mais suave.

---

## 8. Quando apenas acolher

> *Situações em que a técnica está correta e o usuário só precisa de validação.*

- Desconforto passageiro.
- Frustração por baixa adesão.
- Dificuldade em seguir ritmo.
- Cansaço.

**Resposta:** acolhimento sem mudança técnica.

---

## 9. Detecção de padrões preocupantes

> *Status: CONSENSO. Implementação MVP.*

### 9.1 Padrões a monitorar

| Padrão | Sinal |
|--------|-------|
| **Queda brusca de adesão** | -50% em 7 dias. |
| **Aumento de sessões "canceladas por evento"** | > 30% das sessões. |
| **Múltiplos eventos adversos** | 3+ em 1 mês. |
| **Busca de termos críticos** | "suicídio", "morte", etc. |
| **Acesso repetido ao SOS** | > 3x/dia por 7 dias. |
| **Padrão noturno anômalo** | Sessões em horários 2h-4h da manhã. |

### 9.2 Resposta

| Padrão | Resposta |
|--------|----------|
| Queda de adesão | Mensagem calorosa; profissional notificado. |
| Eventos adversos | Profissional notificado. |
| Termos críticos | Tela de hotline; profissional notificado imediatamente. |
| Acesso SOS excessivo | Verificar com profissional. |
| Padrão noturno | Avaliar insônia severa. |

---

## 10. Interrupção por comportamento de risco

> *Status: CONSENSO.*

### 10.1 Comportamentos que justificam interrupção

- Tentativa de burlar limites de dose.
- Compartilhamento de conta (LGPD + segurança).
- Uso em estado alterado (álcool, drogas).
- Recusa em atualizar consentimento.
- Tentativa de acessar dados de terceiros.

### 10.2 Resposta

- Bloqueio de feature.
- Mensagem educativa.
- Alerta profissional.
- **Não** exclusão imediata — oferecer regularização.

---

## 11. Triagem de risco ao onboarding

> *Status: CONSENSO. Implementação MVP obrigatória.*

### 11.1 Perguntas obrigatórias

1. Histórico de síncope?
2. Epilepsia?
3. Problemas cardíacos?
4. Asma / DPOC?
5. Glaucoma?
6. Gravidez?
7. Transtorno de pânico?
8. TEPT?
9. Hipertensão não controlada?
10. Ideação suicida atual?

### 11.2 Resposta

- **Se "sim"** para 1, 2, 7, 8, 10: **bloquear uso sem profissional**.
- **Se "sim"** para outros: **alertar + oferecer versão reduzida**.
- **Se "sim"** para 10: **tela de hotline imediata + encaminhamento**.

---

## 12. Populações de risco especial

> *Status: CONSENSO.*

### 12.1 Regras adicionais por população

| População | Regra adicional |
|-----------|-----------------|
| **Gestante** | Sem retenção > 4s; sessão curta; aviso de decúbito. |
| **Idoso frágil** | Sessão supervisionada no início; sentar obrigatório. |
| **Criança** | Modo infantil obrigatório; presença de adulto. |
| **TEA adulto** | Visual previsível; tolerância a interrupção. |
| **TEPT** | Body scan contraindicado sem preparo. |
| **Pânico severo** | Não iniciar sem estabilização. |
| **Depressão grave** | Triagem de suicídio obrigatória. |
| **Psicose** | Avaliação psiquiátrica antes de iniciar. |

---

## 13. Sinais de alerta de ideação suicida

> *Status: CONSENSO forte.*

### 13.1 Sinais indiretos a monitorar

- Queda abrupta de uso (desesperança).
- Aumento súbito de uso (buscando alívio).
- Relatos de "não aguento mais".
- Pesquisas por "suicídio", "morte", "fim".
- Frases em notas livres.
- Escalas PHQ-9 com item 9 positivo.

### 13.2 Resposta

1. **Não ignorar.**
2. **Tela de acolhimento + CVV 188 visível**.
3. **Botão de ligação direta.**
4. **Alerta profissional Imediato.**
5. **Marcação interna de risco (privada).**
6. **Recomendação de não continuar sozinho**.

### 13.3 Princípios

- **Perguntar diretamente** se houver preocupação: "Você está pensando em se machucar?"
- **Sem julgamento**.
- **Sem promessas mágicas**.
- **Conexão com ajuda humana sempre**.

---

## 14. Resposta a crise em escala clínica

> *Vide `25_RESEARCH_PROTOCOL.md` para cadência.*

### 14.1 Limiares críticos

| Escala | Limiar | Ação |
|--------|--------|------|
| GAD-7 | ≥ 15 | Alerta profissional + mensagem cuidadosa. |
| GAD-7 | ≥ 20 | Alerta Imediato + recomendação presencial. |
| PHQ-9 | ≥ 20 | Alerta profissional + triagem de suicídio. |
| PHQ-9 item 9 | > 0 | Triagem obrigatória de suicídio. |
| ISI | ≥ 22 | Alerta profissional. |
| PSS-10 | ≥ 27 | Alerta profissional. |
| EVA | ≥ 7 | Reavaliação de protocolo de dor. |

---

## 15. Procedimento de notificação ao profissional

> *Status: CONSENSO.*

### 15.1 Tipos de alerta

| Tipo | Canal | Latência |
|------|-------|----------|
| **Crítico** | Push + e-mail + SMS | < 1h |
| **Importante** | Push + e-mail | < 24h |
| **Informativo** | Apenas dashboard | semanal |

### 15.2 Conteúdo do alerta

- Quem (paciente)
- O quê (evento)
- Quando
- Contexto (sessão em andamento, escala, etc.)
- Ação sugerida

---

## 16. Procedimento de notificação ao DPO

> *Status: CONSENSO.*

### 16.1 Quando

- Evento adverso grave (grau 3-4).
- Vazamento de dados.
- Reclamação grave.
- Indício de uso inadequado.

### 16.2 Como

- Sistema de ticket interno.
- Prazo: 24h.

---

## 17. Procedimento de farmacovigilância-like

> *Status: CONSENSO. Pré-requisito para classificação SaMD.*

### 17.1 Definição

O AraFlow não é medicamento, mas pode causar eventos adversos. Por isso, adotamos **práticas de farmacovigilância adaptadas**.

### 17.2 Pipeline

```
Evento adverso reportado
  → Triagem automática
  → Classificação de severidade
  → Investigação clínica
  → Relatório interno
  → Revisão de protocolo
  → Comunicação a usuários (se aplicável)
  → Reporte a autoridades (se grave)
```

### 17.3 Periodicidade

- **Revisão semanal** de eventos leves.
- **Revisão imediata** de eventos moderados-graves.
- **Relatório anual** consolidado.

---

## 18. Logs de segurança

> *Status: CONSENSO.*

### 18.1 Eventos logados

- Toda interrupção automática.
- Todo relato de evento adverso.
- Toda triagem de risco.
- Toda ação de hotline.
- Todo alerta ao profissional.
- Toda exclusão de conta.
- Toda alteração de consentimento.

### 18.2 Retenção

- Eventos clínicos: 60 meses.
- Eventos técnicos: 12 meses.

### 18.3 Acesso

- Paciente (próprios eventos).
- Profissional (pacientes sob cuidado).
- DPO e segurança (auditoria).

---

## 19. Fluxogramas

### 19.1 Fluxo geral de evento adverso

```
Sessão em andamento
  ↓
Evento adverso detectado (relato ou sensor)
  ↓
Classificação de severidade
  ├─ Leve ──► Acolhimento + continuação opcional
  ├─ Moderado ──► Pausa + acolhimento + continuação reduzida
  ├─ Grave ──► Encerramento + tela orientação
  └─ Crítico ──► Encerramento + emergência (192)
  ↓
Log do evento
  ↓
Comunicação ao profissional (se moderado+)
  ↓
Reavaliação de protocolo (se recorrente)
```

### 19.2 Fluxo de triagem ao onboarding

```
Novo usuário
  ↓
Triagem de risco (10 perguntas)
  ├─ Sem fatores ──► Acesso liberado
  ├─ Fatores relativos ──► Versão reduzida + alertas
  └─ Fatores críticos ──► Bloqueio + encaminhamento
  ↓
Consentimento
  ↓
Acesso liberado
```

### 19.3 Fluxo de ideação suicida

```
Sinal detectado
  ↓
Tela de acolhimento + CVV 188
  ↓
Botão de ligação direta
  ↓
Alerta Imediato ao profissional
  ↓
Marcação interna de risco
  ↓
Recomendação: não continuar sozinho
  ↓
Profissional contacta em < 24h
```

### 19.4 Fluxo de evento crítico (dor torácica)

```
Relato de dor torácica
  ↓
Encerramento IMEDIATO da sessão
  ↓
Tela de emergência
  ├─ 192 visível
  ├─ Botão de ligação direta
  └─ Recomendação: vá a emergência
  ↓
Log crítico
  ↓
Alerta Imediato ao profissional
  ↓
Follow-up em 24h
```

---

## 20. Testes de stress de cenários adversos

> *Status: CONSENSO.*

### 20.1 Cenários a testar

1. Usuário relata tontura no meio de sessão intensa.
2. Usuário relata dor torácica.
3. Usuário pesquisa "suicídio".
4. Sessão interrompida por queda de conexão (não é evento adverso, mas testar recuperação).
5. Usuário marca "sim" para todas as triagens.
6. Usuário relata evento adverso grave após sessão.
7. Usuário reporta múltiplos eventos em 1 dia.
8. Padrão de uso anômalo (SOS repetido).
9. Termo crítico em nota livre.
10. Pressão alta reportada.

### 20.2 Método

- Teste de mesa com equipe.
- Simulação em ambiente de staging.
- QA manual + automatizado.

---

## 21. Educação do usuário

> *Status: CONSENSO.*

### 21.1 Conteúdo educativo

- Aviso na primeira sessão.
- Tela de segurança em sessões intensas.
- Mensagem educativa após evento adverso.
- FAQ sobre segurança.

### 21.2 Tom

- Acolhedor, sem alarmismo.
- Sem paternalismo.
- Linguagem clara.

---

## 22. Educação do profissional

> *Status: CONSENSO.*

### 22.1 Capacitação

- Treinamento obrigatório antes de prescrever.
- Material de farmacovigilância-like.
- Acesso a logs clínicos.
- Workflow de alertas.

### 22.2 Responsabilidades

- Monitorar pacientes ativos.
- Responder alertas em prazo adequado.
- Documentar decisões clínicas.
- Reportar eventos adversos.

---

## 23. Atualização deste documento

- **Revisão trimestral** obrigatória.
- **Revisão extraordinária** se:
  - Evento grave.
  - Nova evidência.
  - Mudança regulatória.
  - Feedback de usuário ou profissional.

---

*Segurança não é feature. É postura. Cuide sempre.*