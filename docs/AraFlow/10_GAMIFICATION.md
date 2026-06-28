# AraFlow — Gamificação

> **Versão:** 0.1.0
> **Data:** 2026-06-24
> **Owner:** Product Owner + UX Designer
>
> A gamificação do AraFlow é **intencionalmente leve, ética e centrada em saúde**. Não busca engajamento artificial; busca **construir hábito terapêutico** e **reforçar autocuidado** sem manipular o usuário.

---

## Sumário

1. Princípios éticos
2. Tipos de motivação
3. Mecânicas propostas
4. Sistema de sequência (streak)
5. Conquistas
6. Marcos pessoais
7. Níveis e jornada
8. Recompensas intrínsecas
9. Recompensas extrínsecas (limitadas)
10. Personalização da gamificação
11. Pop-ups e microinterações
12. Compartilhamento social
13. Gamificação para profissionais
14. Anti-patterns (o que evitar)
15. Métricas
16. Acessibilidade
17. Roadmap

---

## 1. Princípios éticos

| Princípio | Significado |
|-----------|-------------|
| **Não manipular** | Nada de dark patterns, urgência falsa, medo. |
| **Não infantilizar** | Adulto não é criança. |
| **Não substituir** | Reforça hábito; não é fim em si mesmo. |
| **Sempre opcional** | Usuário pode desligar tudo. |
| **Progresso, não perfeição** | Falhas não geram punição. |
| **Intrínseco sobre extrínseco** | Conquistas pessoais > pontos genéricos. |
| **Transparente** | Nada de "game loops" ocultos. |

---

## 2. Tipos de motivação

A gamificação do AraFlow equilibra três动机 (motivações), conforme teoria de autodeterminação:

| Motivação | Como aplicamos |
|----------|----------------|
| **Autonomia** | Usuário escolhe objetivo, ritmo, lembrete. |
| **Competência** | Marcos que mostram progresso. |
| **Conexão** | Compartilhar com profissional / comunidade (opcional). |

---

## 3. Mecânicas propostas

### 3.1 Inventário

| Mecânica | MVP | Fase 2 | Fase 3 |
|----------|-----|--------|--------|
| Streak (dias consecutivos) | ✅ | ✅ | ✅ |
| Sessões concluídas | ✅ | ✅ | ✅ |
| Tempo total acumulado | ✅ | ✅ | ✅ |
| Conquistas | ✅ | ✅ | ✅ |
| Marcos pessoais | ✅ | ✅ | ✅ |
| Níveis | — | ✅ | ✅ |
| Missões semanais | — | ✅ | ✅ |
| Avatar/planta que cresce | — | ✅ | ✅ |
| Pontos (XP) | — | ✅ | ✅ |
| Ranking entre amigos | — | — | ✅ |
| Desafios globais | — | — | ✅ |
| Recompensas reais | — | — | ⚠ Com cuidado |

---

## 4. Sistema de sequência (streak)

### 4.1 Regra

- Streak = dias consecutivos com **≥ 1 sessão concluída**.
- **Zerar** após 24h sem sessão (com tolerância de 4h).

### 4.2 Visual

```
🔥 7 dias seguidos
```

### 4.3 Marcos de streak

| Marco | Recompensa visual |
|-------|-------------------|
| 3 dias | Mensagem calorosa + cor destacada |
| 7 dias | Conquista "Primeira semana" |
| 14 dias | Conquista "Duas semanas" |
| 30 dias | Conquista "Mês de cuidado" |
| 60 dias | Conquista "Persistência" |
| 100 dias | Conquista "Centenário" |
| 365 dias | Conquista "Um ano" |

### 4.4 Quebra de streak

- **Sem mensagem punitiva.**
- Mensagem: *"Tudo bem. Recomeçar é mais simples do que você imagina."*
- Convite direto: [Fazer uma sessão curta agora]

### 4.5 Modo "férias"

- Usuário pode pausar streak por até 14 dias (1x por trimestre).

---

## 5. Conquistas

### 5.1 Categorias

| Categoria | Exemplos |
|----------|---------|
| **Adesão** | "Primeira sessão", "10 sessões", "100 sessões" |
| **Diversidade** | "5 domínios diferentes", "Todas as categorias" |
| **Horário** | "Manhã cedo", "Antes de dormir" |
| **Duração** | "5 minutos sem parar", "20 minutos" |
| **Compartilhamento** | "Compartilhou com profissional" |
| **Bem-estar** | "Streak de 30 dias", "Voltou depois de pausa" |
| **Curiosidade** | "Experimentou todos os visuais" |

### 5.2 Visual

- Card com ícone + título + descrição.
- Cor de fundo varia por raridade:
  - Comum: `neutral-100`
  - Rara: `primary-50`
  - Épica: `energy-100`
  - Lendária: `info-100`

### 5.3 Notificação ao desbloquear

- Toast discreto: "Conquista desbloqueada".
- Não bloqueia fluxo.

---

## 6. Marcos pessoais

São **marcos individuais**, não genéricos:

- "Maior sequência: X dias"
- "Total de minutos: Y"
- "Categoria mais usada: Z"
- "Dia da semana preferido"
- "Horário mais frequente"

São exibidos em **relatório simples**, sem gamificação agressiva.

---

## 7. Níveis e jornada

### 7.1 Níveis (Fase 2)

| Nível | Nome | XP necessário |
|-------|------|---------------|
| 1 | Semente | 0 |
| 2 | Broto | 100 |
| 3 | Raiz | 300 |
| 4 | Folha | 700 |
| 5 | Flor | 1500 |
| 6 | Fruto | 3000 |
| 7 | Árvore | 6000 |

### 7.2 Visual

- Avatar/planta que cresce com XP.
- Tema: jardinagem terapêutica (não competição).

---

## 8. Recompensas intrínsecas

| Recompensa | Implementação |
|------------|---------------|
| **Insight clínico** | "Sua ansiedade caiu 30% em 4 semanas." |
| **Padrão descoberto** | "Você dorme melhor nos dias que respira de manhã." |
| **Comemoração pessoal** | Mensagem carinhosa em marcos. |
| **Visual novo** | Liberar visual respiratório após N sessões. |
| **Tema de cor** | Liberar tema após N sessões. |

---

## 9. Recompensas extrínsecas (limitadas)

> ⚠ Recompensas extrínsecas devem ser **sempre em saúde, nunca monetárias**.

| Recompensa | Como |
|------------|------|
| **Conteúdo premium** | Libera narração avançada após 30 sessões. |
| **Modo especial** | Libera "modo profundo" após N sessões. |
| **Visual raro** | Libera "mandala dourada" após 100 sessões. |
| **Selo compartilhável** | Imagem para Instagram (sem competição). |

### 9.1 O que **NÃO** fazemos

- ❌ Vouchers / cupons / descontos.
- ❌ Ranking público.
- ❌ Compra de "vidas" ou "energias".
- ❌ Notificação "outros usuários estão avançando mais".

---

## 10. Personalização da gamificação

| Preferência | Configuração |
|-------------|--------------|
| Gamificação geral | Ativada (padrão) / Desativada |
| Streak | Visível / Oculto |
| Conquistas | Com som / Sem som |
| Marcos | Mostrados / Ocultos |
| Nível | Mostrado / Oculto |

---

## 11. Pop-ups e microinterações

### 11.1 Regras gerais

- Máximo **1 pop-up** por sessão.
- Sempre dispensável.
- Tempo de leitura mínimo: 2s.

### 11.2 Tipos permitidos

- Toast (curto, no topo).
- Card inline (sem interromper).
- Modal apenas para ações críticas.

### 11.3 Tipos proibidos

- Modal que bloqueia primeira sessão.
- Banner permanente que pede interação.
- Notificação com contagem regressiva falsa.

---

## 12. Compartilhamento social

### 12.1 O que pode ser compartilhado

- Selo pessoal (imagem estática).
- Relatório semanal resumido.
- Conquista específica.

### 12.2 O que **não** é compartilhado

- Detalhes da sessão (técnica).
- Escalas clínicas brutas.
- Localização.
- Identificação além do nickname.

### 12.3 Onde

- Stories do Instagram (imagem).
- WhatsApp (link).
- Cópia para área de transferência.

---

## 13. Gamificação para profissionais

Profissionais têm **mecânicas próprias**, sem competição com pacientes:

| Mecânica | Uso |
|----------|-----|
| Pacientes ativos | Contador simples |
| Taxa de adesão média | Métrica acompanhada |
| Pacientes com desfecho positivo | Conquista clínica |
| Educação continuada | Recompensa em certificados |
| Protocolos criados | Métrica interna |

---

## 14. Anti-patterns (o que evitar)

| Anti-pattern | Por que evitar |
|--------------|----------------|
| **Streak "quebra tudo"** | Cria culpa e abandono. |
| **Daily reward com timer** | Manipulação. |
| **Notificação "seus amigos avançaram"** | Comparação tóxica. |
| **Gastar energia em algo** | Stress desnecessário. |
| **Loops infinitos** | Esgotamento. |
| **Recompensas monetárias por uso** | Confusão de papéis. |
| **Nomes infantilizados** | Idosos e adultos não aceitam. |
| **Streak de login (sem prática)** | Gamificação vazia. |

---

## 15. Métricas

### 15.1 Métricas de gamificação

| Métrica | Meta |
|---------|------|
| Streak médio entre ativos | ≥ 14 dias |
| Taxa de retorno após quebra de streak | ≥ 50% |
| Conquistas desbloqueadas por usuário ativo (média) | ≥ 3 |
| Usuários com gamificação ativada | ≥ 70% |
| Configurações "desativar gamificação" | < 5% |

### 15.2 Sinais de alerta

| Sinal | Investigar |
|-------|------------|
| Cancelamento logo após streak quebrar | UX está punindo. |
| Streak muito longo + cancelamento súbito | Esgotamento. |
| Gamificação desativada por muitos | Modelo errado. |
| Streak médio muito baixo | Onboarding fraco. |

---

## 16. Acessibilidade

- Texto alternativo em todos os ícones de conquista.
- Conquistas não dependem exclusivamente de cor.
- Streak tem versão textual ("7 dias seguidos" + ícone).
- Sem áudio obrigatório.

---

## 17. Roadmap

| Fase | Entregas |
|------|----------|
| **MVP** | Streak, conquistas básicas, marcos pessoais, mensagens calorosas. |
| **Fase 2** | Níveis, planta que cresce, missões semanais, insights. |
| **Fase 3** | Avatar customizável, ranking entre amigos (opt-in), desafios sazonais. |

---

*A gamificação é instrumento, não fim. Cuidado genuíno é o que retém usuários.*