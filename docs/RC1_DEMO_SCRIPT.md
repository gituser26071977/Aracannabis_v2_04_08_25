# RC1 Demo Script — 5 minutos

> Roteiro oficial da primeira demonstração pública do **AraOS Clinical Intelligence — Knowledge Engine**.
> Acompanha o demoer. Cada etapa tem objetivo, mensagem principal, ação na interface, resultado esperado e duração estimada.
> **Tempo total: 5 minutos.**

---

## 0. Antes de começar (30 s — antes de abrir a tela)

> Dizer uma única frase:

> *"Vou abrir a página e deixá-la contar o que ela faz. Em cinco minutos vocês vão ver um pipeline clínico completo rodar, explicar o que encontrou e provar que o resultado é reproduzível."*

Nada mais. Sem slides. Sem apresentação prévia. Sem introdução sobre arquitetura.

---

## 1. Paciente (20 s)

| Item | Conteúdo |
|------|----------|
| **Objetivo** | Mostrar quem está sendo analisado |
| **Mensagem** | "Tudo começa com um paciente e uma janela de tempo" |
| **Ação** | Apontar para o card **"Quem é o paciente?"** |
| **Resultado esperado** | Identificador do paciente + janela inicial → final (já preenchidos pelo Demo Mode) |
| **Duração** | 20 s |

> Frase-modelo para o demoer:
>
> *"Aqui está o paciente que estamos analisando — um identificador, uma janela de tempo. Nada de prontuário aberto, nada de PHI exposto."*

---

## 2. Pipeline (20 s)

| Item | Conteúdo |
|------|----------|
| **Objetivo** | Mostrar que o sistema processou a janela |
| **Mensagem** | "O AraOS processou a janela inteira em uma única execução reprodutível" |
| **Ação** | Apontar para o card **"O pipeline executou?"** |
| **Resultado esperado** | Duração em ms + identificador da requisição + trilha de correlação |
| **Duração** | 20 s |

> Frase-modelo:
>
> *"Esse card diz: a execução terminou em X milissegundos, com estes identificadores. Cada execução tem um ID — você consegue voltar nela e auditar."*

---

## 3. Genome (30 s)

| Item | Conteúdo |
|------|----------|
| **Objetivo** | Mostrar que o pipeline produziu uma representação estruturada |
| **Mensagem** | "Toda a informação do paciente virou um **genome** — uma representação determinística com hash" |
| **Ação** | Apontar para o card **"O genome foi criado?"** |
| **Resultado esperado** | Nº de genes / correlações / hipóteses + `state_hash` + identificador URN |
| **Duração** | 30 s |

> Frase-modelo:
>
> *"O genome é a fotografia do paciente sob a ótica do AraOS. Os números — quantos genes, quantas correlações, quantas hipóteses — vêm junto. E tem um hash: se você rodar de novo, vai dar o mesmo."*

---

## 4. Correlações (45 s)

| Item | Conteúdo |
|------|----------|
| **Objetivo** | Mostrar padrões quantitativos encontrados |
| **Mensagem** | "Aqui estão os pares de genes que mais se movem juntos neste paciente" |
| **Ação** | Apontar para o card **"Quais correlações foram encontradas?"** |
| **Resultado esperado** | Total de correlações + ρ máximo + ρ médio + top 5 (par de genes × coeficiente × método) |
| **Duração** | 45 s |

> Frase-modelo:
>
> *"Oito correlações encontradas. A mais forte é -0.82: quanto maior a latência do sono, menor o arousal autonômico. Pearson. Tem 91% de confiança. Não é opinião — é estatística bruta."*

---

## 5. Hipóteses (45 s)

| Item | Conteúdo |
|------|----------|
| **Objetivo** | Mostrar afirmações geradas a partir das correlações |
| **Mensagem** | "As correlações alimentam regras versionadas que produzem afirmações verificáveis" |
| **Ação** | Apontar para o card **"Quais hipóteses surgiram?"** |
| **Resultado esperado** | Total de hipóteses + confiança máxima + top 3 (afirmação textual + barra de confiança + genes que apoiam) |
| **Duração** | 45 s |

> Frase-modelo:
>
> *"Três hipóteses. A mais forte diz: latência do sono elevada está associada a hiperarousal autonômico. O AraOS não diagnostica — ele organiza padrões com base em regras versionadas e auditáveis."*

---

## 6. Knowledge Graph (45 s)

| Item | Conteúdo |
|------|----------|
| **Objetivo** | Mostrar visualização do conhecimento como rede |
| **Mensagem** | "O mesmo conhecimento, visto como grafo" |
| **Ação** | Apontar para o card **"O grafo foi persistido?"** |
| **Resultado esperado** | 12 nós em círculo + 13 arestas (espessura = peso) + `state_hash` do grafo |
| **Duração** | 45 s |

> Frase-modelo:
>
> *"Aqui o mesmo conhecimento virou grafo. Cada nó é um gene, cada linha é uma relação. A espessura da linha diz o peso. Dá pra dar zoom, dar pan, clicar — mas não dá pra editar. É leitura, não escrita."*

---

## 7. Replay (30 s)

| Item | Conteúdo |
|------|----------|
| **Objetivo** | Provar que o estado é reproduzível |
| **Mensagem** | "Vamos rodar o replay — o sistema reconstrói o estado e compara o hash" |
| **Ação** | No card **"O replay reproduz exatamente o mesmo estado?"**, clicar **"Executar Replay"** (já pré-selecionado) |
| **Resultado esperado** | Chip verde: *"Replay OK · state_hash idêntico"* |
| **Duração** | 30 s |

> Frase-modelo:
>
> *"Replay OK. O sistema reconstruiu tudo a partir do log e o hash é idêntico. Isso é reprodutibilidade determinística."*

---

## 8. Conclusão (30 s)

| Item | Conteúdo |
|------|----------|
| **Objetivo** | Fechar a demonstração |
| **Mensagem** | "Oito cards. Um fluxo. Reprodutível." |
| **Ação** | Olhar para o conjunto da página e dizer: |
| **Resultado esperado** | Silêncio respeitoso |
| **Duração** | 30 s |

> Frase-modelo (escolher uma):
>
> *"Em cinco minutos vocês viram um pipeline clínico rodar, encontrar correlações, formular hipóteses, persistir um grafo e provar que tudo é reproduzível. Esse é o produto."*
>
> **OU**
>
> *"Um pipeline reprodutível que transforma histórico clínico em conhecimento auditável. Essa é a proposta do AraOS."*

---

## Modo de ativação do Demo Mode

- URL com flag `?demo=1` — exemplo: `https://app.arapath.com.br/clinical-pipeline?demo=1`
- A página se hidrata automaticamente com paciente exemplo
- Não toca o backend
- Não persiste nada
- Banner superior indica o modo e oferece botão **"Sair do demo"**

## Notas para o demoer

- **Não** explicar a arquitetura. **Não** falar de DDD, Event Sourcing, bitemporalidade, Content-Derived IDs, ADR-0006.
- **Não** falar de SQL, PostgreSQL, migrations.
- **Pode** falar de: paciente, janela, correlações, hipóteses, grafo, replay, hash, reprodutibilidade.
- Se alguém perguntar sobre arquitetura: *"posso te mostrar em outra hora; agora estamos olhando o produto."*
- Se alguém perguntar se o resultado é diagnóstico: *"não. é organização de padrões sob regras versionadas."*

## Checklist final (RC1_DEMO_CHECKLIST.md)

Use o checklist de pré/durante/pós-demo junto a este roteiro.