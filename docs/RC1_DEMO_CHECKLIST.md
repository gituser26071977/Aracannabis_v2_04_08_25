# RC1 Demo Checklist

> Use este checklist **antes**, **durante** e **depois** de cada demonstração do AraOS Knowledge Engine.
> Item não-marcado = demo abortada.

---

## ANTES (T-30 min)

### Ambiente

- [ ] URL da página carrega (`https://app.arapath.com.br/clinical-pipeline`)
- [ ] URL com Demo Mode funciona (`?demo=1` no final)
- [ ] Navegador atualizado (Chrome ≥ 120 ou Edge ≥ 120)
- [ ] Aba única; sem extensões interferindo (desativar bloqueador, dark reader, tradutor)
- [ ] Tela cheia habilitada (`F11`)
- [ ] Resolução ≥ 1440×900
- [ ] Som do navegador funcional (caso queira narrar o replay)
- [ ] Plano de fundo do navegador: claro ou neutro (não escuro)
- [ ] Zoom do navegador em 100%

### Conteúdo

- [ ] Demo Mode renderiza pipeline automaticamente (cards preenchidos em < 1 s)
- [ ] Card **"Quem é o paciente?"** mostra `patient_demo_a1`
- [ ] Card **"O pipeline executou?"** mostra duração < 5 s
- [ ] Card **"O genome foi criado?"** mostra contagens
- [ ] Card **"Quais correlações foram encontradas?"** mostra top 5
- [ ] Card **"Quais hipóteses surgiram?"** mostra top 3
- [ ] Card **"O grafo foi persistido?"** mostra nós + arestas
- [ ] Card **"O replay reproduz exatamente o mesmo estado?"** mostra chip verde
- [ ] Timeline rail mostra ≥ 6 entradas com timestamps

### Conexão / Rede

- [ ] Internet do local da demo confirmada (testar em `https://example.com`)
- [ ] Fallback de rede: vídeo gravado em `/docs/demo-backup.mp4` acessível
- [ ] Plano B: se a página cair, abrir o vídeo e terminar o roteiro verbalmente

### Material físico

- [ ] Mouse externo sem fio (não usar trackpad se possível)
- [ ] Cabo HDMI testado (caso seja em projetor)
- [ ] Microfone de lapela (se audiência > 5 pessoas)

### Público

- [ ] Confirmar nome + perfil de cada pessoa (médico / pesquisador / investidor / dev)
- [ ] Confirmar se posso gravar a sessão (termo de consentimento)
- [ ] Identificar quem é o **decisor** na audiência

### Demoer

- [ ] Leu `RC1_DEMO_SCRIPT.md` há menos de 24 h
- [ ] Decorou as 8 falas-modelo (não decorou a arquitetura)
- [ ] Reviu a resposta para "isso é IA diagnóstica?" → **"não, é organização de padrões sob regras versionadas"**
- [ ] Levou garrafa de água
- [ ] Celular no silencioso

---

## DURANTE (T+0 min)

### Abertura (T+0:00 — T+0:30)

- [ ] Entregar o mouse ao espectador principal
- [ ] Dizer: *"Vou abrir uma página e deixá-la contar o que ela faz. Em cinco minutos vocês vão ver um pipeline clínico completo rodar."*
- [ ] **NÃO** falar mais nada

### Silêncio absoluto (T+0:30 — T+5:00)

- [ ] Não interromper o espectador enquanto ele explora
- [ ] Se ele perguntar algo, responder: *"Vamos olhar mais. Conversamos depois."*
- [ ] Observar:
  - [ ] Qual card ele lê primeiro
  - [ ] Onde ele trava
  - [ ] Se ele volta para reler algum card
  - [ ] Se ele tenta clicar em algo (Replay, Graph)
  - [ ] Se ele pede para rolar a página

### Fechamento (T+5:00)

- [ ] Pedir a frase-modelo: *"Em suas palavras, o que essa empresa faz?"*
- [ ] Anotar a resposta **verbatim** no relatório da sessão
- [ ] Agradecer e abrir para perguntas
- [ ] **NÃO** falar de arquitetura a menos que perguntado diretamente
- [ ] Se perguntarem de arquitetura: *"Posso mostrar em outro momento. Agora estamos vendo o produto."*

---

## DEPOIS (T+5 min — T+30 min)

### Anotar imediatamente

- [ ] Quem estava na sala (lista nominal)
- [ ] Tempo de compreensão (até 1 min / 1–3 min / 3–5 min / mais de 5 min)
- [ ] Primeira pergunta feita pelo espectador (verbatim)
- [ ] Última frase do espectador sobre o produto (verbatim)
- [ ] Dúvidas que surgiram (lista)
- [ ] Confusões observadas (lista)

### Classificar

- [ ] 🟢 entendeu sem ajuda
- [ ] 🟡 entendeu com 1 dica
- [ ] 🔴 não entendeu

### Ações pós-demo

- [ ] Salvar relatório no diretório `docs/validation-sessions/yyyy-mm-dd-<perfil>.md`
- [ ] Atualizar a matriz de validação em `docs/RC1_VALIDATION_MATRIX.md` (criar se não existir)
- [ ] Se 🟡 ou 🔴: registrar sugestão em `POST_RC1_REFACTOR.md` (se estrutural) ou ajustar microcopy (se textual)

---

## Se algo der errado durante a demo

| Sintoma | Ação |
|---------|------|
| Página não carrega | Trocar para `?demo=1` (não precisa backend) |
| Demo Mode não dispara | Recarregar com Ctrl+Shift+R (hard refresh) |
| Graph não renderiza | Clicar em "Fit View" no canto inferior direito do React Flow |
| Replay demora | Esperar até 5 s; se passar, abrir `POST_RC1_REFACTOR.md` para diagnóstico |
| Visitante pergunta sobre HIPAA/LGPD | Responder: *"compliance regulatório foi desenhado desde o ADR-0006, não improvisado"*. Se não souber, marcar follow-up |
| Visitante pede para ver código | Oferecer: *"posso te enviar o OPENAPI.yaml agora"* (não mostrar código-fonte) |
| Visitante quer testar | Abrir uma nova aba anônima e enviar a URL `?demo=1` |

---

## Resumo visual

```
┌─────────────────────────────────────────────────────────┐
│ ANTES:    ambiente OK · demo OK · rede OK · público OK │
│ DURANTE:  5 min de silêncio · anotar observações        │
│ DEPOIS:   classificar · salvar · registrar sugestão     │
└─────────────────────────────────────────────────────────┘
```

---

*Ver também: `RC1_DEMO_SCRIPT.md`, `CLINICAL_VALIDATION.md`, `RESEARCH_VALIDATION.md`, `INVESTOR_VALIDATION.md`, `DEVELOPER_VALIDATION.md`, `POST_RC1_REFACTOR.md`.*