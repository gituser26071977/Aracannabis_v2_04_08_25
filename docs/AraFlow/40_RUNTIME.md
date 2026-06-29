# 40 — AraFlow Runtime

**Sprint:** 4 — AraFlow Runtime Facade · **Status:** Implementado, testado,
congelado. · **Versão:** `@core/runtime@1.0.0`

---

## Propósito

O **AraFlow Runtime** é a **única API pública do Core**. É um Facade +
Orchestrator que embrulha os três engines frozen (Timer, Breath,
ProtocolRuntime) atrás de **12 métodos** e **um stream de eventos taggeado por
fonte**. Consumidores (mobile UI, backend jobs, integrações) **nunca tocam um
engine diretamente** — sempre passam pelo Runtime.

Ele existe para:

1. **Eliminar boilerplate** — o harness do Sprint 3.5 provou que integrar os 3
   engines exige ~50 linhas de wiring; centralizamos isso no Runtime.
2. **Fechar 9 ergonomic gaps** identificados na exploração do Sprint 3.5: estado
   `'errored'` inalcançável, pause-outlasts-plan silencioso, ausência de
   completion promise, agregação de eventos, etc.
3. **Padronizar superfícies** — uma única assinatura `subscribe(listener)`, um
   único `getState()`, uma única `getMetrics()`.
4. **Forçar ownership** — Runtime é dono do Timer, Breath e ProtocolRuntime. App
   chama `notifyBackground/notifyForeground` no Runtime, que fan-out.

---

## O que NÃO é

- ❌ Não é o Session Engine (próxima sprint após validação).
- ❌ Não é UI / React / React Native.
- ❌ Não é áudio / animação / persistência.
- ❌ Não é cliente de rede / backend.
- ❌ Não é analytics / safety / scoring.
- ❌ Não é reescrita dos engines — eles continuam frozen.

---

## Onde vive

```
mobile/src/core/runtime/
├── index.ts                          barrel público + RUNTIME_ENGINE_VERSION
├── application/
│   ├── RuntimeEngine.ts              Facade: 12 métodos
│   ├── RuntimeEngineDeps.ts          shape do construtor
│   └── RuntimeEventStream.ts         dispatcher taggeado + listener-error
├── domain/
│   ├── RuntimeState.ts               FSM de 10 estados
│   ├── RuntimeEvent.ts               union taggeado (4 fontes)
│   ├── RuntimeLifecycleEvent.ts      eventos emitidos pelo Runtime
│   ├── RuntimeSnapshot.ts            merged snapshot
│   └── RuntimeMetrics.ts             métricas agregadas
└── util/
    ├── aggregate-metrics.ts          puro: snapshot × plan × counters
    ├── plan-to-breath-config.ts      adaptador N-phase → 4-phase
    └── timer-like-adapter.ts         TimerEngine → TimerLike (15 linhas)
```

---

## API pública (12 métodos + 2 derivados)

```ts
import { RuntimeEngine, type RuntimeEngineDeps } from '@core/runtime';

const rt = new RuntimeEngine({ runtimeId: EngineId('app-1') });

// 1. Compile + load (conveniência)
const r1 = rt.compile(source); // Result<void, EngineError>

// 2. Load direto (se já tem plano)
const r2 = rt.loadProtocol(plan); // Result<void, EngineError>

// 3–7. Lifecycle
rt.start(); // Result<void, EngineError>
rt.pause();
rt.resume();
rt.cancel();
rt.dispose(); // terminal

// 8. Subscribe (uma assinatura, 4 fontes)
const unsub = rt.subscribe((event) => {
  /* ... */
});

// 9–12. Observation (read-only)
rt.getState(); // RuntimeState
rt.getMetrics(); // RuntimeMetrics
rt.getExecutionPlan(); // ProtocolExecutionPlan | null
rt.snapshot(); // RuntimeSnapshot (merged)
rt.getWarnings(); // readonly Failure[]

// AppState forwards
rt.notifyBackground();
rt.notifyForeground();
```

---

## Arquitetura

```
              Consumer (mobile UI / backend / integração)
                       │
                       ▼
           ┌────────────────────────┐
           │     RuntimeEngine      │
           │  (Facade + Orchestrator)│
           │  12 métodos, 1 stream   │
           └─────┬─────┬─────────┬───┘
                 │     │         │
                 │     │         │ owning &
                 │     │         │ bridging
                 ▼     ▼         ▼
       ┌──────────┐ ┌──────────────┐ ┌──────────────────────┐
       │Timer     │ │Breath        │ │ProtocolRuntime       │
       │Engine    │ │Engine        │ │(+ ProtocolCompiler)  │
       │(created) │ │(lazy)        │ │(created)             │
       └──────────┘ └──────────────┘ └──────────────────────┘
            ▲             │                   │
            │             └───── shares ──────┘ TimerLike (15-line adapter)
            │
       Shared Contracts
       (Result / EngineError / BreathPhase / EngineId / Failure)
```

**Pontos arquiteturais chave:**

- **Single public API.** Consumidores nunca importam `@core/timer-engine`,
  `@core/breath-engine` ou `@core/protocol-compiler` diretamente.
- **Lazy Breath Engine.** `createBreathEngine()` é chamado dentro de
  `loadProtocol` apenas quando há phases (cycles > 0). Plan com `cycles === 0`
  não cria breath engine.
- **3 engines → 1 stream.** Runtime assina timer e protocol no construtor;
  breath é assinado dentro de `loadProtocol`. Os 3 streams são fundidos num
  único `RuntimeEvent` taggeado por `source`.
- **Listener-error isolation.** Se um listener joga uma exceção, ela vai para
  `onListenerError` e os outros listeners continuam recebendo.
- **AppState forwards.** App chama `notifyBackground/notifyForeground` **no
  Runtime**, que propaga para os 3 engines.

---

## FSM de estados (10 estados)

```
uninitialized ─loadProtocol→ loaded ─start→ starting ─→ running ⇄ paused
                                                            │
                                                            ▼
                                                     stopping → stopped
                                                            │
                                                            ▼
                                                   completed | errored
                                                            │
                                                          dispose
                                                            ▼
                                                         disposed (terminal)
```

| Estado        | Origem                         | Pode chamar              |
| ------------- | ------------------------------ | ------------------------ |
| uninitialized | estado inicial                 | loadProtocol             |
| loaded        | loadProtocol OK                | start, dispose           |
| starting      | start (transitório)            | (running)                |
| running       | start OK                       | pause, cancel, dispose   |
| paused        | pause OK                       | resume, cancel, dispose  |
| stopping      | cancel (transitório)           | (stopped)                |
| stopped       | cancel OK                      | start, dispose           |
| completed     | ProtocolRuntime natural end    | start (restart), dispose |
| errored       | erro de compile/start/protocol | dispose                  |
| disposed      | dispose OK (terminal)          | (nada)                   |

**Estados terminais:** `stopped`, `completed`, `errored`, `disposed`.

---

## Event stream (tagged union)

```ts
type RuntimeEvent =
  | { source: 'timer'; payload: TimerEvent }
  | { source: 'breath'; payload: BreathEvent }
  | { source: 'protocol'; payload: ProtocolRuntimeEvent }
  | { source: 'runtime'; payload: RuntimeLifecycleEvent };

type RuntimeLifecycleEvent =
  | {
      type: 'runtime-warnings';
      warnings: readonly Failure[];
      monotonicMs: number;
    }
  | {
      type: 'runtime-compile-failed';
      failures: readonly Failure[];
      warnings: readonly Failure[];
      monotonicMs: number;
    }
  | {
      type: 'runtime-error';
      code: string;
      message: string;
      cause?: unknown;
      monotonicMs: number;
    }
  | { type: 'runtime-disposed'; monotonicMs: number }
  | { type: 'runtime-completed'; totalElapsedMs: number; monotonicMs: number };
```

**Zero information loss** — todos os eventos dos 3 engines fluem pelo mesmo
stream, com `source` discriminando a origem. O Runtime adiciona 5 eventos
próprios (lifecycle) que não existem nos engines — eles são projeções de estado
que o ProtocolRuntime não emite (compile-failed, runtime-error,
runtime-disposed, runtime-completed, runtime-warnings).

### Padrão de consumo

```ts
const unsub = rt.subscribe((e) => {
  switch (e.source) {
    case 'timer':
      /* TimerEvent */ break;
    case 'breath':
      /* BreathEvent */ break;
    case 'protocol':
      /* ProtocolRuntimeEvent */ break;
    case 'runtime':
      switch (e.payload.type) {
        case 'runtime-completed':
          /* ... */ break;
        case 'runtime-error':
          /* ... */ break;
        // etc.
      }
      break;
  }
});
```

---

## Métricas (RuntimeMetrics)

```ts
interface RuntimeMetrics {
  elapsedMs: number;
  plannedDurationMs: number;
  driftMs: number; // elapsed - planned
  cyclesCompleted: number;
  totalCycles: number;
  currentCycle: number;
  currentPhase: BreathPhase | null;
  phaseProgress: number;
  tickCount: number;
  pauseCount: number;
  totalPausedMs: number;
  warnings: number;
  errors: number;
  eventCounters: {
    timer: number;
    breath: number;
    protocol: number;
    runtime: number;
  };
}
```

`getMetrics()` é **O(1)** — os counters são atualizados in-place durante o
bridge; o `aggregateMetrics()` puro deriva a forma final a partir do snapshot.

---

## Snapshot (RuntimeSnapshot)

```ts
interface RuntimeSnapshot {
  runtimeId: EngineId;
  state: RuntimeState;
  plan: ProtocolExecutionPlan | null;
  protocol: ProtocolRuntimeSnapshot | null;
  breath: BreathSnapshot | null;
  timer: TimerEngineSnapshot | null;
}
```

Point-in-time view de tudo. Útil para sincronizar UI sem fan-out manual.

---

## Modelo de erro

| Code                          | Origem                                 | Onde cai                                    |
| ----------------------------- | REDACTED | REDACTED |
| `runtime_invalid_state`       | Lifecycle chamado em estado errado     | Result.Err                                  |
| `runtime_empty_plan`          | `plan.phases.length === 0`             | Result.Err                                  |
| `runtime_no_plan`             | start antes de load                    | Result.Err                                  |
| `runtime_compile_failed`      | `compiler.compile()` falhou            | Result.Err + emite `runtime-compile-failed` |
| `runtime_pause_outlasts_plan` | `elapsed >= planned` em resume()       | Result.Err                                  |
| `runtime_error`               | tradução de `protocol-runtime-errored` | emite lifecycle, vai p/ 'errored'           |

---

## Lifecycle ownership

**Runtime é dono** de:

- `TimerEngine` — criado no constructor (default) ou injetado via
  `deps.timerEngine`.
- `BreathEngine` — criado **lazily** em `loadProtocol` se `plan.cycles > 0`.
- `ProtocolRuntime` — criado no constructor; ele recebe o `TimerLike` adapter
  que embrulha o `TimerEngine`.
- `ProtocolCompiler` — criado no constructor para `compile()`.

**App é dono** de:

- Chamar `notifyBackground()` / `notifyForeground()` no Runtime (que fan-out
  para os 3 engines).
- Listener errors — coletar via `onListenerError` callback se quiser.

**App NÃO deve:**

- Importar qualquer engine diretamente. Quebra o contrato.
- Cancel e dispose são idempotentes.

---

## Gaps do Sprint 3 fechados pelo Runtime

| #   | Gap (Sprint 3)                                   | Sprint 4 fix                                                           |
| --- | REDACTED | REDACTED |
| 1   | `'errored'` state unreachable em ProtocolRuntime | Runtime traduz `protocol-runtime-errored` para seu próprio `'errored'` |
| 2   | Pause-outlasts-plan rewind silencioso            | `resume()` checa `elapsed >= planned` e retorna Err                    |
| 3   | Zero compile-time warning events                 | `runtime-warnings` event via lifecycle stream                          |
| 4   | 3 streams paralelos para subscribe               | 1 stream taggeado por fonte                                            |
| 5   | Sem promessa/concluído quando completa           | `runtime-completed` event com `totalElapsedMs`                         |
| 6   | Snapshot requer fan-out manual                   | `snapshot()` retorna merged de tudo                                    |
| 7   | Sem métricas agregadas                           | `getMetrics()` com drift + counters + cycle/phase                      |
| 8   | Criar 3 engines + wiring repete ~50 linhas       | 1 linha: `new RuntimeEngine({ runtimeId })`                            |
| 9   | Listener exception derruba o dispatch            | `onListenerError` callback; outros listeners continuam                 |

---

## Limites assumidos

- **Node 20+ ou React Native 0.74+** — depende do ambiente host.
- **1 Runtime por sessão** — não é compartilhável entre telas.
- **Background forward manual** — App é responsável por
  `notifyBackground/notifyForeground`.
- **`dispose()` é mandatório** — vazamentos de TimerEngine se não chamado.
- **Sem concorrência interna de start/pause** — chamadas sequenciais;
  comportamento concorrente indefinido.
- **Listeners não devem jogar** — mas se jogarem, vão para `onListenerError`.

---

## Como usar (consumidor)

```ts
// Mobile / Backend / Integração
import { RuntimeEngine } from '@core/runtime';
import { EngineId } from '@araflow/shared-contracts';
import { JsonSource } from '@core/protocol-compiler';

const rt = new RuntimeEngine({ runtimeId: EngineId('app-session-1') });

// Subscribe PRIMEIRO para não perder eventos
rt.subscribe((e) => {
  if (e.source === 'runtime' && e.payload.type === 'runtime-completed') {
    notifyUI({ kind: 'session-done', elapsedMs: e.payload.totalElapsedMs });
  }
});

// Compile + load + start
const source = JsonSource(fs.readFileSync(protocolPath, 'utf8'), protocolPath);
const r = rt.compile(source);
if (!r.ok) {
  console.error(r.error.code, r.error.message);
  process.exit(1);
}

rt.start();

// App state (mobile)
AppState.addEventListener('change', (s) => {
  if (s === 'background') rt.notifyBackground();
  else if (s === 'active') rt.notifyForeground();
});

// Cleanup
window.addEventListener('beforeunload', () => rt.dispose());
```

---

## Como estender (futuro)

- **Session Engine** vai consumir Runtime como dependência (1 linha), nunca
  engine direto.
- **Backend jobs** podem rodar Runtime em worker thread — Runtime não
  compartilha estado entre instâncias.
- **Testing** — injetar `timerEngine` fake via `deps.timerEngine` para controlar
  o tempo; Pulsar de ProtocolRuntime events via `t.emitTick(...)`.
- **Multi-source consumers** — usar o switch por `source` para roteamento (ex.:
  timer → métricas, breath → áudio, protocol → UI).

---

## Referências

- `docs/AraFlow/40_SPRINT4_RUNTIME_REPORT.md` — métricas, deliverables, gaps.
- `docs/adr/araflow/023-runtime-facade.md` — ADR-023.
- `docs/AraFlow/39_CORE_INTEGRATION.md` — harness CLI que provou o Core.
- `docs/AraFlow/38_PROTOCOL_COMPILER.md` — ProtocolRuntime vem daqui.
- `docs/AraFlow/36_BREATH_ENGINE.md` — Breath Engine.
- `docs/AraFlow/35_TIMER_ENGINE.md` — Timer Engine.
- `docs/AraFlow/37_CORE_CONTRACTS.md` — Shared Contracts.
