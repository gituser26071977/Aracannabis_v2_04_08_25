# AraFlow — Protocol Compiler

> **Versão:** 1.0.0
> **Data:** 2026-06-27
> **Sprint:** 3 — Protocol Compiler
> **Status:** Implementado, testado, congelado.

---

## Sumário

1. Visão geral
2. Onde mora
3. Pipeline obrigatório
4. Camadas
5. Parser
6. Validators
7. Migration Pipeline
8. Intermediate Representation (IR)
9. Optimizer
10. Execution Plan
11. ProtocolCompiler (orchestrator)
12. Protocol Linter
13. Protocol Runtime
14. Simulation Runtime
15. Determinismo
16. Extensibilidade
17. Limitações
18. Performance
19. Referências

---

## 1. Visão geral

O **Protocol Compiler** é o primeiro compilador completo do ecossistema AraFlow. Ele transforma uma definição declarativa de protocolo (JSON) em um **Execution Plan** imutável, determinístico, serializável e independente de UI, e em seguida (quando solicitado) executa esse plano através de um Runtime desacoplado.

**O que ele conhece:**

- Documento de protocolo (JSON declarativo).
- Schema, semântica, versões, migrations.
- IR imutável.
- Optimization passes (redundância, normalização, pré-cálculo).
- Execution Plan (artefato final, frozen).
- Máquina de estados de Runtime (idle, ready, running, paused, stopping, stopped, completed, errored).
- Lint rules (warnings, nunca blocking).
- Simulation mode (execução pura sem Timer Engine).

**O que ele NÃO conhece:**

- React, React Native, UI.
- Audio Engine, Animation Engine, Session Engine, Runtime de aplicação.
- Persistência (responsabilidade de camadas superiores).
- Identidade do paciente, telemetria, billing.
- Plataforma específica (Node, RN, browser).

**Princípios:**

- Zero dependência de UI, React, React Native, plataforma.
- 100% determinístico: mesmo input → mesmo checksum → mesmo executionId.
- IR totalmente imutável (`Object.freeze` em breath, phases, ir).
- Execution Plan totalmente imutável e versionado.
- Runtime desacoplado do Timer Engine (recebe apenas `TimerLike`).
- Simulation Mode funcional sem Timer Engine.
- Linter gera **warnings**, nunca bloqueia compilação.
- Metadata preservada intacta do documento até o plan.

---

## 2. Onde mora

```
mobile/src/core/protocol-compiler/
├── domain/                         # Tipos puros + contratos
│   ├── SchemaVersion.ts            # URIs de schema + compat
│   ├── DocumentPhaseType.ts        # Map: documento → canônico
│   ├── DocumentCurve.ts            # Map: documento → curva canônica
│   ├── ProtocolDocument.ts         # Shape do ProtocolDocument
│   ├── ProtocolSource.ts           # Source (JsonSource, etc.)
│   ├── ProtocolParser.ts           # Interface Parser + registry
│   ├── IntermediateRepresentation.ts # IR imutável
│   └── ExecutionPlan.ts            # Plan imutável + ExecutionId
├── parser/
│   └── JsonProtocolParser.ts       # Parser JSON (extensível)
├── validation/
│   └── Validators.ts               # SchemaValidator, SemanticValidator, VersionCompatibilityValidator
├── migration/
│   └── ProtocolMigrationPipeline.ts # BFS de migrations
├── ir/
│   └── IRBuilder.ts                # Doc → IR (frozen)
├── optimizer/
│   └── OptimizerPass.ts            # 5 passes canônicos + FNV-1a hash
├── compiler/
│   ├── ExecutionPlanBuilder.ts     # IR → Plan
│   └── ProtocolCompiler.ts         # Orchestrator
├── linter/
│   └── ProtocolLinter.ts           # 7 lint rules
├── runtime/
│   ├── ProtocolRuntime.ts          # State machine (Timer-driven)
│   └── SimulationRuntime.ts        # Pure simulator (Clock-driven)
└── index.ts                        # Public barrel (PROTOCOL_COMPILER_PUBLIC_VERSION)
```

---

## 3. Pipeline obrigatório

```
ProtocolSource
   │
   ▼
Parser ────────────►  structural shape (semantically unvalidated)
   │
   ▼
SchemaValidator ────►  limites estruturais (cycles, phases, durations)
   │
   ▼
SemanticValidator ──►  invariantes de domínio (exhale presente, etc.)
   │
   ▼
VersionCompatibilityValidator ──►  major version compatível
   │
   ▼
ProtocolMigrationPipeline ──►  aplica chain de migrations (se necessário)
   │
   ▼
IRBuilder ──────────►  IR (frozen)
   │
   ▼
Optimizer ──────────►  IR otimizado + checksum + executionId
   │
   ▼
ExecutionPlanBuilder ► ProtocolExecutionPlan (imutável, versionado, determinístico)
   │
   ▼
ProtocolRuntime / SimulationRuntime
```

Cada estágio é isolado, testável independentemente, e produz `Result`-like ou `Failure` (severity).

---

## 4. Camadas

| Camada | Local | Conhece | Não conhece |
|--------|-------|---------|-------------|
| Domain | `domain/` | Types, contratos, mapeamentos | JSON, I/O, UI |
| Parser | `parser/` | Texto cru → shape estruturado | Semântica, runtime |
| Validation | `validation/` | Limites estruturais, invariantes | IR, runtime |
| Migration | `migration/` | Versions, transformações | IR |
| IR | `ir/` | Domain model | Schema, JSON, runtime |
| Optimizer | `optimizer/` | IR + transforms idempotentes | Sources, UI |
| Compiler | `compiler/` | Orquestração | Detalhes de cada estágio |
| Linter | `linter/` | Documento + IR | Runtime |
| Runtime | `runtime/` | Plan + Timer-like | Sources, schema |

---

## 5. Parser

### `ProtocolSource`

```ts
interface ProtocolSource {
  format: 'json' | 'yaml' | 'afl' | 'visual';
  raw: string;
  origin?: 'filesystem' | 'network' | 'inline';
}
```

Helper: `JsonSource(raw, origin?)`.

### `ProtocolParser`

```ts
interface ProtocolParser<T = unknown> {
  readonly format: ProtocolSourceFormat;
  parse(source: ProtocolSource): Result<ProtocolDocument, Failure[]>;
}
```

Sprint 3 entrega **apenas `JsonProtocolParser`** (foco do escopo). A interface é desenhada para que YAML, AFL DSL, ou Visual Editor sejam adicionados em sprints futuros sem alterar o compilador.

### `JsonProtocolParser`

- Aceita `$schema` opcional (default v1).
- Valida estrutura (id, version, title, breath).
- Retorna `Failure` com `code: 'json_parse_error'` ou `code: 'schema_*'` em caso de erro.
- Type guards em todo lugar (bracket notation para `noPropertyAccessFromIndexSignature`).

---

## 6. Validators

### `SchemaValidator`

| Limite | Valor | Justificativa |
|--------|-------|---------------|
| `MAX_CYCLES` | 100 | Sessões terapêuticas |
| `MAX_PHASES` | 16 | Limite de complexidade por ciclo |
| `MIN_PHASE_MS` | 100 | Resolúvel pelo Timer Engine |
| `MAX_PHASE_MS` | 60000 | 1 min — anti-patológico |

Valida estrutura completa do `ProtocolDocument`.

### `SemanticValidator`

Invariantes semânticas:

- `exhale` deve existir em algum lugar do array de phases (ninguém prende a respiração para sempre).
- `evidenceLevel` ∈ {A, B, C, D, undefined}.
- ULID regex `^[0-9A-HJKMNP-TV-Z]{26}$` (Crockford base32, exclui I, L, O, U).
- `category` setado se há `evidenceLevel` ou `author`.
- Semver compatível.

### `VersionCompatibilityValidator`

- Extrai major do `$schema` URI (`/v(\d+)(?:\.json)?$` ou `://protocol/v(\d+)$`).
- Compara com `compatibilityMajor` configurado (default = `CURRENT_SCHEMA_MAJOR`).
- Falha com `compat_future_major` se major do doc > major atual.

---

## 7. Migration Pipeline

### Modelo

```ts
interface Migration {
  readonly fromMajor: number;
  readonly toMajor: number;
  readonly name: string;
  apply(doc: ProtocolDocument): ProtocolDocument;
}
```

### Registry

`createMigrationRegistry()` retorna um `MigrationRegistry` com:

- `register(migration)`
- `available()` (frozen)
- `find(fromMajor, toMajor, registry)` (BFS — busca cadeia transitiva)

### Pipeline

```ts
class ProtocolMigrationPipeline {
  constructor(registry, targetMajor);
  migrate(doc): { doc: ProtocolDocument; failures: Failure[]; trace: MigrationTraceEntry[] };
}
```

Comportamento:

- Se major do doc = major alvo → pass-through.
- Se major do doc = supported schema major, mas URI diferente → pass-through.
- Se major do doc < alvo e chain existe → aplica cadeia (BFS).
- Se major do doc < alvo e chain não existe → `migration_no_path`.
- Se URI não casa regex → `migration_unknown_schema`.
- Se algum `apply` lança → `migration_apply_failed`.

Helpers: `extractMajorFromUri`, `noopMigration(from, to)`.

---

## 8. Intermediate Representation (IR)

### Por que IR

O documento de origem é rico, opcional, e extensível. O runtime precisa de um modelo **mínimo, imutável, sem serialização, sem dependências**. A IR é essa camada intermediária.

### `ProtocolIR`

```ts
interface ProtocolIR {
  readonly id: ProtocolId;
  readonly schemaVersion: number;
  readonly version: SemanticVersion;
  readonly title: string;
  readonly description?: string;
  readonly breath: Readonly<BreathConfigIR>;
  readonly metadata: Readonly<MetadataIR>;
}
```

### `BreathConfigIR`

```ts
interface BreathConfigIR {
  readonly cycles: number;
  readonly restBetweenCyclesMs: number;
  readonly phases: readonly PhaseIR[];
}

interface PhaseIR {
  readonly index: number;
  readonly phase: BreathPhase;       // canonical
  readonly durationMs: number;
  readonly curve: CurveType;          // canonical
}
```

### `MetadataIR`

```ts
interface MetadataIR {
  readonly author?: string;
  readonly language?: string;
  readonly references: readonly string[];
  readonly evidenceLevel?: EvidenceLevel;
  readonly contraindications: readonly string[];
  readonly category?: string;
  readonly tags: readonly string[];
  readonly approvedAt?: Iso8601;
}
```

### Imutabilidade

`buildIR(doc)` chama `Object.freeze()` em `breath`, `phases` array, e em cada `PhaseIR` antes de retornar. **Mutating post-compile é impossível em runtime** (deep freeze em runtime, ou congelado estruturalmente em TS strict).

`emptyMetadataIR()` produz o esqueleto vazio (para protocolos sem metadata).

---

## 9. Optimizer

### 5 passes canônicos (em ordem)

1. **removeRedundancyPass** — remove phases duplicadas consecutivas (mesma `BreathPhase` + mesma `durationMs` + mesma `CurveType`).
2. **normalizePhasesPass** — normaliza phase types para o canônico (`inhale` → `inhaling`).
3. **precalculateCyclesPass** — pré-calcula `cycleIndex` em cada phase.
4. **precalculateDurationsPass** — pré-calcula `totalCycleDuration`, `totalDuration`, e durações relativas.
5. **checksumPass** — computa `checksum` (FNV-1a hash) e `executionId`.

### FNV-1a hash

```ts
function fnv1a(input: string): string {
  let h = 0x811c9dc5;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return `fnv1a:${(h >>> 0).toString(16)}`;
}
```

Formato: `fnv1a:<hex>`. Determinístico, estável, sem deps.

### `runOptimizerPipeline`

```ts
runOptimizerPipeline(ir: ProtocolIR, now: () => number): OptimizerDiagnostics
```

Retorna IR transformado + diagnostics (passes rodadas, timings, checksum, executionId).

### `computeExecutionId(ir, now)`

Combina FNV-1a do IR canônico + ULID derivado de `now()`. Mesmo IR + mesmo `now` → mesmo executionId.

---

## 10. Execution Plan

### `ProtocolExecutionPlan`

```ts
interface ProtocolExecutionPlan {
  readonly planFormatVersion: typeof PROTOCOL_PLAN_FORMAT_VERSION;
  readonly executionId: ExecutionId;
  readonly sourceProtocolId: ProtocolId;
  readonly sourceProtocolVersion: SemanticVersion;
  readonly checksum: string;
  readonly cycles: number;
  readonly totalCycleDuration: Duration;
  readonly totalDuration: Duration;
  readonly restBetweenCyclesMs: Duration;
  readonly phases: readonly PlanPhaseStep[];
  readonly metadata: PlanMetadata;
  readonly compiledAt: Iso8601;
  readonly compiledBy: EngineId;
}
```

### `PlanPhaseStep`

```ts
interface PlanPhaseStep {
  readonly index: number;
  readonly cycleIndex: number;
  readonly phase: BreathPhase;
  readonly duration: Duration;
  readonly curve: CurveType;
}
```

### `PlanMetadata`

Espelha `MetadataIR`. Preserva todos os campos intactos: `author`, `language`, `references`, `evidenceLevel`, `contraindications`, `category`, `tags`, `approvedAt`.

### Imutabilidade

`buildExecutionPlan` retorna objeto `Object.freeze`-ado. Planos podem ser serializados (`JSON.stringify` é seguro) e transmitidos por IPC entre camadas sem medo de mutação.

### Determinismo

- `checksum` é FNV-1a do IR canônico serializado.
- `executionId` é derivado de `checksum + now()`.
- Mesmo input + mesmo `now` → mesmo plan (bitwise).

---

## 11. ProtocolCompiler (orchestrator)

```ts
class ProtocolCompiler {
  constructor(config: CompilerConfig);
  compile(source: ProtocolSource): FullCompilerResult;
}

interface CompilerConfig {
  readonly compiledBy: EngineId;
  readonly parsers?: ParserRegistry;       // default = [JsonProtocolParser]
  readonly migrations?: MigrationRegistry;  // default = empty
  readonly compatibilityMajor?: number;     // default = CURRENT_SCHEMA_MAJOR
  readonly now?: () => number;              // default = Date.now
}

interface FullCompilerResult {
  readonly plan: ProtocolExecutionPlan | null;
  readonly failures: readonly Failure[];     // blocking (error/fatal)
  readonly warnings: readonly Failure[];     // lint warnings only
  readonly diagnostics: CompilerDiagnostics;
}

interface CompilerDiagnostics {
  readonly totalTimeMs: number;
  readonly optimizerPasses: readonly string[];
  readonly stages: readonly { stage: string; durationMs: number }[];
}
```

### Estágios (na ordem)

1. **Parser lookup** — `parsers.lookup(source.format)`.
2. **Parse** — `parser.parse(source)`.
3. **Schema validation** — `SchemaValidator.validate(doc)`.
4. **Semantic validation** — `SemanticValidator.validate(doc)`.
5. **Version compat** — `VersionCompatibilityValidator.validate(doc, compatibilityMajor)`.
6. **Migration** — `ProtocolMigrationPipeline.migrate(doc)`.
7. **IR build** — `buildIR(doc)`.
8. **Optimizer** — `runOptimizerPipeline(ir, now)`.
9. **Plan build** — `buildExecutionPlanFromIR(ir, ...)` (incluindo lint).
10. **Lint** — `ProtocolLinter.lint(doc, plan)` — emite warnings (nunca bloqueia).

### Failure vs. Warning

| Origem | Tipo | Severidade | Bloqueia plan? |
|--------|------|------------|----------------|
| Parser error | failure | fatal | sim |
| Schema invalid | failure | error | sim |
| Semantic error | failure | error | sim |
| Compat error | failure | error | sim |
| Migration error | failure | error | sim |
| Lint warning | warning | warn | **não** |

### `toSharedCompilerResult(result)`

Adapta para o shape consumido pelo `@araflow/shared-contracts/Compiler` interface.

---

## 12. Protocol Linter

### 7 regras (todas warnings)

| Rule | Code | Detecta |
|------|------|---------|
| `redundantStepsRule` | `lint_redundant_steps` | Phases com mesma phase + duration + curve consecutivos |
| `invalidDurationRule` | `lint_invalid_duration` | Duração fora de [100ms, 60000ms] |
| `missingMetadataRule` | `lint_missing_metadata` | Sem author, sem references, sem evidenceLevel |
| `emptyProtocolRule` | `lint_empty_protocol` | 0 phases ou 0 cycles |
| `checksumInconsistencyRule` | `lint_checksum_inconsistency` | Checksum vs computed mismatch |
| `unusualCycleCountRule` | `lint_unusual_cycle_count` | Cycles fora de [1, 100] |
| `missingDescriptionRule` | `lint_missing_description` | Sem `description` |

### Severidade

Todos retornam `severity: 'warn'` (via `Failure` + `lint_warning` code). O compilador separa `failures` (blocking) de `warnings` (informational). **Linter nunca bloqueia compilação.**

### Uso customizado

```ts
const linter = new ProtocolLinter();
linter.addRule(myCustomRule);
const warnings = linter.lint(doc, plan);
```

---

## 13. Protocol Runtime

### State Machine

```
   ┌──────┐    load()    ┌────────┐  start()  ┌─────────┐
   │ idle │ ────────────►│ ready  │──────────►│ running │
   └──────┘              └────────┘           └────┬────┘
                                                 │
                       ┌─────────┐  pause()  ◄────┘
                       │ paused  │──────────┐
                       └────┬────┘  resume() │
                            │               ▼
                            │         ┌─────────┐
                            │         │ running │
                            │         └────┬────┘
                            │              │ (tick → elapsed >= totalDuration)
                            │              ▼
                            │         ┌───────────┐
                            │         │ completed │
                            │         └───────────┘
                            │              │
                            │         stop()│
                            │              ▼
                            │         ┌─────────┐
                            │         │ stopped │
                            │         └─────────┘
                            ▼
                       stop() → stopping → stopped
```

### `TimerLike` interface

```ts
interface TimerLike {
  start(): void;
  stop(): void;
  subscribe(listener: (event: TimerLikeEvent) => void): () => void;
  getTotalElapsedMs(): number;
}
```

**O runtime NÃO importa Timer Engine diretamente.** Ele recebe um adapter `TimerLike`. Produção usa o Timer Engine real; testes usam `FakeTimer`. Decoupling explícito.

### `ProtocolRuntimeEvent`

```ts
type ProtocolRuntimeEvent =
  | { type: 'protocol-runtime-started'; ... }
  | { type: 'protocol-runtime-paused'; ... }
  | { type: 'protocol-runtime-resumed'; ... }
  | { type: 'protocol-runtime-tick'; ... }
  | { type: 'protocol-runtime-phase-changed'; ... }
  | { type: 'protocol-runtime-cycle-completed'; ... }
  | { type: 'protocol-runtime-completed'; ... }
  | { type: 'protocol-runtime-stopped'; ... }
  | { type: 'protocol-runtime-errored'; ... };
```

### API

```ts
class ProtocolRuntime {
  constructor(deps: ProtocolRuntimeDeps);
  load(plan: ProtocolExecutionPlan): Result<void, EngineError>;
  start(): Result<void, EngineError>;
  pause(): Result<void, EngineError>;
  resume(): Result<void, EngineError>;
  stop(): Result<void, EngineError>;
  subscribe(listener: ProtocolRuntimeListener): () => void;
  snapshot(): ProtocolRuntimeSnapshot;
  readonly state: ProtocolRuntimeState;
}
```

### `onListenerError`

Hook opcional para capturar exceções em listeners sem interromper dispatch (semelhante ao EventEmitter do Timer Engine).

### Snapshot

```ts
interface ProtocolRuntimeSnapshot {
  state: ProtocolRuntimeState;
  executionId: string | null;
  currentPhase: BreathPhase | null;
  cycleIndex: number;
  phaseIndex: number;
  elapsedMs: number;
  phaseProgress: number;
  totalCycles: number;
  totalDurationMs: number;
}
```

---

## 14. Simulation Runtime

### Quando usar

Quando você precisa validar que um Execution Plan está correto sem depender do Timer Engine (ex: em testes, em backend Node, em CI, em smoke tests de produção sem device).

### `SimulationRuntime`

```ts
class SimulationRuntime {
  constructor(plan: ProtocolExecutionPlan, clock: Clock);
  runToCompletion(): SimulationReport;
}

interface Clock {
  now(): number;
  wallNow(): number;
}
```

### Comportamento

- Itera todos os ciclos.
- Em cada cycle, itera todos os phases.
- Calcula phase start/end com base em `getTotalElapsedMs()` do `Clock`.
- Emite registros de phase e cycle.
- Retorna `SimulationReport` com totais.

### `SimulationReport`

```ts
interface SimulationReport {
  readonly totalCycles: number;
  readonly totalDurationMs: number;
  readonly phases: readonly SimulationPhaseRecord[];
  readonly cycles: readonly SimulationCycleRecord[];
}
```

### Não tem `start/pause/stop`

É batch-only. Para runtime interativo, use `ProtocolRuntime` (que aceita Timer Engine real).

---

## 15. Determinismo

Garantias:

1. **Mesmo input + mesmo `now` → mesmo checksum.**
2. **Mesmo input + mesmo `now` → mesmo executionId.**
3. **Optimization é idempotente** — rodar 2x produz mesmo IR.
4. **FNV-1a é estável** — mesmos bytes → mesmo hash.
5. **ULID é monotonic** — `now` crescente → executionId crescente.
6. **Plano é serializável bitwise** — `JSON.stringify(planA) === JSON.stringify(planB)` quando checksums batem.

Casos onde determinismo **NÃO** se aplica:

- Se `now()` mudar entre execuções → executionId muda (correto — executionId é temporal).
- Se `now()` for não-monotonic (ex: NTP step) → executionId pode regredir (mitigado por monotonic clock no Timer Engine).

---

## 16. Extensibilidade

### Adicionar um novo parser

```ts
class YamlProtocolParser implements ProtocolParser {
  readonly format = 'yaml';
  parse(source: ProtocolSource): Result<ProtocolDocument, Failure[]> {
    // ...
  }
}

registry.register(new YamlProtocolParser());
```

O compilador descobre parsers via `ParserRegistry` — zero alterações ao orchestrator.

### Adicionar uma migration

```ts
const m: Migration = {
  fromMajor: 1,
  toMajor: 2,
  name: 'add-rest-between-cycles',
  apply: (doc) => ({
    ...doc,
    breath: { ...doc.breath, restBetweenCyclesMs: 0 },
  }),
};

migrations.register(m);
```

### Adicionar uma optimizer pass

```ts
const myPass: OptimizerPass = (ir) => {
  // transform IR (pure function)
  return newIr;
};

const result = runOptimizerPipeline(ir, now, [removeRedundancyPass, /* ..., */ myPass]);
```

### Adicionar uma lint rule

```ts
const myRule: LintRule = (doc, plan) => {
  if (plan.cycles > 50) {
    return [Failure({ code: 'lint_too_many_cycles', severity: 'warn', ... })];
  }
  return [];
};

linter.addRule(myRule);
```

---

## 17. Limitações

| Limitação | Sprint futura |
|-----------|---------------|
| Apenas JSON parser (YAML, AFL, Visual Editor pendentes) | Sprint 4+ |
| Sem AFL DSL própria | Sprint 5 |
| Runtime não integra com Breath Engine (curves são resolvidas no runtime, mas cycle é 4-phase rigid no Breath) | Sprint 4 (N-phase protocol cycles) |
| Linter só tem 7 rules | Sprint 4+ |
| Não persiste planos | Sprint 4+ (Storage Engine) |
| Sem telemetria | Sprint 5+ (Analytics) |
| Sem undo de migration | Fora de escopo |

---

## 18. Performance

### Hot paths

- **JSON.parse** — único call por compile. O(n) no tamanho do doc.
- **Schema validation** — O(n_phases) traversal.
- **Semantic validation** — O(n_phases + n_metadata_fields).
- **IR build** — O(n_phases).
- **Optimizer (5 passes)** — O(n_phases × 5) total, cada pass O(n).
- **FNV-1a** — O(n_bytes) sobre IR serializado.

### Benchmarks típicos (mobile)

| Documento | Tamanho | Tempo (compile completo) |
|-----------|---------|--------------------------|
| 4-7-8 (3 phases, 4 cycles) | ~600 bytes | <2 ms |
| Box (4 phases, 10 cycles) | ~700 bytes | <2 ms |
| Coherent (2 phases, 50 cycles) | ~650 bytes | <2 ms |
| Custom (16 phases, 100 cycles) | ~1.5 KB | <5 ms |

Runtime tick é O(1) — apenas walk forward do cycle/phase pointer.

### Memory

IR e Plan são frozen structures. Memória estável. Zero allocations por tick.

---

## 19. Referências

- `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md` — Architectural foundation
- `docs/AraFlow/34_SPRINT0_IMPLEMENTATION_REPORT.md` — Sprint 0 (Setup)
- `docs/AraFlow/35_TIMER_ENGINE.md` + `35_SPRINT1_TIMER_REPORT.md` — Sprint 1
- `docs/AraFlow/36_BREATH_ENGINE.md` + `36_SPRINT2_BREATH_REPORT.md` — Sprint 2
- `docs/AraFlow/37_CORE_CONTRACTS.md` + `37_SPRINT2_5_REPORT.md` — Sprint 2.5
- `docs/adr/araflow/019-master-clock-implementation.md` — Timer Engine ADR
- `docs/adr/araflow/020-breath-engine.md` — Breath Engine ADR
- `docs/adr/araflow/021-core-contracts.md` — Shared Contracts ADR
- `docs/adr/araflow/022-protocol-compiler.md` — Protocol Compiler ADR
- `docs/AraFlow/REDACTED.md` — Sprint 3 report