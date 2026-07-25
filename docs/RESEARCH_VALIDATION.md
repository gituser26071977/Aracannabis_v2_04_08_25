# Validation 2 — Research

> **Objetivo:** avaliar se um pesquisador acadêmico consegue compreender o fluxo científico do Knowledge Engine.
> **Método:** sentar um pesquisador (PhD, pós-doc, professor) em frente ao Clinical Pipeline Explorer com `?demo=1` ativo, e pedir que ele avalie clareza metodológica, compreensão do pipeline e limitações percebidas.
> **Duração da sessão:** 20 minutos (5 min de demo + 15 min de entrevista técnica).

---

## Setup

- Demo Mode ativo (`?demo=1`)
- Pesquisador convidado sem conhecimento prévio do AraOS
- **Recomendado:** 3 perfis — (a) estatístico/bioinformata, (b) epidemiologista, (c) pesquisador em IA aplicada à saúde
- Áudio gravado (com consentimento)

---

## Protocolo de observação

| Minuto | Ação | O que observar |
|--------|------|----------------|
| 0:00 | Entregar o mouse. Dizer: *"Vou abrir uma ferramenta que processa dados clínicos. Olhe por cinco minutos e depois conversamos."* | Postura inicial: cético? curioso? apático? |
| 0:05 | Perguntar: *"Em suas palavras, o que esse sistema faz?"* | Capturar a leitura técnica dele. |
| 0:07 | Perguntar: *"Quais métodos estatísticos você consegue identificar?"* | Ele cita Pearson/Spearman? Sabe o que significam? |
| 0:10 | Perguntar sobre **limitações percebidas** (lista livre). | Capturar as 5 primeiras que ele citar. |
| 0:13 | Perguntar: *"Se você tivesse que publicar um paper usando os dados desse sistema, que pergunta faria primeiro?"* | Capturar o uso acadêmico imaginado. |
| 0:16 | Perguntar: *"O que te daria mais confiança no resultado?"* | Capturar o que ele precisa para citar. |
| 0:18 | Perguntar: *"Onde você procuraria a metodologia por trás das hipóteses?"* | Ele precisa de link para `rule_id` — onde está? |

---

## Roteiro de entrevista técnica (15 perguntas)

### Bloco 1 — Clareza metodológica

1. Qual o método de correlação? Você vê o nome dele?
2. O sistema mostra o tamanho da amostra? Se não, isso te incomoda?
3. As hipóteses são ajustadas para múltiplas comparações? (Bonferroni, FDR)
4. O sistema mostra o intervalo de confiança ou apenas o ponto?
5. Você consegue distinguir "regra" de "modelo treinado"?
6. As regras são versionadas? Você vê isso na tela?

### Bloco 2 — Compreensão do pipeline

7. O que o sistema entende como "gene"? É uma variável clínica?
8. Como o sistema lida com dados faltantes? (missing data)
9. O sistema aplica correção de tendência ou sazonalidade nos dados longitudinais?
10. Você consegue diferenciar **estado atual** de **mudança no tempo**?

### Bloco 3 — Limitações percebidas

11. Cite 3 limitações metodológicas que você enxerga
12. Em que cenários esse sistema **não deveria** ser usado?
13. Qual o pior risco de interpretação dos números apresentados?
14. O que precisaria ser adicionado para você citar em um paper?
15. Que pergunta de pesquisa esse sistema **permite** responder que antes não era possível?

---

## Critérios de sucesso

| Critério | Métrica |
|----------|---------|
| Clareza metodológica | Pesquisador identifica Pearson/Spearman nos cards sem ajuda |
| Compreensão do pipeline | Pesquisador verbaliza fluxo "paciente → gene → correlação → regra → hipótese" |
| Reconhecimento de limitações | Pesquisador cita ≥ 3 limitações reais (não inventadas) |
| Audit trail | Pesquisador identifica `rule_id` como caminho para metodologia |
| Reprodutibilidade | Pesquisador entende que o `state_hash` garante reprodutibilidade |
| Caso de uso acadêmico | Pesquisador cita ≥ 1 paper que poderia usar o sistema |
| Sugestão de melhoria | Pesquisador cita ≥ 1 adição que fortaleceria o sistema |

---

## Template de relatório

```
# Validation 2 — Sessão #___

Data: ____
Pesquisador: ____ (área: ____, instituição: ____)
Duração total: ____ min

## Clareza metodológica (nota 1–5): ___
- Comentário dele:

## Compreensão do pipeline (nota 1–5): ___
- Resumo dele:

## Limitações percebidas (em ordem de severidade)
1.
2.
3.
4.
5.

## Onde ele procuraria a metodologia
- Citou `rule_id`?
- Pediu link externo?
- Pediu paper de referência?

## Uso acadêmico imaginado
- Paper #1:
- Paper #2:

## O que ele precisa para citar
1.
2.
3.

## Veredicto
- [ ] 🟢 metodologicamente aceitável
- [ ] 🟡 metodologicamente questionável
- [ ] 🔴 metodologicamente insuficiente

## Próxima ação
```

---

## O que NÃO perguntar

- Não perguntar se ele "concorda com o produto"
- Não perguntar sobre arquitetura técnica
- Não perguntar sobre UI/UX
- Não induzir respostas

---

## Quando considerar aprovado

A validação de pesquisa está aprovada quando, em **3 sessões consecutivas** com pesquisadores diferentes:

1. 100% entendem que `rule_id` é o caminho para auditoria metodológica
2. 100% entendem que o sistema **não faz inferência causal** (apenas correlação + regras)
3. 80% conseguem citar um caso de uso acadêmico legítimo
4. 80% conseguem citar **pelo menos 3 limitações reais** (não inventadas)
5. Pelo menos 1 pesquisador cita um paper que poderia usar o sistema como fonte secundária

---

*Ver também: `RC1_DEMO_SCRIPT.md`, `CLINICAL_VALIDATION.md`, `INVESTOR_VALIDATION.md`, `DEVELOPER_VALIDATION.md`.*