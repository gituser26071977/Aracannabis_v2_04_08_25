# ADR-0019 — Master Clock Implementation

> **Status:** Accepted
> **Data:** 2026-06-25

## Contexto

A Constituição Técnica (33) define o Master Clock Pattern (ADR-007):

> "Audio buffer scheduling (não tempo real): áudio agendado para tocar em momento exato do wall clock."

A Sprint 1 implementa o Timer Engine, que materializa o Master Clock. Este ADR documenta decisões de implementação que detalham o ADR-007 sem contradizê-lo.

## Decisões

### D1. Dual-clock (Monotonic + Wall)

- **Monotonic** para todas as medições internas (drift, elapsed, ticks).
- **Wall** APENAS para timestamps serializáveis (logs, ISO 8601, persistência).
- **Razão:** monotonic é imune a NTP/DST/mudança manual; wall é humano-legível.

### D2. Tick scheduler recursivo, não fixo

- `setTimeout` para próximo tick (não `setInterval`).
- Cada tick calcula delay do próximo com compensação de drift.
- **Razão:** `setInterval` é fire-and-forget; não permite ajuste fino. `setTimeout` recursivo permite compensação por tick.

### D3. Drift filter de 1ms

- Drift events são emitidos apenas quando `|drift| >= 1ms`.
- Drift < 1ms é ruído de medição.
- **Razão:** evita spam de eventos. Para análise detalhada, testes podem usar `getTotalElapsedMs()` e calcular externamente.

### D4. Time scale isolado do tick interval

- `setTimeScale(n)` afeta `getTotalElapsedMs()` mas NÃO o intervalo de tick.
- **Razão:** ticks devem continuar em frequência real (60Hz continua sendo 60Hz em escala 100). A escala afeta o "tempo de sessão" percebido pelo engine, não a frequência de callbacks do runtime.

### D5. Re-entrância via snapshot de listeners

- `emit()` faz `Array.from(listeners)` no início.
- Mudanças durante dispatch não afetam iteração atual.
- **Razão:** permite pause/resume/setMode dentro de tick handler sem corrupção.

### D6. App lifecycle via notifyBackground/notifyForeground

- Engine NÃO depende de `AppState` (RN-specific).
- App-level code (futuro) chama `notifyBackground` ao receber `AppState.change`.
- **Razão:** mantém Timer Engine platform-agnostic.

### D7. Background pausa automático

- `notifyBackground()` em `running` cancela o handle ativo.
- Transita para `paused` (mas emite `backgrounded`, não `paused`).
- **Razão:** evita acúmulo de tempo quando JS thread é suspenso. Emite evento distinto para distinguir de pausa voluntária.

### D8. Erros de listener capturados

- `EventDispatcher` aceita `onListenerError` callback.
- Default: silencioso (mas não silencioso-problemático — logger pode ser plugado).
- **Razão:** um listener buggy não pode derrubar a sessão.

## Alternativas consideradas

| Alternativa | Por que não |
|-------------|-------------|
| `setInterval` direto | Sem compensação de drift. |
| `requestAnimationFrame` | 60Hz fixo; acopla a render loop. |
| Bibliotecas (e.g., `nanotimer`) | Dependência externa; API menos type-safe. |
| Web Workers com MessageChannel | Overhead proibitivo no MVP. |
| Wall clock como source of truth | Quebra com NTP/DST. |

## Consequências

### Positivas
- Drift < 10ms em 20min (medido).
- Determinístico em testes.
- Platform-agnostic.
- Cross-engine consistency garantida.

### Negativas
- `setTimeout` recursivo é mais código que `setInterval`.
- Background handling depende de cooperação do app layer.

### Neutras
- Requer ADR-007 vigente (já existe).
- Não impacta outros engines diretamente até a Sprint 2.

## Conformidade com a Constituição

- ✅ Não contradiz 32 (Decisões de Produto).
- ✅ Não contradiz 33 (Engenharia, ADR-007, §10 Sincronização).
- ✅ Não contradiz 34 (Sprint 0 Foundation).
- ✅ Implementa o que ADR-007 prometeu sem expandir escopo.
