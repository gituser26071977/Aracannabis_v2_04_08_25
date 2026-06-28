# 37 — Core Contracts (AraFlow Shared Contracts)

**Sprint:** 2.5
**Status:** ✅ Aprovado (Constituição Técnica)
**Versão:** 2.5.0
**Owner:** AraFlow Core Team
**Data:** 2026-06-25

---

## 1. Visão Geral

O módulo `@araflow/shared-contracts` é o **único ponto oficial de definição de contratos** do AraFlow. Nenhum engine, feature, ou aplicativo pode definir tipos próprios que já existam neste módulo.

**Regra de ouro:** Se dois lugares precisarem falar sobre o mesmo conceito (ex.: `EngineState`, `Duration`, `Result<T,E>`), ambos importam do shared-contracts. Não existe exceção.

### 1.1 Por que existe

- **Consistência:** o Breath Engine no mobile e o Protocol Engine no backend usam exatamente o mesmo `BreathPhase`.
- **Refatoração segura:** trocar o nome `EngineState = 'idle'` por outro valor é uma alteração única, propagada via type-check.
- **Testes determinísticos:** o consumidor pode confiar que `Duration(1000)` rejeita `Duration(-1)` em qualquer ambiente.
- **Documentação executável:** os tipos carregam semântica (Branded, Frozen) que IDEs e linters usam para validar.

### 1.2 Restrições arquiteturais

| Restrição | Razão |
|-----------|-------|
| Zero dependências de React, React Native, Node, Browser, infra | Os tipos precisam rodar em TODOS os ambientes (mobile, backend, edge) |
| 100% TypeScript strict | `noImplicitAny`, `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess` |
| Zero `any` | Toda ambiguidade deve ser modelada com `unknown` + type guards ou `Result<T, E>` |
| Zero TODO / FIXME | Contratos não podem ter pendências |
| 100% cobertura de testes | Todos os value objects, result patterns, errors e contracts |
| Pure functions | Sem efeitos colaterais, sem `Date.now()` interno |

---

## 2. Estrutura do Módulo

```
shared-contracts/
├── src/
│   ├── value-objects/      # Tipos primitivos com validação
│   │   ├── validation.ts       # AppError + helpers de validação
│   │   ├── ids.ts              # ProtocolId, SessionId, EngineId, etc.
│   │   ├── numeric.ts          # Duration, Timestamp, Percentage, Progress
│   │   └── version.ts          # SemanticVersion
│   │
│   ├── enums/               # Constantes canônicas + types
│   │   ├── state.ts            # EngineState, ProtocolState, SessionState
│   │   ├── breath.ts           # BreathPhase, CurveType, InterpolationType
│   │   ├── priority.ts         # Priority, Severity + rank records
│   │   └── types.ts            # CurveFn
│   │
│   ├── patterns/            # Result, Option, Either, Failure
│   │   ├── result.ts           # Ok/Err + map/flatMap/unwrap/all
│   │   ├── option.ts           # Some/None + map/flatMap/zip/firstSome
│   │   ├── either.ts           # Left/Right + mapLeft/mapRight
│   │   └── failure.ts          # Failure + groupFailuresBySeverity
│   │
│   ├── utilities/           # Helpers reutilizáveis
│   │   ├── readonly.ts         # DeepReadonly, Immutable
│   │   ├── uuid.ts             # generateUuidV4, validateUuidV4, generateUlidLike
│   │   └── time-unit.ts        # TIME_UNITS, toMilliseconds, fromMilliseconds
│   │
│   ├── interfaces/          # Contratos de comportamento
│   │   ├── lifecycle.ts        # Disposable, Subscription, Engine, LifecycleController
│   │   ├── infrastructure.ts   # Clock, Scheduler
│   │   ├── observability.ts    # Logger, MetricsCollector, Event, EventBus
│   │   └── protocol.ts         # ProtocolSource, ExecutionPlan, Compiler
│   │
│   ├── events/              # Tipos de evento canônicos
│   │   └── lifecycle.ts        # EngineStarted, EngineStopped, Tick, PhaseChanged, ...
│   │
│   ├── errors/              # Hierarquia tipada de erros
│   │   └── base.ts             # AppError + ValidationError, CompilationError, etc.
│   │
│   └── index.ts             # Barrel público
│
└── __tests__/               # 299 testes · 100% cobertura
```

---

## 3. Value Objects

### 3.1 Branded IDs

Identificadores são `string` em runtime, mas **tipos distintos em compile-time**. Construtores validam formato e lançam `AppError` em caso de falha.

```typescript
import { ProtocolId, EngineId } from '@araflow/shared-contracts';

const protocolId = ProtocolId('01ARZ3NDEKTSV4RRFFQ69G5FAV');  // ULID válido
const engineId = EngineId('timer-engine');                     // kebab-case
const bad = ProtocolId('invalid');                              // throws AppError('invalid_protocol_id')
```

| Tipo | Formato | Construtor lança |
|------|---------|------------------|
| `ProtocolId` | ULID (26 chars, Crockford base32) | `invalid_protocol_id` |
| `SessionId` | ULID | `invalid_session_id` |
| `EngineId` | kebab-case, inicia com letra, ≥2 chars | `invalid_engine_id` |
| `TenantId` | ULID | `invalid_tenant_id` |
| `UserId` | ULID | `invalid_user_id` |
| `PatientId` | ULID | `invalid_patient_id` |

### 3.2 Time and Numeric Values

Toda duração é armazenada em **milissegundos** (unidade canônica). Conversões para outras unidades são explícitas.

```typescript
import {
  Duration,
  DurationFromSeconds,
  DurationFromMinutes,
  DurationZero,
  durationToSeconds,
  Timestamp,
  TimestampNow,
  timestampDifference,
  Iso8601,
  Iso8601FromTimestamp,
} from '@araflow/shared-contracts';

const inhaleMs = DurationFromSeconds(4);     // 4000ms
const cycleMs = DurationFromMinutes(2);      // 120_000ms
const total = timestampDifference(endTs, startTs);
const iso = Iso8601FromTimestamp(TimestampNow());
```

| Tipo | Faixa | Validação |
|------|-------|-----------|
| `Duration` | `[0, 100h]` em ms (integer) | `invalid_duration` |
| `Timestamp` | `[0, year 9999]` em ms (integer) | `invalid_timestamp` |
| `Percentage` | `[0, 100]` | `invalid_percentage` |
| `Progress` | `[0, 1]` | `invalid_progress` |
| `CycleIndex` | `[0, ∞)` integer | `invalid_cycle_index` |
| `PhaseIndex` | `[0, ∞)` integer | `invalid_phase_index` |
| `Iso8601` | ISO 8601 string | `invalid_iso8601` |

### 3.3 SemanticVersion

Comparação segue [semver.org](https://semver.org/) — incluindo prerelease e build metadata.

```typescript
import { SemanticVersion, compareSemanticVersions, isVersionCompatible } from '@araflow/shared-contracts';

const v1 = SemanticVersion('1.0.0');
const v2 = SemanticVersion('1.0.1-alpha');

compareSemanticVersions(v1, v2);           // 1 (v1 > v2, prerelease é menor)
isVersionCompatible(v1, v2);               // false
isVersionCompatible(v2, v1);               // true (prerelease < release)
```

---

## 4. Enums Canônicos

Cada enum é exportado como **três coisas**: tipo (`type X`), tuple (`const X_TUPLE = [...] as const`), e predicado (`isX(value)`).

```typescript
import {
  ENGINE_STATES,
  isEngineState,
  BREATH_PHASES,
  isBreathPhase,
  PRIORITY_RANK,
  SEVERITY_RANK,
} from '@araflow/shared-contracts';

if (isEngineState(state)) {
  switch (state) { /* exhaustivo */ }
}

if (PRIORITY_RANK[eventPriority] >= PRIORITY_RANK.high) {
  // dispatch imediatamente
}
```

### 4.1 EngineState

`idle → initializing → ready → running ⇄ paused → stopping → stopped | errored | disposed`

### 4.2 BreathPhase (canônico para engines)

`'inhaling' | 'holdAfterInhale' | 'exhaling' | 'holdAfterExhale'`

> **Nota:** existe um schema separado em `protocol/index.ts` para serialização JSON, com nomes abreviados (`inhale`, `hold-in`, etc.). Engines usam o enum canônico deste módulo.

---

## 5. Patterns

### 5.1 Result<T, E>

Para erros esperados. Substitui `throw` em fronteiras previsíveis (validação, parsing, network).

```typescript
import { Result, Ok, Err, isOk, mapResult, flatMapResult } from '@araflow/shared-contracts';

const parseDuration = (raw: string): Result<Duration, ValidationError> => {
  const n = Number(raw);
  if (!Number.isFinite(n) || n < 0) {
    return Err(new ValidationError(`Invalid: ${raw}`, { code: 'invalid_duration', severity: 'warn' }));
  }
  return Ok(Duration(n));
};

// Encadear
const result = flatMapResult(parseDuration(raw), (d) => {
  if (d > 60_000) return Err(new ValidationError('too long', { code: 'too_long', severity: 'warn' }));
  return Ok(d);
});

if (isOk(result)) {
  use(result.value);
} else {
  log(result.error);
}
```

### 5.2 Option<T>

Para valores opcionais onde ausência é normal (não é erro).

```typescript
import { Option, Some, None, isSome, mapOption, unwrapOptionOr, zip2, firstSome } from '@araflow/shared-contracts';

const findUser = (id: UserId): Option<User> => ...;

const user = findUser(id);
if (isSome(user)) {
  console.log(user.value.name);
}

// zip: Some(1) + Some('a') → Some([1, 'a'])
//      Some(1) + None    → None
const combined = zip2(findUser(a), findUser(b));

// firstSome: [None, None, Some(3)] → Some(3)
const fallback = firstSome([maybeA, maybeB, maybeC]);
```

### 5.3 Either<L, R>

Para quando ambos os ramos carregam dados significativos.

```typescript
import { Either, Left, Right, isRight, mapRight } from '@araflow/shared-contracts';

// Convention: Left = "alternative/negative", Right = "primary/positive"
const result: Either<ParseError, Token> = ...;

if (isRight(result)) {
  consume(result.right);
}
```

### 5.4 Failure

Estrutura para acumular múltiplos erros (compilação, validação batch).

```typescript
import { Failure, groupFailuresBySeverity, hasBlockingFailures } from '@araflow/shared-contracts';

const failures: Failure[] = [
  Failure({ code: 'e1', message: 'first error', severity: 'error', path: 'phases[0]' }),
  Failure({ code: 'w1', message: 'warning',     severity: 'warn' }),
];

if (hasBlockingFailures(failures)) {
  const grouped = groupFailuresBySeverity(failures);
  // grouped.error = [first], grouped.warn = [w1], grouped.info = [], grouped.fatal = []
}
```

---

## 6. Errors

### 6.1 Hierarquia

```
AppError (base)
├── ValidationError     (path?: string)
├── CompilationError    (source?: string)
├── EngineError
├── ProtocolError
├── TimerError
└── BreathError
```

Todos preservam `name`, `code`, `severity`, `context`, `cause`. `instanceof` funciona através de todos os módulos porque `Object.setPrototypeOf` é chamado em cada construtor.

```typescript
import { AppError, ValidationError, EngineError } from '@araflow/shared-contracts';

try {
  doRisky();
} catch (e) {
  if (e instanceof ValidationError) {
    logValidationError(e.path);
  } else if (e instanceof EngineError) {
    logEngineError(e.code);
  } else if (e instanceof AppError) {
    logGeneric(e.code, e.context);
  }
}
```

### 6.2 toJSON() para logs estruturados

```typescript
const err = new ValidationError('bad', {
  code: 'invalid_input',
  severity: 'error',
  context: { field: 'name' },
});
console.log(JSON.stringify(err.toJSON()));
// {
//   "name": "ValidationError",
//   "message": "bad",
//   "code": "invalid_input",
//   "severity": "error",
//   "context": { "field": "name" },
//   "cause": null,
//   "stack": "..."
// }
```

---

## 7. Interfaces

### 7.1 Lifecycle

```typescript
interface Engine {
  readonly id: EngineId;
  readonly state: EngineState;
  snapshot(): unknown;
  subscribe(listener: (event: unknown) => void): Subscription;
  dispose(): void;
}

interface LifecycleController {
  start():  Result<void, EngineError>;
  pause():  Result<void, EngineError>;
  resume(): Result<void, EngineError>;
  stop():   Result<void, EngineError>;
}
```

### 7.2 Observability

```typescript
interface Logger {
  debug(message: string, context?: LogContext): void;
  info(message: string, context?: LogContext): void;
  warn(message: string, context?: LogContext): void;
  error(message: string, context?: LogContext): void;
  fatal(message: string, context?: LogContext): void;
  log(entry: LogEntry): void;
}

interface EventBus<T extends Event = Event> {
  publish(event: T): void;
  subscribe(type: string, listener: EventListener<T>): Subscription;
  subscribeAll(listener: EventListener<T>): Subscription;
  listenerCount(type?: string): number;
  clear(): void;
}
```

### 7.3 Protocol

```typescript
interface Compiler {
  compile(source: ProtocolSource): Result<CompilerResult, CompilationError>;
  validate(source: ProtocolSource): ValidationResult;
}

interface ExecutionPlan {
  readonly protocolId: ProtocolId;
  readonly version: SemanticVersion;
  readonly phases: readonly PhaseStep[];
  readonly totalDuration: Duration;
  readonly cycles: number;
  readonly compiledAt: Iso8601;
  readonly compiledBy: EngineId;
}
```

---

## 8. Events

9 eventos canônicos. Todos estendem `Event` (base com `type`, `monotonicMs`, `priority?`, `engineId?`, `payload?`).

| Evento | Quando |
|--------|--------|
| `EngineStartedEvent` | engine.start() completou |
| `EngineStoppedEvent` | engine.stop() completou (reason: completed/cancelled/errored) |
| `EnginePausedEvent` | engine.pause() |
| `EngineResumedEvent` | engine.resume() |
| `TickEvent` | tick periódico (cadência definida por engine) |
| `PhaseChangedEvent` | BreathPhase mudou (com cycleIndex + phaseProgress) |
| `CycleCompletedEvent` | BreathCycle terminou (com totalCycles + cycleDuration) |
| `ProtocolLoadedEvent` | ProtocolSource foi carregada do loader |
| `ProtocolCompiledEvent` | ExecutionPlan foi compilada |

```typescript
import { CANONICAL_EVENT_TYPES } from '@araflow/shared-contracts';

CANONICAL_EVENT_TYPES.forEach((type) => console.log(type));
// 'engine-started' 'engine-stopped' 'engine-paused' 'engine-resumed'
// 'tick' 'phase-changed' 'cycle-completed' 'protocol-loaded' 'protocol-compiled'
```

---

## 9. Utilities

```typescript
import {
  generateUuidV4,
  validateUuidV4,
  generateUlidLike,
  TIME_UNITS,
  toMilliseconds,
  fromMilliseconds,
  isTimeUnit,
  type DeepReadonly,
  type Immutable,
} from '@araflow/shared-contracts';

const id = generateUuidV4();                  // 'REDACTED'
const ulid = generateUlidLike(Date.now());    // 26-char Crockford base32

const inMs = toMilliseconds(2, 'minute');      // 120_000
const inMin = fromMilliseconds(120_000, 'minute'); // 2

type Snapshot = Immutable<EngineState>;
```

---

## 10. Testes e Cobertura

- **23 suites, 299 testes** — todos passando
- **100% Statements / Branches / Functions / Lines**

```
File                   % Stmts % Branch % Funcs % Lines
REDACTED
enums/                       100      100     100     100
errors/                      100      100     100     100
events/                      100      100     100     100
patterns/                    100      100     100     100
utilities/                   100      100     100     100
value-objects/               100      100     100     100
REDACTED
TOTAL                        100      100     100     100
```

Para rodar:
```bash
cd shared-contracts
npm test         # roda testes
npm run coverage # verifica 100% em todos os thresholds
```

---

## 11. Como Consumir

```typescript
// Em qualquer package do monorepo
import {
  // Value objects
  Duration, DurationFromSeconds, Timestamp, Iso8601,
  ProtocolId, EngineId, SemanticVersion,
  // Enums
  type EngineState, type BreathPhase,
  ENGINE_STATES, isEngineState, BREATH_PHASES,
  // Patterns
  Result, Ok, Err, isOk,
  Option, Some, None, isSome,
  // Errors
  AppError, ValidationError, EngineError,
  // Interfaces
  type Engine, type Logger, type EventBus,
  // Events
  type EngineStartedEvent, type TickEvent,
  CANONICAL_EVENT_TYPES,
} from '@araflow/shared-contracts';
```

---

## 12. Próximas Sprints

- **Sprint 3 (Protocol Engine):** implementará `Compiler`, `ProtocolSourceLoader` consumindo estes contratos.
- **Sprint 4 (Session Engine):** usará `Engine`, `LifecycleController`, eventos canônicos.
- **Sprint 5+ (Audio / Animation / Analytics / Safety):** cada engine implementa `Engine` + emite eventos canônicos.

> **Pare.** Nenhum engine pode adicionar tipos que já existem aqui. Se precisar de algo novo, primeiro adicione ao shared-contracts, depois consuma.
