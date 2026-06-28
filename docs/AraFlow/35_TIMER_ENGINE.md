# AraFlow — Timer Engine

> **Versão:** 1.0.0
> **Data:** 2026-06-25
> **Sprint:** 1 — Foundation Implementation
> **Status:** Implementado, testado, congelado.

---

## Sumário

1. Visão geral
2. Onde mora
3. Arquitetura em camadas
4. Componentes
5. Fluxo de uma sessão
6. Máquina de estados
7. Eventos
8. Modos de operação
9. Drift correction
10. Background / Foreground
11. Time scaling
12. Pontos de extensão
13. Limitações
14. Reuso em outras plataformas
15. Performance
16. Referências

---

## 1. Visão geral

O **Timer Engine** é o relógio mestre da plataforma AraFlow. Toda medição de tempo DEVE passar por ele. Nenhum outro engine (Breath, Audio, Animation, Session) instancia `setTimeout`/`setInterval` próprios.

**Por que centralizar?**

1. **Drift único.** Um único algoritmo de compensação; bugs e melhorias beneficiam todos os engines.
2. **Determinismo testável.** Toda lógica temporal é testável com FakeClockProvider sem mock de Jest.
3. **Sincronização implícita.** Audio, Animation e Breath convergem no mesmo relógio.
4. **Cross-platform.** Reutilizável em Mobile, Web, Desktop, Wearables e AraOS.

**Princípios:**

- Zero dependência de UI, React, React Native.
- 100% determinístico dado mesmo ClockProvider e MonotonicClock.
- Re-entrante: chamar pause() dentro de um listener é seguro.
- Erros em listeners não interrompem dispatch para outros.

---

## 2. Onde mora

```
mobile/src/core/timer-engine/
├── domain/                    # Tipos puros
│   ├── MonotonicClock.ts
│   ├── WallClock.ts
│   ├── ClockHandle.ts
│   ├── ClockProvider.ts
│   ├── TimerMode.ts
│   ├── TimerState.ts
│   ├── DriftMeasurement.ts
│   ├── TimerEvent.ts
│   ├── TimeScale.ts
│   ├── Listener.ts
│   └── index.ts
├── application/               # Orquestração
│   ├── EventEmitter.ts
│   ├── DriftCorrector.ts
│   ├── TimerEngine.ts
│   └── index.ts
└── infrastructure/            # Adaptadores
    ├── BrowserMonotonicClock.ts
    ├── BrowserWallClock.ts
    ├── DefaultClockProvider.ts
    └── index.ts
```

E o ponto de entrada público:

```
mobile/src/core/timer-engine/index.ts
```

---

## 3. Arquitetura em camadas

```
┌─────────────────────────────────────────┐
│             APPLICATION                 │
│                                          │
│   TimerEngine  ───  DriftCorrector       │
│        │              │                  │
│        │              ▼                  │
│        │         (strategy)               │
│        ▼                                   │
│   EventDispatcher (re-entrância)          │
│                                          │
└──────────────┬──────────────────────────┘
               │ depende apenas de DOMAIN
               ▼
┌─────────────────────────────────────────┐
│               DOMAIN                     │
│                                          │
│   MonotonicClock  WallClock              │
│   ClockProvider   ClockHandle            │
│   TimerMode       TimerState             │
│   TimerEvent      DriftMeasurement       │
│                                          │
│   (zero deps, zero I/O)                  │
│                                          │
└──────────────▲──────────────────────────┘
               │ implementa
┌──────────────┴──────────────────────────┐
│           INFRASTRUCTURE                │
│                                          │
│   BrowserMonotonicClock (perf.now)      │
│   BrowserWallClock (Date.now)           │
│   DefaultClockProvider (setTimeout)     │
│                                          │
└─────────────────────────────────────────┘
```

**Regras de dependência (Clean Architecture):**

- `domain` não importa nada.
- `application` importa apenas `domain`.
- `infrastructure` importa apenas `domain` (para implementar interfaces).
- `application` e `infrastructure` NUNCA se importam mutuamente.

---

## 4. Componentes

### 4.1 MonotonicClock

Relógio cuja progressão é estritamente não-decrescente. Imune a NTP, DST, mudanças manuais.

**Implementação produção:** `performance.now()` (compatível com RN 0.74+, browsers, Node 16+, Bun, Deno).

### 4.2 WallClock

Relógio civil correlacionado com tempo Unix. Usado APENAS para timestamps persistentes e exibição.

**Implementação produção:** `Date.now()` + `new Date().toISOString()`.

### 4.3 ClockProvider

Abstração sobre `setTimeout`/`setInterval`. Em produção, `DefaultClockProvider`; em testes, `FakeClockProvider` determinístico.

**Princípio:** se o engine precisa de tempo, vai pelo ClockProvider. Se um teste quer controle, injeta um fake.

### 4.4 EventDispatcher

Pub/sub type-safe. Características:

- Síncrono (dispatch imediato).
- Re-entrante (snapshot da lista no início do dispatch).
- Erros em listener não quebram engine.
- Suporta unsubscribe via função retornada.

### 4.5 DriftCorrector

Strategy pattern. Calcula o delay do próximo tick compensando drift acumulado.

**Algoritmo:**

```
drift = actualElapsed - (tickIndex * intervalMs)
nextDelay = clamp(intervalMs - drift, 1, 2*intervalMs)
```

Eventos `drift` são emitidos apenas quando `|drift| >= 1ms` (filtro de ruído).

### 4.6 TimerEngine

Orquestrador. Implementa a máquina de estados, tick scheduler, event dispatch. Ver Seção 6 para o state machine.

---

## 5. Fluxo de uma sessão

```
[User]                 [TimerEngine]               [ClockProvider]      [Listeners]
  │                          │                            │                   │
  │ start()                  │                            │                   │
  ├─────────────────────────►│                            │                   │
  │                          │ state: idle → running      │                   │
  │                          │ emit("started")            │                   │
  │                          ├───────────────────────────────────────────────►│
  │                          │ scheduleNextTick()         │                   │
  │                          ├───────────────────────────►│                   │
  │                          │                            │                   │
  │                          │   [delay]                  │                   │
  │                          │                            │                   │
  │                          │◄─────── tick callback ─────┤                   │
  │                          │ measure drift              │                   │
  │                          │ emit("tick")               │                   │
  │                          ├───────────────────────────────────────────────►│
  │                          │ reschedule with adjusted   │                   │
  │                          │ delay (drift compensation) │                   │
  │                          ├───────────────────────────►│                   │
  │                          │                            │                   │
  │ pause()                  │                            │                   │
  ├─────────────────────────►│                            │                   │
  │                          │ state: running → paused    │                   │
  │                          │ cancel active handle       │                   │
  │                          ├───────────────────────────►│                   │
  │                          │ emit("paused")             │                   │
  │                          ├───────────────────────────────────────────────►│
  │                          │                            │                   │
  │ resume()                 │                            │                   │
  ├─────────────────────────►│                            │                   │
  │                          │ state: paused → running    │                   │
  │                          │ emit("resumed")            │                   │
  │                          ├───────────────────────────────────────────────►│
  │                          │ scheduleNextTick()         │                   │
  │                          ├───────────────────────────►│                   │
  │                          │                            │                   │
  │ stop()                   │                            │                   │
  ├─────────────────────────►│                            │                   │
  │                          │ state: running → stopped   │                   │
  │                          │ emit("stopped")            │                   │
  │                          ├───────────────────────────────────────────────►│
```

---

## 6. Máquina de estados

```
                ┌─────────────┐
                │    idle     │◄─────────────┐
                └──────┬──────┘              │
                  start│                      │ reset
                       ▼                      │
                ┌─────────────┐               │
                │   running   │───────────────┤
                └─┬───────┬───┘               │
            pause│       │stop                │
                  ▼       ▼                    │
                ┌─────────────┐                │
                │   paused    │────stop──►┌─────────────┐
                └──────┬──────┘           │   stopped   │
                  resume│                  └──────┬──────┘
                       ▼                          │ reset
                ┌─────────────┐                  │
                │   running   │                  │
                └─────────────┘                  │
                       │                          │
                       └──────────────────────────┘
                              reset
```

**Invariantes:**

- `state === 'running'`  ⇔  `activeHandle !== null`
- `activeHandle === null` quando `state !== 'running'`
- `totalActiveMs` cresce APENAS em `running`
- `totalPausedMs` cresce APENAS em `paused`
- `totalBackgroundedMs` cresce durante `notifyBackground()` → `notifyForeground()`

**Transições inválidas lançam AppError:**

- `start()` de `paused` ou `stopped`
- `pause()` de `running` é no-op (não é erro, é apenas no-op)
- `resume()` de não-paused é no-op
- `stop()` de `idle` ou `stopped` é no-op

---

## 7. Eventos

| Evento | Quando | Payload |
|--------|--------|---------|
| `started` | Ao entrar em running | monotonicMs, wallIso, startMonotonicMs, startWallIso |
| `paused` | Ao pausar | totalElapsedMs, pausedAtMonotonicMs |
| `resumed` | Ao retomar de paused | totalElapsedMs, pausedForMs |
| `stopped` | Ao parar | totalElapsedMs, totalActiveMs |
| `reset` | Ao resetar | previousState |
| `tick` | A cada tick | tickIndex, elapsedMs, totalElapsedMs |
| `drift` | Quando drift >= 1ms | measurement (DriftMeasurement) |
| `mode-changed` | Ao trocar mode | previousMode, currentMode, tickIntervalMs |
| `backgrounded` | Ao receber notifyBackground | totalElapsedMs |
| `foregrounded` | Ao receber notifyForeground | totalElapsedMs, backgroundedForMs |
| `time-scale-changed` | Ao trocar timeScale | previousScale, currentScale |

**Garantias:**

- Eventos são DISPATCHED SÍNCRONOS.
- Listeners que modificam estado durante dispatch (ex.: pause de dentro de tick) são tratados corretamente.
- Erros em listener são logados e engolidos, não interrompem dispatch.

---

## 8. Modos de operação

| Modo | Intervalo | Uso | Custo |
|------|-----------|-----|-------|
| `high-precision` | 16.67ms (60Hz) | Animações, sync com áudio | Alto (CPU) |
| `balanced` | 100ms (10Hz) | Sessão de respiração padrão | Médio |
| `low-power` | 1000ms (1Hz) | Background tracking | Mínimo |

**Default:** `balanced`.

**Mudança de modo em runtime:** `engine.setMode('high-precision')`. Não invalida sessão atual; próximo tick usa novo intervalo.

---

## 9. Drift correction

**Definição:** diferença entre tempo esperado (intervalMs * tickIndex) e tempo real decorrido.

**Modelo matemático:**

```
expected = tickIndex * intervalMs
actual   = monotonicNow() - sessionStartedAt
drift    = actual - expected
```

**Compensação:**

```
nextDelay = clamp(intervalMs - drift, 1, intervalMs * 2)
```

**Por que clamps:**

- Mínimo 1ms: garante que o callback eventualmente execute.
- Máximo 2×interval: previne "burst" de ticks quando o runtime volta de background.

**Limitação:** drift só pode ser compensado FRENTE (catch-up). Se o runtime atrasar tanto que ultrapasse `expected + 2*interval`, o engine emite `foregrounded` event e zera.

**Resultado medido (ver Sprint Report):** drift acumulado < 10ms em sessão de 20 minutos com FakeClockProvider. Em runtime real, deriva do event loop impacta (ver §15).

---

## 10. Background / Foreground

**API:**

```typescript
engine.notifyBackground();  // chamado pelo AppState listener
engine.notifyForeground();
```

**Comportamento:**

1. `notifyBackground()` em `running`:
   - Cancela handle ativo.
   - Transita para `paused` (note: NÃO emite `paused`, emite `backgrounded`).
   - Acumula tempo ativo até o ponto.
2. `notifyForeground()` quando há background pendente:
   - Acumula tempo em background.
   - Transita para `running`.
   - Reseta `lastTickMonotonicMs` (evita catch-up inválido).
   - Emite `foregrounded` event.

**Por que separar `paused` e `backgrounded`:** permitem que o Session Engine distinga pausa voluntária (usuário parou para atender alguém) de pausa involuntária (app foi minimizado). Importante para LGPD analytics e safety.

---

## 11. Time scaling

**Propósito:** acelerar ou desacelerar o tempo de engine em relação ao tempo real. Usado por:

- Testes (scale=100 → 20min em 12s).
- Demos (scale=0.5 → relaxa sessão).
- Não usado em produção (sempre scale=1).

**API:**

```typescript
engine.setTimeScale(2.0);  // 1ms real = 2ms engine
```

**Validação:** `isValidTimeScale()` aceita apenas valores em `[0.001, 1000]`. Fora disso, `AppError`.

**Comportamento:**

- `getTotalElapsedMs()` retorna tempo de engine (real * scale).
- `getTotalPausedMs()` é o tempo PAUSADO em escala de engine.
- O tick interval NÃO escala; ticks continuam em tempo real.

---

## 12. Pontos de extensão

| Para customizar | Implemente |
|-----------------|------------|
| Relógio monotonic (ex.: precisão de hardware) | `MonotonicClock` |
| Relógio wall (ex.: mock para testes) | `WallClock` |
| Scheduler (ex.: foreground service no Android) | `ClockProvider` |
| Algoritmo de drift (ex.: Kalman filter) | `DriftCorrectionStrategy` |
| Listener de erro customizado | `onListenerError` em deps |

**Exemplo:** injetar `MonotonicClock` com precisão de sub-millisecond via `process.hrtime` no Node:

```typescript
import { performance } from 'perf_hooks';
const monotonic: MonotonicClock = { now: () => performance.now() };
```

**Exemplo:** trocar drift strategy:

```typescript
import { TimerEngine, type DriftCorrectionStrategy } from '@core/timer-engine';

const kalmanStrategy: DriftCorrectionStrategy = { ... };
const engine = new TimerEngine({
  monotonic, wall, clockProvider,
  // @ts-expect-error: future API
  driftStrategy: kalmanStrategy,
});
```

(Último exemplo requer ADR novo; não é API atual.)

---

## 13. Limitações

### 13.1 Conhecidas

1. **Drift em runtime real > drift em fake.** Em produção, event loop do JS é preempted por GC, paint, layout. Drift de 1-3ms é normal. Acima de 10ms indica problema no host (e.g., thread main bloqueado).

2. **`performance.now()` polyfill em RN.** Versões antigas do RN polyfillam. Se RN < 0.65, há degradação. O fallback para `Date.now()` no construtor cobre, mas o engine perde precisão.

3. **Background no Android.** Doze mode pode suspender o JS thread por minutos. `notifyBackground()` é essencial. Sem ele, `setTimeout` pode não acumular e o tempo "congela".

4. **Time scale não escala ticks.** O intervalo de tick NÃO escala; apenas o tempo medido. Isso significa que `scale=100` emite ticks em ~16ms real cada, mas o engine "pensa" que cada tick vale 1.6s de tempo de sessão.

### 13.2 Não-cobre

- **Persistência de estado:** após kill do app, o engine reseta. Persistência é responsabilidade do Session Engine (próximo sprint).
- **Sincronização com backend:** tempo local é source of truth durante sessão ativa. Sync é responsabilidade do Session Engine.
- **Wall-clock correction:** se o usuário muda o relógio do device, o WallClock reflete mas MonotonicClock não.

---

## 14. Reuso em outras plataformas

O Timer Engine é totalmente platform-agnostic. Reuso em:

| Plataforma | Como |
|------------|------|
| **Mobile (iOS/Android)** | Já integrado. `performance.now()` polyfilled pelo RN. |
| **Web (Browser)** | `performance.now()` nativo. Sem mudanças. |
| **Desktop (Electron/Tauri)** | `performance.now()` no main thread. Workers têm sua própria instância. |
| **Wearables (watchOS/Wear OS)** | `performance.now()` disponível. Verificar se Doze mode é simétrico. |
| **AraOS (Node.js backend)** | `performance.now()` no Node 16+. Para serviços de longa duração, considerar `process.hrtime.bigint()` se precisão sub-millisecond for crítica. |
| **Web Workers** | Importar mesma implementação; cada worker tem seu próprio `performance.now()`. |

**Requisito único:** `setTimeout`, `setInterval`, `performance.now()`, `Date.now()`, `Date.toISOString()`. Todos presentes em qualquer runtime JS 2026.

---

## 15. Performance

### 15.1 Benchmarks sintéticos (FakeClockProvider)

| Operação | Tempo |
|----------|-------|
| Inicialização | < 1ms |
| 20 min sessão simulada (12k ticks a 100ms) | < 500ms wall time |
| 60Hz x 60s (3600 ticks) | < 500ms wall time |
| Subscribe 1000 listeners | < 50ms |
| 1 tick com 1000 listeners | < 5ms |
| Re-entrant subscribe x 100 durante tick | < 100ms |

### 15.2 Benchmark real (setTimeout real, 30s sessão)

Em macOS M1, Node 20, modo `balanced` (100ms tick):

```
[BENCH — Real Time]
  Session:        30000ms
  Wall elapsed:   30045ms
  Mono elapsed:   30045.32ms
  Drift:          45.32ms (0.151%)
  Ticks emitted:  301
  Avg tick int:   99.85ms
  Min tick int:   96.12ms
  Max tick int:   112.45ms
  Engine elapsed: 30045.10ms
```

**Observações:**

- Drift < 1% é normal em runtime real (vs < 0.05% em fake).
- Tick jitter de 96-112ms (16ms amplitude) é dominado por GC e event loop.
- Em hardware mais antigo (e.g., Android entry-level), esperar drift de 2-3%.

### 15.3 Memory

- Heap delta após 10.000 ticks: < 1MB.
- Sem vazamento: `clock.activeHandleCount() === 0` após stop/reset (verificado em testes).
- 1000 listeners simultâneos: < 500KB heap adicional.

---

## 16. Referências

- Constitution: `docs/AraFlow/32_FINAL_PRODUCT_DECISIONS.md`
- Blueprint: `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md`
- Sprint 0 Foundation: `docs/AraFlow/34_SPRINT0_IMPLEMENTATION_REPORT.md`
- Sprint 1 Report: `docs/AraFlow/35_SPRINT1_TIMER_REPORT.md`
- ADR-019: `docs/adr/araflow/019-master-clock-implementation.md`
- W3C High Resolution Time: https://www.w3.org/TR/hr-time-3/
- ECMA-262 Timers: https://tc39.es/ecma262/#sec-timers
- MDN performance.now(): https://developer.mozilla.org/en-US/docs/Web/API/Performance/now

---

**Mantido por:** Chief Technology Officer (CTO)
**Última atualização:** 2026-06-25
**Próxima revisão:** após Sprint 2 (Breath Engine) para validar integração.
