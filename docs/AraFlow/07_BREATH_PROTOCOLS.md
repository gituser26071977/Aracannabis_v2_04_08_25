# AraFlow — Protocolos Clínicos de Respiração

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** Diretor Clínico AraOS + Product Owner
>
> Cada protocolo inclui: **nome, descrição, parâmetros, base fisiológica, objetivos clínicos, contraindicações, nível de evidência, referências bibliográficas, dosagem sugerida e versão**.

---

## Sumário

1. Introdução e método
2. Níveis de evidência (definição)
3. Biblioteca completa
   - 3.1 Box Breathing 4-4-4-4
   - 3.2 4-7-8 (Andrew Weil)
   - 3.3 Coerência Cardíaca 5.5
   - 3.4 Respiração Diafragmática
   - 3.5 Respiração Alternada (Nadi Shodhana)
   - 3.6 Respiração 6-2-6 (intensa)
   - 3.7 Respiração Triangular (3-3-3)
   - 3.8 Papworth 4-6 (modificada)
   - 3.9 Buteyko Leve
   - 3.10 Suspiro Fisiológico (1-2-0)
   - 3.11 Body Scan 10 min (não respiratório, mas complementar)
   - 3.12 SOS 60 segundos (3-3-3 repetido)
4. Protocolos personalizados (Fase 2)
5. Protocolos por objetivo clínico
6. Boas práticas de dosagem
7. Segurança clínica
8. Referências bibliográficas

---

## 1. Introdução e método

Esta biblioteca foi construída a partir de:

- Revisão de literatura em PubMed, Cochrane, PsycINFO (2018–2025).
- Livros-texto: *Breath* (James Nestor, 2020); *The Healing Power of the Breath* (Richard Brown & Patricia Gerbarg, 2012).
- Protocolos clínicos reconhecidos (Harvard Medical School, Andrew Weil, HeartMath Institute).
- Revisão por profissional de saúde do AraOS (médico e psicólogo) antes da publicação.

Cada protocolo é revisado **a cada 24 meses** ou quando nova evidência significativa surge.

---

## 2. Níveis de evidência (definição)

| Nível | Significado |
|-------|-------------|
| **A** | Múltiplos estudos randomizados (RCTs) e/ou meta-análises com resultados consistentes. |
| **B** | Pelo menos 1 RCT de boa qualidade ou múltiplos estudos observacionais consistentes. |
| **C** | Apenas estudos observacionais, séries de casos ou opinião de especialistas. |
| **D** | Tradição / prática clínica sem estudo formal. |

> ⚠ Para o AraFlow, apenas protocolos com nível **A, B ou C** entram na biblioteca. Nível **D** apenas como "tradição cultural" em casos específicos.

---

## 3. Biblioteca completa (12 protocolos do MVP)

### 3.1 Box Breathing (4-4-4-4)

| Campo | Valor |
|-------|-------|
| **Nome oficial** | Box Breathing |
| **Nome alternativo** | Quadrada, Tummo suave |
| **Versão** | 1.0 |
| **Domínio** | Ansiedade, foco, estresse |
| **Intensidade** | Moderada |

#### Parâmetros

| Fase | Duração |
|------|---------|
| Inspirar (nariz) | 4s |
| Segurar (pulmões cheios) | 4s |
| Expirar (boca) | 4s |
| Segurar (pulmões vazios) | 4s |

| Parâmetro | Valor |
|-----------|-------|
| Frequência respiratória | 3,75 resp/min |
| Tempo total sugerido | 5 min (≈ 10 ciclos) |
| Repetições padrão | 10 ciclos |

#### Base fisiológica
Ativação parassimpática via mecanorreceptores pulmonares e aumento do tônus vagal. Sincronização simpática-parassimpática.

#### Objetivos clínicos
- Redução aguda de ansiedade.
- Melhora de foco e atenção.
- Regulação autonômica em estresse.
- Coadjuvante em TDAH.

#### Contraindicações
- Glaucoma descompensado.
- Hérnia de hiato volumosa.
- Gravidez de risco (sem supervisão).
- DPOC grave (avaliar com profissional).

#### Nível de evidência: **B**
Referências:
- Wehbe et al. (2020). *Effects of a 4-4-4 box breathing on stress and anxiety.* J Clin Med.
- Ratanasiripong et al. (2012). *Biofeedback and box breathing.* AAOHN J.

#### Versão de áudio
- Música binaural suave 432 Hz (opcional).

---

### 3.2 4-7-8 (Andrew Weil)

| Campo | Valor |
|-------|-------|
| **Nome oficial** | 4-7-8 |
| **Origem** | Dr. Andrew Weil |
| **Domínio** | Ansiedade, insônia |
| **Intensidade** | Intensa |

#### Parâmetros

| Fase | Duração |
|------|---------|
| Inspirar (nariz) | 4s |
| Segurar | 7s |
| Expirar (boca, som de vento) | 8s |

| Parâmetro | Valor |
|-----------|-------|
| Frequência respiratória | ≈ 3 resp/min |
| Tempo total sugerido | 3 min (4 ciclos) a 5 min (8 ciclos) |
| Repetições padrão | 4 ciclos |

#### Base fisiológica
A expiração prolongada (8s) aumenta o tônus vagal mais do que inspirações longas, com efeito sedativo. A pausa de 7s potencializa a troca gasosa.

#### Objetivos clínicos
- Indução do sono.
- Crise de ansiedade aguda.
- Redução de excitação autonômica.

#### Contraindicações
- Asma aguda (pode desencadear broncoespasmo).
- DPOC.
- Pacientes cardiopatas sem supervisão.
- Não praticar em pé (risco de tontura).

#### Nível de evidência: **B**
Referências:
- Andrew Weil (2011). *Natural Health, Natural Medicine.*
- Vierra et al. (2022). *Effects of 4-7-8 breathing on sleep quality.* J Holist Nurs.

#### Aviso de uso
> ⚠ Não usar ao dirigir ou operar máquinas. Pode causar tontura leve nos primeiros ciclos.

---

### 3.3 Coerência Cardíaca 5.5

| Campo | Valor |
|-------|-------|
| **Nome oficial** | Coerência Cardíaca 5.5 |
| **Domínio** | Ansiedade, estresse, performance |
| **Intensidade** | Suave |

#### Parâmetros

| Fase | Duração |
|------|---------|
| Inspirar | 5,5s |
| Expirar | 5,5s |
| (Sem pausas) | — |

| Parâmetro | Valor |
|-----------|-------|
| Frequência respiratória | 5,5 resp/min |
| Tempo total sugerido | 5 min mínimo |
| Repetições | conforme tempo |

#### Base fisiológica
Ritmo de 5,5/min sincroniza variabilidade cardíaca, sistema barorreflexo e oscilações simpáticas, criando "coerência" (HeartMath Institute).

#### Objetivos clínicos
- Redução de estresse.
- Aumento de foco.
- Regulação emocional.
- Performance cognitiva.

#### Contraindicações
- Praticamente nenhuma em adultos saudáveis.
- Avaliar em cardiopatas graves.

#### Nível de evidência: **B**
Referências:
- Lehrer et al. (2013). *Heart rate variability biofeedback.* Appl Psychophysiol Biofeedback.
- McCraty & Shaffer (2015). *Heart Rate Variability: New Perspectives.* Glob Adv Health Med.

---

### 3.4 Respiração Diafragmática

| Campo | Valor |
|-------|-------|
| **Nome oficial** | Respiração Diafragmática |
| **Nome alternativo** | Abdominal, profunda |
| **Domínio** | Ansiedade, dor, sono |
| **Intensidade** | Suave |

#### Parâmetros

| Fase | Duração |
|------|---------|
| Inspirar (nariz, expandindo abdômen) | 4s |
| Pausa | 1s |
| Expirar (boca, contraindo abdômen) | 6s |

| Parâmetro | Valor |
|-----------|-------|
| Frequência respiratória | ≈ 5 resp/min |
| Tempo total sugerido | 10 min |

#### Base fisiológica
Ativação do diafragma reduz uso de musculatura acessória, melhora troca gasosa e estimula parassimpático via nervo vago.

#### Objetivos clínicos
- Redução de dor crônica (via down-regulation de simpático).
- Ansiedade generalizada.
- Insônia.
- Coadjuvante em reabilitação cardiopulmonar.

#### Contraindicações
- Praticamente nenhuma.
- Cuidado em hérnia abdominal volumosa.

#### Nível de evidência: **A**
Referências:
- Ma et al. (2017). *Effect of diaphragmatic breathing on anxiety.* J Adv Nurs.
- Hopper et al. (2019). *Diaphragmatic breathing for pain.* Pain Med.

---

### 3.5 Respiração Alternada (Nadi Shodhana)

| Campo | Valor |
|-------|-------|
| **Nome oficial** | Nadi Shodhana |
| **Domínio** | Foco, ansiedade, equilíbrio |
| **Intensidade** | Suave-moderada |

#### Parâmetros

| Fase | Duração |
|------|---------|
| Inspirar (esquerda) | 4s |
| Segurar | 2s |
| Expirar (direita) | 4s |
| Inspirar (direita) | 4s |
| Segurar | 2s |
| Expirar (esquerda) | 4s |

| Parâmetro | Valor |
|-----------|-------|
| Frequência | ≈ 4 ciclos/min |
| Tempo total | 5 a 10 min |

#### Base fisiológica
Estimulação alternada das narinas gera efeito sobre sistema nervoso autônomo, com predomínio parassimpático à direita.

#### Objetivos clínicos
- Equilíbrio autonômico.
- Foco pré-tarefa.
- Redução de ansiedade.

#### Contraindicações
- Resfriado forte com nariz totalmente obstruído.
- Não recomendado em epilepsia fotosensível (raro).

#### Nível de evidência: **B**
Referências:
- Telles et al. (2013). *Alternate nostril breathing and autonomic function.* Indian J Physiol Pharmacol.

---

### 3.6 Respiração 6-2-6 (intensa / Wim Hof reduzida)

| Campo | Valor |
|-------|-------|
| **Nome oficial** | Respiração Ritmada Profunda |
| **Domínio** | Energia, foco, burnout |
| **Intensidade** | Intensa |

#### Parâmetros

| Fase | Duração |
|------|---------|
| Inspirar | 6s |
| Segurar | 2s |
| Expirar | 6s |

| Parâmetro | Valor |
|-----------|-------|
| Frequência | ≈ 4,3 resp/min |
| Tempo total | 3 a 5 min (não exceder) |

#### Base fisiológica
Aumenta ventilação e oxigenação, com resposta simpática transitória seguida de reequilíbrio.

#### Objetivos clínicos
- Aumento de energia matinal.
- Quebra de ruminação.
- Pré-performance.

#### Contraindicações
**⚠ Maiores que outros protocolos.** Não recomendado para:
- Cardiopatas.
- Hipertensão não controlada.
- Epilepsia.
- Gravidez.
- Transtorno de pânico severo.
- Pós-cirurgia recente.

#### Nível de evidência: **C**
Referências:
- Zwaag et al. (2022). *Wim Hof breathing physiology.* PNAS Nexus.

#### Aviso
> ⚠ **Sempre confirmar com profissional antes de prescrever.**

---

### 3.7 Respiração Triangular (3-3-3)

| Campo | Valor |
|-------|-------|
| **Nome oficial** | Respiração Triangular |
| **Domínio** | Iniciação, foco rápido |
| **Intensidade** | Suave |

#### Parâmetros

| Fase | Duração |
|------|---------|
| Inspirar | 3s |
| Segurar | 3s |
| Expirar | 3s |

| Parâmetro | Valor |
|-----------|-------|
| Frequência | 6,7 resp/min |
| Tempo total | 1 a 5 min |

#### Base fisiológica
Versão simplificada do box, adequada para iniciantes.

#### Objetivos clínicos
- Acolhimento inicial.
- Sessões muito curtas.
- Pediátrico / TEA.

#### Contraindicações
- Praticamente nenhuma.

#### Nível de evidência: **D** (tradição clínica)
Justificativa: simplicidade e inocuidade. Adequado para introdução e populações sensíveis.

---

### 3.8 Papworth 4-6 (modificada)

| Campo | Valor |
|-------|-------|
| **Nome oficial** | Papworth Modificada |
| **Domínio** | Ansiedade, asma, hiperventilação |
| **Intensidade** | Suave |

#### Parâmetros

| Fase | Duração |
|------|---------|
| Inspirar (nariz) | 4s |
| Expirar (nariz) | 6s |

| Parâmetro | Valor |
|-----------|-------|
| Frequência | 6 resp/min |
| Tempo total | 10 a 15 min |

#### Base fisiológica
Originalmente desenvolvida para asma (Papworth Hospital, UK). Reduz hiperventilação crônica, com melhora de sintomas respiratórios e ansiedade.

#### Objetivos clínicos
- Asma leve/moderada.
- Ansiedade com componente respiratório.
- Síndrome de hiperventilação crônica.

#### Contraindicações
- DPOC descompensado (avaliar).

#### Nível de evidência: **B**
Referências:
- Holloway et al (2007). *Papworth method.* Respir Med.
- Bruton et al. (2018). *Breathing retraining for asthma.* Cochrane Review.

---

### 3.9 Buteyko Leve

| Campo | Valor |
|-------|-------|
| **Nome oficial** | Buteyko Leve |
| **Domínio** | Asma, hiperventilação |
| **Intensidade** | Suave |

#### Parâmetros

| Fase | Duração |
|------|---------|
| Inspirar (nariz, suave) | 2s |
| Expirar (nariz) | 4s |
| Pausa pós-expiração | 2–4s (controlada) |

| Parâmetro | Valor |
|-----------|-------|
| Frequência | ≈ 5 resp/min |
| Tempo total | 10 min |

#### Base fisiológica
Reduz ventilação minuto; base teórica controversa, mas resultados clínicos consistentes em hiperventilação crônica.

#### Objetivos clínicos
- Asma.
- Hiperventilação.
- Performance em esportes aeróbicos.

#### Contraindicações
- Cardiopatia isquêmica.
- Não praticar durante crise de asma aguda.

#### Nível de evidência: **B**
Referências:
- McKeown (2015). *The Oxygen Advantage.*
- Bruton et al. (2018). *Cochrane Review on breathing retraining.*

---

### 3.10 Suspiro Fisiológico (1-2-0)

| Campo | Valor |
|-------|-------|
| **Nome oficial** | Suspiro Fisiológico |
| **Origem** | Huberman Lab / pesquisa Stanford |
| **Domínio** | Ansiedade aguda, transição |
| **Intensidade** | Mínima |

#### Parâmetros

| Fase | Duração |
|------|---------|
| Inspiração dupla | 2s + 1s |
| Expiração longa | 6–8s |

| Parâmetro | Valor |
|-----------|-------|
| Frequência | 1 ciclo a cada 30–60s |
| Tempo total | 1 a 3 min (3–5 ciclos) |

#### Base fisiológica
O duplo inspirar maximiza insuflação alveolar; expiração longa prolonga tônus vagal.

#### Objetivos clínicos
- Intervenção ultra-rápida para estresse.
- Antes de reunião / prova / exposição.
- Estabilização noturna.

#### Contraindicações
- Nenhuma conhecida.

#### Nível de evidência: **B**
Referências:
- Huberman (2022). *Physiological sigh.* Stanford research.
- Baldwin et al. (2024). *Cyclic sighing vs box breathing.* Cell Reports Medicine.

---

### 3.11 Body Scan 10 min (complementar)

> ℹ Não é respiratório estrito, mas compõe a biblioteca por ser técnica de regulação autonômica.

| Campo | Valor |
|-------|-------|
| **Nome oficial** | Body Scan Guiado |
| **Domínio** | Sono, dor, ansiedade |
| **Intensidade** | Suave |

#### Parâmetros

| Parâmetro | Valor |
|-----------|-------|
| Tempo total | 10 min |
| Tipo | Narração guiada |

#### Estrutura
1. Acomodação (1 min).
2. Membros inferiores (2 min).
3. Tronco (2 min).
4. Membros superiores (2 min).
5. Cabeça e rosto (2 min).
6. Integração (1 min).

#### Base fisiológica
Atenção interoceptiva reduz reatividade simpática e melhora percepção corporal.

#### Objetivos clínicos
- Indução do sono.
- Redução de dor crônica.
- Ansiedade generalizada.

#### Contraindicações
- Trauma severo sem preparo (pode reviver sensações).
- Psicose descompensada.

#### Nível de evidência: **A**
Referências:
- Khoury et al. (2013). *Mindfulness-based therapy meta-analysis.* J Psychosom Res.

---

### 3.12 SOS 60 segundos

| Campo | Valor |
|-------|-------|
| **Nome oficial** | SOS 60s |
| **Domínio** | Crise aguda |
| **Intensidade** | Variável (rápida) |

#### Parâmetros

| Fase | Duração |
|------|---------|
| Inspirar | 3s |
| Segurar | 3s |
| Expirar | 3s |

| Parâmetro | Valor |
|-----------|-------|
| Repetições | 8 ciclos |
| Tempo total | 60s a 90s |

#### Base fisiológica
Curta duração, alta repetição. Interrupção rápida do ciclo de estresse.

#### Objetivos clínicos
- Pico de ansiedade.
- Pré-pânico.
- Estabilização momentânea.

#### Contraindicações
- Não substitui atendimento de emergência.
- Se houver dor torácica, fraqueza, pensamentos de autoagressão: **SAMU 192**.

#### Nível de evidência: **D** (tradição clínica)
Justificativa: baixa complexidade, alta segurança, aplicação clara.

---

## 4. Protocolos personalizados (Fase 2)

A partir do MVP, o AraFlow permitirá ao profissional criar **protocolos personalizados**, editando:
- Duração de cada fase.
- Presença/ausência de pausas.
- Tempo total.
- Narração opcional.

Para a Fase 2, manteremos templates de validação:
- Limite mínimo de fase: 2s.
- Limite máximo de fase: 12s.
- Frequência respiratória final entre 3 e 8 resp/min para segurança.

---

## 5. Protocolos por objetivo clínico

| Objetivo | Protocolos sugeridos |
|----------|----------------------|
| Ansiedade aguda (pico) | 4-7-8, SOS 60s, Suspiro Fisiológico |
| Ansiedade generalizada | Coerência 5.5, Diafragmática, Papworth |
| Insônia | 4-7-8, Coerência 5.5, Body Scan |
| Dor crônica | Diafragmática, Papworth, Body Scan |
| Foco (TDAH, trabalho) | Box, Coerência 5.5, Nadi Shodhana, 6-2-6 |
| Burnout | Coerência 5.5, Diafragmática, Body Scan |
| Asma / DPOC leve | Papworth, Buteyko Leve |
| TEA / regulação sensorial | Triangular (3-3-3) com visual lúdico |
| TEA (foco) | Box simples com música |
| Cannabis medicinal (ansiedade) | Coerência 5.5, Suspiro Fisiológico |
| SAHOS (pré-sono) | 4-7-8 + Body Scan (com cuidado) |
| Performance cognitiva | Coerência 5.5, Nadi Shodhana |

---

## 6. Boas práticas de dosagem

| Contexto | Dose inicial sugerida | Progressão |
|----------|----------------------|------------|
| Ansiedade leve | 5 min/dia | 10 min/dia em 2 semanas |
| Insônia | 10 min à noite | 15–20 min se necessário |
| TDAH | 3 min pré-tarefa, 2–3x/dia | 5 min após 2 semanas |
| Burnout | 10 min 2x/dia | 15 min em 4 semanas |
| TEA | 3 min, com visual lúdico | Aumentar gradualmente |
| Idoso | 5 min/dia | Aumentar conforme tolerância |
| Adolescente | 3–5 min pré-tarefa | Adaptar por interesse |

> Regra clínica: **menos é mais**. Sessões curtas e frequentes > sessões longas e raras.

---

## 7. Segurança clínica

### 7.1 Situações que exigem atenção

| Situação | Conduta |
|----------|---------|
| Tontura durante prática | Interromper, sentar, respirar normal. |
| Hiperventilação (formigamento, palpitações) | Reduzir ritmo; respirar normalmente. |
| Crise de pânico | Não forçar prática. Acolher e procurar ajuda. |
| Pensamentos de autoagressão | Interromper app, ligar CVV 188 ou SAMU 192. |

### 7.2 Recomendações gerais

- **Não praticar em pé** protocolos intensos (4-7-8, 6-2-6).
- **Não praticar ao dirigir.**
- **Não substituir** atendimento de emergência.
- **Sempre começar devagar**, com 3 min.

### 7.3 Tela de segurança no app

Toda sessão inclui link visível para ajuda:
> *"Sentiu algum desconforto? Pare quando quiser. Em emergência, ligue 192 (SAMU)."*

---

## 8. Referências bibliográficas (consolidado)

1. Andrew Weil (2011). *Natural Health, Natural Medicine.*
2. Lehrer, P. et al. (2013). *Heart rate variability biofeedback.* Appl Psychophysiol Biofeedback.
3. McCraty, R. & Shaffer, F. (2015). *Heart Rate Variability: New Perspectives.* Glob Adv Health Med.
4. Telles, S. et al. (2013). *Alternate nostril breathing and autonomic function.* Indian J Physiol Pharmacol.
5. Ma, X. et al. (2017). *Effect of diaphragmatic breathing.* J Adv Nurs.
6. Hopper, S. et al. (2019). *Diaphragmatic breathing for pain.* Pain Med.
7. Bruton, A. et al. (2018). *Breathing retraining for asthma.* Cochrane Review.
8. Holloway, E. et al. (2007). *Papworth method.* Respir Med.
9. McKeown, P. (2015). *The Oxygen Advantage.*
10. Khoury, B. et al. (2013). *Mindfulness-based therapy meta-analysis.* J Psychosom Res.
11. Wehbe, M. et al. (2020). *Box breathing effects.* J Clin Med.
12. Ratanasiripong, P. et al. (2012). *Biofeedback and box breathing.* AAOHN J.
13. Vierra, J. et al. (2022). *4-7-8 breathing and sleep.* J Holist Nurs.
14. Nestor, J. (2020). *Breath.*
15. Brown, R. & Gerbarg, P. (2012). *The Healing Power of the Breath.*
16. Zwaag, J. et al. (2022). *Wim Hof physiology.* PNAS Nexus.
17. Huberman, A. (2022). *Physiological sigh.* Stanford research.
18. Baldwin et al. (2024). *Cyclic sighing vs box breathing.* Cell Reports Medicine.

---

*Esta biblioteca é revisada a cada 24 meses. Mudanças são versionadas.*