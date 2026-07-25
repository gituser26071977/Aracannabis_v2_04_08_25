# Validation 4 — Developer

> **Objetivo:** avaliar se um desenvolvedor consegue integrar com o AraOS Knowledge Engine usando **apenas** o `OPENAPI.yaml`.
> **Método:** entregar o `OPENAPI.yaml` + URL base + credenciais. Pedir que ele construa um cliente mínimo que execute um pipeline e leia o resultado. Anotar dúvidas, endpoints confusos, documentação insuficiente.
> **Duração:** 60 minutos (10 min leitura + 50 min coding).

---

## Setup

- Fornecer ao desenvolvedor:
  - URL base da API (ex.: `https://api.arapath.com.br`)
  - Token JWT (escopo: `knowledge.read`, `knowledge.execute`)
  - Arquivo `OPENAPI.yaml`
  - 1 parágrafo de contexto (≤ 50 palavras) sobre o produto
- **NÃO** fornecer:
  - Documentação adicional
  - Exemplos de código
  - Diagramas
  - Nomes de endpoints já decorados

---

## Tarefa

> *"Em 50 minutos, escreva um cliente em qualquer linguagem que: (a) execute o pipeline de knowledge para o paciente `patient_demo_a1`, (b) recupere o genome gerado, (c) execute o replay da sessão resultante, (d) imprima se o `state_hash` foi igual. Use apenas o OPENAPI.yaml como referência. Pode escolher qualquer biblioteca HTTP. Anote toda dúvida que tiver."*

---

## Protocolo de observação

| Minuto | Ação do dev | O que observar |
|--------|-------------|----------------|
| 0–10 | Lendo o OPENAPI | Onde ele trava? Qual seção ele lê primeiro? |
| 10–30 | Codando | Ele volta ao YAML quantas vezes? Em quais seções? |
| 30–50 | Codando / debugando | Ele erra algum endpoint? Qual? Por quê? |
| 50 | Entrega + 10 min de entrevista | Anotar dúvidas e feedback verbal |

---

## Roteiro de entrevista (após 50 min)

### Bloco 1 — Clareza do contrato

1. Você conseguiu entender **o que** cada endpoint faz sem precisar perguntar?
2. Algum nome de endpoint te confundiu? Qual? Por quê?
3. Os DTOs estavam claros? Onde?
4. Os DTOs estavam confusos? Onde?
5. O envelope `{ success, data, error, meta }` foi claro? Você soube lidar com `error`?

### Bloco 2 — Suficiência

6. Você conseguiu descobrir **como autenticar** lendo o YAML?
7. Você encontrou o **escopo/tenant** no header? Onde?
8. Você entendeu que precisava passar `correlation_id` em algum lugar?
9. Você encontrou a **lista de tipos de regra** (`rule_id`) no YAML? Onde?
10. Você descobriu **como escolher `methods`** (Pearson/Spearman)? Onde?

### Bloco 3 — Lacunas

11. Que informação estava no OPENAPI mas faltava no DTO? (assimetria)
12. Que informação você precisou e **não estava em lugar nenhum**?
13. Qual endpoint você tentou usar e **não existe**? (gap)
14. Que erro 4xx/5xx você recebeu e o que ele te disse?
15. Quanto tempo você economizaria se houvesse **1 exemplo curl** para cada endpoint?

### Bloco 4 — Veredicto

16. Em 1 frase: o que te deu mais confiança?
17. Em 1 frase: o que te deu menos confiança?
18. Em 1 frase: o que **faltou**?

---

## Critérios de sucesso

| Critério | Métrica |
|----------|---------|
| Tempo para 1ª chamada | < 20 min desde o início |
| Sucesso na autenticação | 100% descobrem sozinhos (header `Authorization: Bearer`) |
| Sucesso no pipeline run | 100% acham `POST /api/v1/knowledge/pipelines/run` |
| Sucesso no replay | ≥ 80% acham `POST /api/v1/knowledge/research/sessions/{id}/replay` |
| Compreensão do envelope | 100% entendem `{success, data, error, meta}` |
| Lidam com `error` | 100% verificam `success === true` antes de ler `data` |

---

## Template de relatório

```
# Validation 4 — Sessão #___

Data: ____
Desenvolvedor: ____ (linguagem: ____, senioridade: ____)
Duração total: ____ min

## Tempo até 1ª chamada HTTP
- ___ min

## Endpoints que ele tentou usar errado (se houver)
1. Tentou ___ → deveria ser ___
2.

## Dúvidas principais (verbatim, na ordem)
1. "..."
2. "..."
3.
4.
5.

## Gaps de documentação
1. Falta ___ no OPENAPI
2. Falta ___ nos DTOs
3. Falta exemplo de ___

## Erros HTTP que ele recebeu
- 401: ___ vezes
- 403: ___ vezes
- 404: ___ vezes
- 422: ___ vezes
- 500: ___ vezes

## O que deu mais confiança (verbatim)
- "..."

## O que deu menos confiança (verbatim)
- "..."

## O que faltou (verbatim)
- "..."

## Veredicto
- [ ] 🟢 conseguiu integrar em < 30 min
- [ ] 🟡 conseguiu integrar em 30–60 min com esforço
- [ ] 🔴 não conseguiu em 60 min

## Próxima ação
```

---

## O que NÃO fazer

- **NÃO** dar dicas durante os 50 minutos
- **NÃO** apontar para documentação adicional
- **NÃO** validar o nome do endpoint antes dele tentar
- **NÃO** corrigir erros de autenticação (deixe ele descobrir)

---

## Quando considerar aprovado

A validação de developer está aprovada quando, em **3 sessões consecutivas** com devs diferentes:

1. 100% conseguem fazer a 1ª chamada em < 20 min
2. 100% entendem o envelope sem ajuda
3. ≥ 80% completam o pipeline + replay em < 60 min
4. ≥ 80% conseguem descobrir autenticação lendo o YAML
5. Lacunas documentadas são **as mesmas** em ≥ 2 sessões (não ruído)

---

*Ver também: `RC1_DEMO_SCRIPT.md`, `CLINICAL_VALIDATION.md`, `RESEARCH_VALIDATION.md`, `INVESTOR_VALIDATION.md`.*