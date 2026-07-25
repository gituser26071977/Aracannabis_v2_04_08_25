# Validation 3 — Investor

> **Objetivo:** avaliar a clareza do produto para um investidor.
> **Restrição absoluta:** **sem explicar arquitetura**.
> **Métricas:** em menos de 5 minutos, o investidor entende:
>   1. Qual problema é resolvido?
>   2. Qual diferencial existe?
>   3. Por que isso é difícil de copiar?
> **Duração:** 5 minutos de demo silenciosa + 10 minutos de entrevista.

---

## Regra de ouro

> **O demoer NÃO fala até o minuto 0:05.**
> A página fala por si. O investidor explora sozinho.

Se o investidor perguntar algo durante os 5 minutos iniciais, o demoer responde apenas:

> *"Por favor, continue olhando. Vamos conversar em cinco minutos."*

---

## Setup

- Demo Mode ativo (`?demo=1`)
- Tela cheia, sem distrações
- Investidor convidado sem briefing prévio
- Recomendado: 3 perfis — (a) VC generalista, (b) angel focado em health, (c) corporate venture de health tech
- Áudio gravado (com consentimento)

---

## Protocolo

| Minuto | Ação do demoer | Observação |
|--------|----------------|------------|
| 0:00 | Abrir a página e entregar o mouse. Dizer apenas: *"Olhe essa tela por cinco minutos."* | Expressão facial dele. |
| 0:05 | Perguntar: *"O que essa empresa faz, em uma frase?"* | Capturar a resposta literal. |
| 0:06 | Perguntar: *"Qual o problema que ela resolve?"* | Capturar. |
| 0:07 | Perguntar: *"Quem paga por isso?"* | Capturar. |
| 0:08 | Perguntar: *"Qual o diferencial — o que impede um concorrente de fazer igual em 6 meses?"* | **Esta é a pergunta-chave. Capturar a resposta inteira.** |
| 0:10 | Perguntar: *"Se você investisse, que pergunta técnica faria antes de assinar o cheque?"* | Capturar. |
| 0:13 | Perguntar: *"Quanto você pagaria por isso? Por quê?"* | Capturar. |
| 0:15 | Fechar. | |

---

## Roteiro de perguntas

### Bloco 1 — Clareza do produto (1 pergunta, 1 minuto)

1. **"Em uma frase, o que essa empresa faz?"**

   _Resposta esperada (qualquer variação):_ "transforma histórico clínico em padrões reproduzíveis" / "gera conhecimento verificável a partir de dados de pacientes" / "faz replay de análises clínicas".

   **O que indica falha:** "faz dashboard", "faz prontuário", "faz IA diagnóstica".

### Bloco 2 — Problema (2 perguntas, 2 minutos)

2. **"Qual problema você acha que ela resolve?"**
3. **"Esse problema já é resolvido por alguém?"**

   _Resposta esperada:_ "concorrentes existem, mas nenhum garante reprodutibilidade" / "é o problema de auditoria em IA clínica" / "é o problema de comparar resultados entre instituições".

### Bloco 3 — Diferencial (2 perguntas, 3 minutos)

4. **"O que te chamou atenção — o que é diferente?"**
5. **"Se um concorrente quisesse copiar, o que ele precisaria construir primeiro?"**

   _Resposta esperada:_ "replay determinístico" / "regras versionadas" / "state_hash reproduzível" / "audit trail por padrão".

### Bloco 4 — Moat (1 pergunta, 2 minutos)

6. **"Por que isso é difícil de copiar?"**

   _Resposta esperada:_ "precisa de anos de dados clínicos anotados" / "precisa de compliance regulatório" / "precisa de conhecimento médico embutido nas regras" / "precisa de equipe híbrida clínica + engenharia".

### Bloco 5 — Disposição a pagar (1 pergunta, 2 minutos)

7. **"Quem pagaria por isso?"**
8. **"Quanto?"**

   _Resposta esperada:_ "hospitais de pesquisa", "planos de saúde com programas de crônicos", "farmacêuticas em ensaios clínicos", "operadoras com gestão de risco".

---

## Critérios de sucesso

| Critério | Métrica |
|----------|---------|
| Compreensão em 1 frase | O investidor resume o produto em ≤ 15 palavras |
| Identificação do problema | Ele nomeia o problema corretamente (auditoria, reprodutibilidade, comparação) |
| Identificação do diferencial | Ele cita **replay**, **state_hash** ou **regras versionadas** espontaneamente |
| Identificação do moat | Ele cita ≥ 1 barreira de entrada real (dados, regulação, equipe) |
| Disposição a pagar | Ele cita ≥ 1 cliente plausível |

---

## Template de relatório

```
# Validation 3 — Sessão #___

Data: ____
Investidor: ____ (fundo: ____, foco: ____, ticket médio: ____)
Duração total: ____ min

## Frase dele (verbatim)
- "Essa empresa faz ___________"

## Problema que ele identificou
- "Resolve o problema de ___________"

## Diferencial que ele citou (verbatim)
1.
2.

## Moat que ele identificou (verbatim)
1.
2.

## Pergunta técnica que ele faria antes de investir
- ___________

## Cliente plausível que ele citou
- ___________

## Disposição a pagar
- Cifra estimada: ___________
- Modelo de receita preferido: ___________

## Veredicto
- [ ] 🟢 entendeu e veria valor
- [ ] 🟡 entendeu mas não veria valor
- [ ] 🔴 não entendeu

## Próxima ação
```

---

## O que NÃO fazer

- **NÃO** falar de arquitetura
- **NÃO** falar de tecnologia
- **NÃO** falar de equipe
- **NÃO** falar de tração
- **NÃO** mencionar números financeiros

A página fala. O investidor decide se quer saber mais.

---

## Quando considerar aprovado

A validação de investidor está aprovada quando, em **3 sessões consecutivas** com investidores diferentes:

1. 100% conseguem resumir o produto em uma frase sem ajuda
2. 80% identificam o diferencial **sem** que o demoer precise mencioná-lo
3. 80% citam uma barreira de entrada real
4. 80% citam um cliente plausível

---

*Ver também: `RC1_DEMO_SCRIPT.md`, `CLINICAL_VALIDATION.md`, `RESEARCH_VALIDATION.md`, `DEVELOPER_VALIDATION.md`.*