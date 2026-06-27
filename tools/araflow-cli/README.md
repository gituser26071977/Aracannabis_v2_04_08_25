# AraFlow CLI — Core Integration Harness

> **Version:** 0.1.0
> **Sprint:** 3.5 — Core Integration Harness
> **Status:** Implemented, tested, frozen.

The AraFlow CLI proves that the four frozen Core engines (Timer Engine, Breath Engine, Shared Contracts, Protocol Compiler) work together end-to-end. It loads a protocol JSON, validates it, compiles it, simulates it, runs it with the real Timer Engine, lints it, benchmarks it, and explains it — all without any UI.

## What it is NOT

- ❌ Not a UI
- ❌ Not React Native
- ❌ Not a backend service
- ❌ Not a database client
- ❌ Not the Session Engine

## What it is

- ✅ A Node 20+ CLI
- ✅ A pure consumer of the Core engines
- ✅ A proof that the Core works end-to-end
- ✅ A reference implementation for future integrations
- ✅ A debugging and inspection tool for protocol authors

## Commands

| Command     | Purpose                                                           |
| ----------- | REDACTED |
| `validate`  | Validate a protocol (Schema + Semantic + Compatibility)           |
| `compile`   | Compile a protocol to an Execution Plan                           |
| `simulate`  | Simulate a plan without the Timer Engine                          |
| `run`       | Run a plan with the real Timer Engine + Breath Engine in parallel |
| `lint`      | Run all 7 lint rules and show warnings                            |
| `benchmark` | Measure parse, compile, execute, memory, CPU, drift               |
| `explain`   | Show plan + timeline + warnings + stats + summary                 |

All commands accept `--json` for machine-readable output.

## Usage

```bash
# Install dependencies (workspace install from monorepo root)
cd Aracannabis_SIAP && npm install

# Build shared-contracts (needed for type resolution)
npm run build --workspace @araflow/shared-contracts

# Build the CLI
npm run build --workspace @araflow/cli

# Run commands
npx araflow --help
npx araflow validate tools/araflow-cli/fixtures/box-breathing.json
npx araflow compile tools/araflow-cli/fixtures/four-seven-eight.json
npx araflow simulate tools/araflow-cli/fixtures/box-breathing.json
npx araflow run tools/araflow-cli/fixtures/four-seven-eight.json --max-duration-ms 30000
npx araflow lint tools/araflow-cli/fixtures/four-seven-eight.json
npx araflow benchmark tools/araflow-cli/fixtures/box-breathing.json
npx araflow explain tools/araflow-cli/fixtures/box-breathing.json

# Machine-readable output
npx araflow simulate tools/araflow-cli/fixtures/box-breathing.json --json | jq '.totalCycles'
npx araflow benchmark tools/araflow-cli/fixtures/box-breathing.json --json | jq '.parseMs'
```

## Architecture

```
CLI (Node)
   │
   ├── io/load-source.ts       — reads JSON file → ProtocolSource
   ├── adapters/timer-like.ts  — wraps TimerEngine as TimerLike
   │
   ├── ProtocolCompiler (compile, validate, lint)
   ├── SimulationRuntime (simulate, benchmark)
   ├── TimerEngine + BreathEngine + ProtocolRuntime (run)
   │
   └── formatters/             — human-readable + JSON output
```

## Tests

```bash
npm run test --workspace @araflow/cli
npm run coverage --workspace @araflow/cli
```

## References

- `docs/AraFlow/39_CORE_INTEGRATION.md`
- `docs/AraFlow/39_SPRINT3_5_REPORT.md`
- `docs/AraFlow/38_PROTOCOL_COMPILER.md`
- `docs/AraFlow/36_BREATH_ENGINE.md`
- `docs/AraFlow/35_TIMER_ENGINE.md`
