# Validation 1 — Clinical

> **Objetivo:** validar o entendimento do pipeline por um médico.
> **Método:** sentar um médico em frente ao Clinical Pipeline Explorer com `?demo=1` ativo, sem introdução, e pedir que ele verbalize o que está vendo. Anotar dúvidas, confusões, tempo de compreensão, sugestões.
> **Duração da sessão:** 15 minutos (5 min de demo + 10 min de entrevista semiestruturada).

---

## Setup

- Computador preparado, Demo Mode ativo (`?demo=1`)
- Áudio gravado (com consentimento)
- Médico convidado sem conhecimento prévio do AraOS
- Recomendado: 3 médicos de perfis diferentes (clínico geral, especialista, pesquisador clínico)

---

## Protocolo de observação

| Minuto | O que fazer | O que observar |
|--------|-------------|----------------|
| 0:00 | Entregar o mouse ao médico e dizer apenas: *"Dê uma olhada nesta página por cinco minutos. Não tem objetivo específico — só explore."* | Ver se ele lê os cards na ordem (pipeline → genome → correlações → hipóteses → grafo → replay). Onde ele trava? Onde ele volta? |
| 0:02 | Não interferir. | Primeiro ponto de confusão textual. |
| 0:04 | Não interferir. | Segunda passada: ele volta pra revisar algo? O quê? |
| 0:05 | Pedir: *"Me diga, com suas palavras, o que essa ferramenta faz."* | A resposta dele é o **teste** — capturá-la literalmente. |
| 0:08 | Perguntar: *"O que você entendeu pelo card X?"* — um por um, na ordem que ele escolheu. | Capturar a interpretação real vs a intenção. |
| 0:12 | Perguntar: *"Isso seria útil no seu consultório? Em que situação?"* | Capturar uso imaginado. |
| 0:14 | Perguntar: *"Se você pudesse mudar UMA coisa, qual seria?"* | Capturar sugestão #1. |

---

## Roteiro de entrevista (10 perguntas)

1. O que essa ferramenta faz, em suas palavras?
2. O que é "genome" nesse contexto? (deixar ele falar primeiro; só corrigir se totalmente errado)
3. O que é "state_hash"? Você confiaria num sistema que diz "state_hash idêntico"?
4. Quando você vê "ρ = -0.82", o que isso significa para você?
5. Quando vê "hipótese CONFIRMED com 91% de confiança", o que você decide fazer?
6. A afirmação da hipótese foi clara? Você saberia explicar para um paciente?
7. O grafo ajudou ou atrapalhou? Você prefere a lista de correlações ou o grafo?
8. O replay mudou sua confiança no resultado? Por quê?
9. Onde você procuraria o **porquê** de uma hipótese ter sido gerada? (audit trail)
10. Se você pudesse mudar UMA coisa, o que seria?

---

## Critérios de sucesso da validação

| Critério | Métrica |
|----------|---------|
| Compreensão em 5 min | O médico consegue verbalizar o fluxo principal sem ajuda |
| Compreensão do "genome" | Ele entende que é uma representação, não um diagnóstico |
| Compreensão do "state_hash" | Ele entende que é uma garantia de reprodutibilidade |
| Compreensão do "ρ" | Ele interpreta correlação corretamente |
| Compreensão de "hipótese" | Ele entende que não é sugestão clínica |
| Audit trail encontrável | Ele consegue identificar onde verificar a origem |
| Confiança no replay | Ele entende que o replay prova que o sistema não é aleatório |
| Utilidade percebida | Ele cita pelo menos 1 caso de uso real |

---

## Template de relatório (preencher após a sessão)

```
# Validation 1 — Sessão #___

Data: ____
Médico: ____ (especialidade: ____, tempo de formação: ____)
Duração total: ____ min

## Compreensão em 5 min
- Resumo dele (em 1 parágrafo, com as palavras dele):

## Dúvidas surgiram em
- [ ] Card Paciente
- [ ] Card Pipeline
- [ ] Card Genome
- [ ] Card Correlações
- [ ] Card Hipóteses
- [ ] Card Grafo
- [ ] Card Replay
- [ ] Timeline rail

## Tempo necessário para compreensão
- até 1 min:
- 1–3 min:
- 3–5 min:
- mais de 5 min:

## Sugestões de UX (verbatim, na ordem que ele falou)
1.
2.
3.

## Veredicto
- [ ] 🟢 compreendeu sem ajuda
- [ ] 🟡 compreendeu com 1 dica
- [ ] 🔴 não compreendeu

## Próxima ação
```

---

## O que NÃO perguntar

- Não perguntar se "concorda com o diagnóstico" (não é ferramenta diagnóstica)
- Não perguntar sobre a arquitetura subjacente
- Não perguntar sobre tecnologia, framework, banco de dados

---

## Quando considerar aprovado

A validação clínica está aprovada quando, em **3 sessões consecutivas** com médicos diferentes:

1. 80% compreendem o fluxo principal sem ajuda
2. 100% entendem que o genome **não é** um diagnóstico
3. 100% entendem que o replay é uma garantia de reprodutibilidade
4. Pelo menos 1 caso de uso clínico real é citado por sessão

---

*Ver também: `RC1_DEMO_SCRIPT.md`, `RC1_DEMO_CHECKLIST.md`, `INVESTOR_VALIDATION.md`, `RESEARCH_VALIDATION.md`.*