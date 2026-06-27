# 39 — Core Integration

**Sprint:** 3.5 — Core Integration Harness **Status:** Implementado, testado,
congelado. **Versão:** `@araflow/cli@0.1.0`

---

## Propósito

O **AraFlow Core Integration Harness** é a prova viva de que os quatro engines
frozen do Core (Timer Engine, Breath Engine, Shared Contracts, Protocol
Compiler) funcionam de ponta a ponta — sem UI, sem React Native, sem backend,
sem banco.

Ele existe para:

1. **Validar** que os contratos compartilhados se sustentam em uso real.
2. **Comprometer** o Core como unidade — qualquer regressão em um engine quebra
   a CLI.
3. **Servir como referência** para integrações futuras (mobile, backend, jobs
   assíncronos).
4. **Inspecionar** protocolos: validar, compilar, simular, executar, lintar,
   benchmarkar, explicar.

A CLI é a primeira consumidora real do Core. Se ela roda, o Core funciona.

---

## O que NÃO é

- ❌ Não é uma UI.
- ❌ Não é React Native.
- ❌ Não é um backend / serviço HTTP.
- ❌ Não é cliente de banco.
- ❌ Não é o Session Engine (próxima sprint, após validação do Core).

---

## Comandos

| Comando            | Propósito                                         | Exit codes     |
| ------------------ | REDACTED | -------------- |
| `validate <file>`  | Valida Schema + Semântica + Compatibilidade       | 0 ok · 1 falha |
| `compile <file>`   | Compila para Execution Plan                       | 0 ok · 2 falha |
| `simulate <file>`  | Executa SimulationRuntime (sem relógio real)      | 0 ok · 2 falha |
| `run <file>`       | Executa com Timer Engine + Breath Engine reais    | 0 ok · 3 falha |
| `lint <file>`      | Roda 7 regras de lint (warnings, nunca bloqueia)  | 0 sempre       |
| `benchmark <file>` | Mede parse, compile, execute, memória, CPU, drift | 0 sempre       |
| `explain <file>`   | Mostra plan + timeline + stats + summary          | 0 ok · 2 falha |

Todos aceitam `--json` para saída estruturada (CI / scripting).

**Exit codes globais:**

| Código | Significado                                     |
| ------ | REDACTED |
| 0      | sucesso                                         |
| 1      | falha de validação / lint                       |
| 2      | falha de compilação (sem plan)                  |
| 3      | falha de runtime (timeout, erro, cancelamento)  |
| 99     | erro fatal (escape de comando, IO catastrófico) |

---

## Arquitetura

```
                 CLI (Node 20+)
                       │
        ┌──────────────┼────────────────────────┐
        │              │                        │
    src/io/        src/commands/           src/formatters/
    load-source    validate                json
                  compile                  plan
                  simulate                 timeline
                  run                      stats
                  lint                     summary
                  benchmark                warnings
                  explain
        │              │                        │
        │              ▼                        │
        │      src/util/  +  src/adapters/      │
        │      engine-id     timer-like         │
        │      clock                             │
        │      breath-config                     │
        │              │                        │
        └──────────────┼────────────────────────┘
                       ▼
              Core engines (FROZEN)
   ┌──────────────┬────────────────┬──────────────────────┐
   │ Timer Engine │ Breath Engine  │ Protocol Compiler    │
   │              │                │ (compile / runtime / │
   │              │                │  simulation / lint)  │
   └──────────────┴────────────────┴──────────────────────┘
                       │
                       ▼
              Shared Contracts
              (@araflow/shared-contracts@1.0.0)
```

### Componentes da CLI

| Pasta             | Responsabilidade                                      |
| ----------------- | REDACTED |
| `src/io/`         | Ler JSON do disco → `ProtocolSource` (`JsonSource`)   |
| `src/adapters/`   | Adapter que embrulha `TimerEngine` como `TimerLike`   |
| `src/util/`       | Engine IDs, Clock, conversão Plan → BreathCycleConfig |
| `src/commands/`   | Implementação dos 7 comandos                          |
| `src/formatters/` | Saída humana (chalk) e JSON                           |
| `src/program.ts`  | Builder do Commander (testável, sem `process`)        |
| `src/cli.ts`      | Bin entry — `parseAsync(argv)` + exit codes           |
| `src/index.ts`    | Entry programático (`runProgram(argv)`)               |

---

## Pipeline end-to-end

O comando `run` é o caminho completo que prova o Core:

```
1. loadProtocolSource(filepath)              → ProtocolSource
2. new ProtocolCompiler({ compiledBy })      → compiler
3. compiler.compile(source)                  → { plan, warnings, failures }
4. createTimerEngine()                       → TimerEngine (wall-clock)
5. planToBreathConfig(plan)                  → BreathCycleConfig (4-phase lossy)
6. createBreathEngine({ timer, config })     → BreathEngine (side-channel)
7. new ProtocolRuntime({ timer: TimerLike }) → ProtocolRuntime (source of truth)
8. timer.start() + breath.start()
9. runtime.load(plan) + runtime.start()
10. subscribe(timer / breath / runtime)      → 3 streams paralelos
11. poll até completed | timeout
12. cleanup + summary (drift, phases, cycles)
```

**Decisões arquiteturais chave:**

- **TimerLike adapter (~15 linhas):** o ProtocolRuntime consome `TimerLike`, não
  `TimerEngine` diretamente. Prova que o seam arquitetural é limpo — zero
  alterações no Core para plugar.
- **BreathConfig lossly:** o Breath Engine é 4-phase rígido. O adapter colapsa
  N-phase → 4-phase pegando o primeiro
  `inhaling`/`holdAfterInhale`/`exhaling`/`holdAfterExhale`. Breath Engine é
  observador side-channel, não source of truth.
- **`runProgram(argv)` programático:** além do bin CLI, a função `runProgram`
  permite invocar a CLI sem spawnar processo filho — usado pelos testes E2E.
- **`runToCompletion()` no Simulation:** sem timer real, sem monotonic — usa
  `Clock` injetado. Drift sempre 0.

---

## Fixtures

| Fixture                     | Tipo                                                  | Uso                  |
| --------------------------- | REDACTED | -------------------- |
| `box-breathing.json`        | Positivo · Box (4×4×4×4, 4 cycles)                    | E2E padrão           |
| `diaphragmatic.json`        | Positivo · Respiração Diafragmática (6+2+8, 6 cycles) | E2E                  |
| `physiological-sigh.json`   | Positivo · Suspiro Fisiológico (2+1+6, 3 cycles)      | E2E                  |
| `four-seven-eight.json`     | Positivo · 4-7-8 (4+7+8, 4 cycles)                    | E2E                  |
| `invalid-empty-phases.json` | Negativo · phases ausentes                            | Testa exit codes 1/2 |
| `lint-warnings.json`        | Negativo · durations não múltiplos de 100ms           | Testa regras de lint |

---

## Contratos consumidos

A CLI depende **apenas** de:

- `@araflow/shared-contracts@1.0.0` — `EngineId`, `AppError`, `Clock`, tipos
  compartilhados.
- `@core/timer-engine` — `createTimerEngine`, `TimerEvent` (consumido apenas em
  `run`).
- `@core/breath-engine` — `createBreathEngine`, `BreathEvent`,
  `BreathCycleConfig`.
- `@core/protocol-compiler` — `ProtocolCompiler`, `ProtocolRuntime`,
  `SimulationRuntime`, `TimerLike`, tipos de plan / IR.

Nenhum desses pacotes foi modificado para acomodar a CLI. A prova: o adapter tem
15 linhas.

---

## Como rodar

```bash
# Build de pré-requisitos
npm run build --workspace @araflow/shared-contracts

# Build da CLI
npm run build --workspace @araflow/cli

# Comandos
npx araflow validate tools/araflow-cli/fixtures/box-breathing.json
npx araflow compile  tools/araflow-cli/fixtures/four-seven-eight.json
npx araflow simulate tools/araflow-cli/fixtures/box-breathing.json
npx araflow run      tools/araflow-cli/fixtures/four-seven-eight.json --max-duration-ms 30000
npx araflow lint     tools/araflow-cli/fixtures/four-seven-eight.json
npx araflow benchmark tools/araflow-cli/fixtures/box-breathing.json
npx araflow explain  tools/araflow-cli/fixtures/box-breathing.json

# Machine-readable (CI / scripting)
npx araflow simulate  tools/araflow-cli/fixtures/box-breathing.json --json | jq '.simulation.totalCycles'
npx araflow benchmark tools/araflow-cli/fixtures/box-breathing.json --json | jq '.aggregate.parseMs'

# Testes
npm run test --workspace @araflow/cli
npm run coverage --workspace @araflow/cli
```

---

## Saída humana (exemplos)

### `simulate box-breathing.json`

```
✓ Simulated .../fixtures/box-breathing.json

  executionId  01HXYZ...
  cycles       4
  phases       16
  duration     64.00s
  checksum     0xa3f5b2c1

Timeline
────────────────────────────────────────────────────────────
  [cycle 1/4] phase 1/4  inhaling          0.00s → 4.00s
  [cycle 1/4] phase 2/4  holdAfterInhale   4.00s → 8.00s
  [cycle 1/4] phase 3/4  exhaling          8.00s →12.00s
  [cycle 1/4] phase 4/4  holdAfterExhale  12.00s →16.00s
  ...

Summary
────────────────────────────────────────────────────────────
  executionId         01HXYZ...
  cycles              4 / 4
  phases              16 / 16
  planned             64.00s
  actual              64.00s
  drift               0ms
  status              completed
```

### `benchmark box-breathing.json`

```
Benchmark .../fixtures/box-breathing.json (5 iterations)
────────────────────────────────────────────────────────────
  plan              4 cycles × 16 phases
  planned duration  64.00s

Average timings (ms):
  parse             0.42
  compile           1.87
  execute           0.93
  total             3.22

Resources:
  peak heap delta   128 KB
  cpu user          14 ms
  cpu system        2 ms

Drift:
  drift (simulation) 0.00 ms
```

---

## Limites assumidos

- **Node 20+** requerido (`engines.node`).
- **Lint NUNCA bloqueia** por contrato — é sinal de qualidade, não portão.
- **`run` requer timer real** — em ambientes sem `setTimeout` (ex.: sandbox
  restritivo) usar `simulate`.
- **Drift é informativo**, não alarmado — diferentes Ns de processadores geram
  variação natural.

---

## Referências

- `docs/AraFlow/39_SPRINT3_5_REPORT.md` — métricas, deliverables, status.
- `docs/AraFlow/38_PROTOCOL_COMPILER.md` +
  `REDACTED.md` — Core do Compiler.
- `docs/AraFlow/36_BREATH_ENGINE.md` + `36_SPRINT2_BREATH_REPORT.md` — Breath
  Engine.
- `docs/AraFlow/35_TIMER_ENGINE.md` + `35_SPRINT1_TIMER_REPORT.md` — Timer
  Engine.
- `docs/AraFlow/37_CORE_CONTRACTS.md` + `37_SPRINT2_5_REPORT.md` — Shared
  Contracts.
- `tools/araflow-cli/README.md` — quickstart.
