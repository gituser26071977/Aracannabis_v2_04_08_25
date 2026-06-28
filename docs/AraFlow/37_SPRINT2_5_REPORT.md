# 37 — Sprint 2.5 Report: Core Contracts

**Sprint:** 2.5 (entre Sprint 2 Breath Engine e Sprint 3 Protocol Engine)
**Status:** ✅ Concluído
**Período:** 2026-06-24 → 2026-06-25
**Versão entregue:** `shared-contracts@2.5.0`

---

## Sumário Executivo

A Sprint 2.5 entregou o **módulo `@araflow/shared-contracts`** como Constituição Técnica do AraFlow. Este módulo é o ponto único e oficial de definição de tipos, enums, patterns, errors, interfaces e eventos compartilhados entre mobile, backend e qualquer futuro consumidor.

**Métricas-chave:**

| Métrica | Valor |
|---------|-------|
| Arquivos criados | 21 |
| Linhas de código (src) | ~970 |
| Linhas de testes | ~1.850 |
| Testes | **299** (todos passando) |
| Suites de teste | 23 |
| Cobertura de statements | **100%** |
| Cobertura de branches | **100%** |
| Cobertura de functions | **100%** |
| Cobertura de lines | **100%** |
| TODO / FIXME | **0** |
| `any` types | **0** |
| Dependências de framework | **0** |

---

## Entregas

### 1. Value Objects (`src/value-objects/`)

Tipos primitivos com validação no construtor. Branded types garantem identidade em compile-time.

| Arquivo | Conteúdo |
|---------|----------|
| `validation.ts` | `AppError` (base), helpers `isNonEmptyString`, `isFiniteNumber`, `isInteger`, `isInRange` |
| `ids.ts` | `Brand<T,B>`, `ProtocolId`, `SessionId`, `EngineId`, `TenantId`, `UserId`, `PatientId` (todos validados por ULID ou kebab-case regex) |
| `numeric.ts` | `Duration`, `DurationFromSeconds`, `DurationFromMinutes`, `DurationZero`, `Timestamp`, `TimestampNow`, `timestampDifference`, `Percentage`, `Progress`, `ProgressFromPercentage`, `CycleIndex`, `PhaseIndex`, `Iso8601`, `Iso8601FromTimestamp`, `Iso8601ToTimestamp` |
| `version.ts` | `SemanticVersion`, `parseSemanticVersion`, `compareSemanticVersions`, `isVersionCompatible` (semver.org compliance) |

### 2. Enums Canônicos (`src/enums/`)

Cada enum exporta: tipo, tuple `as const`, predicado `isX()`, e rank record (quando ordenado).

| Arquivo | Conteúdo |
|---------|----------|
| `state.ts` | `ENGINE_STATES` (9 valores), `PROTOCOL_STATES` (6), `SESSION_STATES` (8) |
| `breath.ts` | `BREATH_PHASES` (4), `CURVE_TYPES` (7), `INTERPOLATION_TYPES` (3) |
| `priority.ts` | `PRIORITIES` (6) + `PRIORITY_RANK`, `SEVERITIES` (4) + `SEVERITY_RANK` |
| `types.ts` | `CurveFn` type alias |

### 3. Patterns (`src/patterns/`)

Funções puras, frozen at runtime.

| Pattern | Operações |
|---------|-----------|
| `Result<T,E>` | `Ok`, `Err`, `isOk`, `isErr`, `mapResult`, `mapError`, `flatMapResult`, `unwrap`, `unwrapOr`, `allResults` |
| `Option<T>` | `Some`, `None`, `isSome`, `isNone`, `mapOption`, `flatMapOption`, `unwrapOptionOr`, `zip2`, `firstSome` |
| `Either<L,R>` | `Left`, `Right`, `isLeft`, `isRight`, `mapLeft`, `mapRight`, `unwrapEither` |
| `Failure` | `Failure`, `isFailure`, `groupFailuresBySeverity`, `hasBlockingFailures` |

### 4. Utilities (`src/utilities/`)

| Arquivo | Conteúdo |
|---------|----------|
| `readonly.ts` | `DeepReadonly<T>`, `Immutable<T>` |
| `uuid.ts` | `generateUuidV4`, `validateUuidV4`, `generateUlidLike` (Crockford base32 sortable) |
| `time-unit.ts` | `TIME_UNITS` (5), `toMilliseconds`, `fromMilliseconds`, `isTimeUnit` |

### 5. Interfaces (`src/interfaces/`)

Contratos de comportamento, sem implementação.

| Categoria | Interfaces |
|-----------|------------|
| Lifecycle | `Disposable`, `Subscription`, `Engine`, `LifecycleController` |
| Infrastructure | `Clock`, `Scheduler`, `ScheduledTask`, `TaskCallback`, `MonotonicMs`, `WallClockMs` |
| Observability | `Logger`, `LogContext`, `LogEntry`, `MetricsCollector`, `Counter`, `Gauge`, `Histogram`, `Event`, `EventListener`, `EventBus` |
| Protocol | `ProtocolSource`, `ProtocolSourceFormat`, `ProtocolSourceLoader`, `ExecutionPlan`, `PhaseStep`, `CompilerResult`, `ValidationResult`, `Compiler` |

### 6. Events (`src/events/`)

9 eventos canônicos. Todos estendem `Event`:

- `EngineStartedEvent`, `EngineStoppedEvent`, `EnginePausedEvent`, `EngineResumedEvent`
- `TickEvent`, `PhaseChangedEvent`, `CycleCompletedEvent`
- `ProtocolLoadedEvent`, `ProtocolCompiledEvent`

Plus `CANONICAL_EVENT_TYPES` tuple e `CanonicalEvent` discriminated union.

### 7. Errors (`src/errors/`)

Hierarquia tipada, todos estendem `AppError`:

- `ValidationError` (path field)
- `CompilationError` (source field)
- `EngineError`, `ProtocolError`, `TimerError`, `BreathError`

`instanceof` funciona através de módulos via `Object.setPrototypeOf`.

### 8. Public API (`src/index.ts`)

Barrel re-exporta tudo. `SHARED_CONTRACTS_VERSION = '2.5.0'`.

---

## Testes (`__tests__/`)

23 suites, 299 testes, 100% cobertura em todas as métricas.

| Suite | Testes |
|-------|--------|
| `value-objects/validation.test.ts` | 27 |
| `value-objects/ids.test.ts` | 27 |
| `value-objects/numeric.test.ts` | 47 |
| `value-objects/version.test.ts` | 26 |
| `enums/state.test.ts` | 9 |
| `enums/breath.test.ts` | 12 |
| `enums/priority.test.ts` | 10 |
| `enums/types.test.ts` | 3 |
| `patterns/result.test.ts` | 18 |
| `patterns/option.test.ts` | 20 |
| `patterns/either.test.ts` | 11 |
| `patterns/failure.test.ts` | 11 |
| `utilities/readonly.test.ts` | 2 |
| `utilities/uuid.test.ts` | 11 |
| `utilities/time-unit.test.ts` | 13 |
| `errors/base.test.ts` | 16 |
| `errors/index-re-export.test.ts` | 1 |
| `events/lifecycle.test.ts` | 11 |
| `interfaces/lifecycle.test.ts` | 4 |
| `interfaces/infrastructure.test.ts` | 2 |
| `interfaces/observability.test.ts` | 5 |
| `interfaces/protocol.test.ts` | 6 |
| `index.test.ts` | 8 |
| **TOTAL** | **299** |

### Highlights de cobertura

- **Branded IDs:** todos os 6 construtores validados para input válido, vazio, formato inválido, e código de erro correto.
- **Duration:** todas as fronteiras (zero, MAX, negativo, NaN, Infinity, não-inteiro) testadas. Conversões round-trip.
- **SemanticVersion:** comparação de prerelease, build metadata, identificadores numéricos vs lexicais.
- **Result/Option/Either:** todos os paths de cada helper testados (ok, err, mapeamento, encadeamento, all/zip/first).
- **Errors:** cada subclasse testada para herança correta (`instanceof AppError`, `instanceof Error`), preservação de `code`/`severity`/`context`/`cause`/`path`/`source`.
- **Events:** cada um dos 9 eventos canônicos tem shape test; `CANONICAL_EVENT_TYPES` é exaustivo.
- **Public API:** smoke test end-to-end constrói IDs, valida, e monta um `ProtocolCompiledEvent` para garantir que tudo se conecta.

---

## Decisões Arquiteturais

### D1. Branded types com `__brand` property

```typescript
export type Brand<T, B extends string> = T & { readonly __brand: B };
```

Escolhido em vez de `unique symbol` porque permite composição (ex.: `Brand<Brand<string, 'A'>, 'B'>`) e serializa melhor em logs/errors. Existe um `Brand` legado em `common.ts` com `unique symbol`; ambos coexistem (legacy continua válido).

### D2. Erros lançam `AppError`, não `Error`

Construtores de value object lançam `AppError` com `code` + `severity` + `context`. Benefícios:
- Type narrowing via `instanceof`.
- Pattern matching via `code`.
- Logging estruturado via `toJSON()`.

### D3. Frozen pattern objects

`Ok`, `Err`, `Some`, `None`, `Left`, `Right`, `Failure` retornam `Object.freeze(...)`. Previne mutação acidental — fundamental para value objects imutáveis.

### D4. `parseSemanticVersion` sem defensive guard

Versões inválidas são rejeitadas pelo regex no construtor. Dentro do parser, os fallbacks `?? '0'` foram removidos porque são unreachable. Cobertura 100% exige não ter código morto.

### D5. Default code removido

A primeira versão tinha `options.code ?? 'validation_error'` em cada subclasse. Como `code` é required em `AppErrorOptions`, o fallback nunca dispara. Removido para clareza.

### D6. `BreathPhase` canônico vs schema de serialização

Dois namespaces diferentes:
- `BREATH_PHASES` em `enums/breath.ts` — para runtime dos engines: `'inhaling'`, `'holdAfterInhale'`, `'exhaling'`, `'holdAfterExhale'`.
- `BreathPhaseTypeSchema` em `protocol/index.ts` — para JSON/IPC: `'inhale'`, `'hold-in'`, `'exhale'`, `'hold-out'`.

Ambos documentados. Engines usam o canônico. Conversão acontece na borda IPC (próxima sprint).

---

## Quality Gates (todos verdes)

- ✅ TypeScript strict mode (incluindo `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`)
- ✅ 299 testes passando
- ✅ 100% cobertura em 4 métricas
- ✅ Zero `any` types
- ✅ Zero TODO / FIXME
- ✅ Zero dependências de framework (React, RN, Node, Browser)
- ✅ ESLint sem warnings

---

## Compatibilidade com Sprints Anteriores

- `Timer Engine` (Sprint 1): nenhuma quebra — `Duration`, `Timestamp`, `EngineState` agora vêm do shared-contracts, mas são type-compatible.
- `Breath Engine` (Sprint 2): idem. `BreathPhase` no engine (`'inhaling'`) é o mesmo do `BREATH_PHASES` no shared-contracts.
- `common.ts` (legacy): preservado, exportado como `Legacy*` para evitar quebra.

---

## Próximos Passos

> **Pare.** A Sprint 3 (Protocol Engine) **deve** consumir estes contratos integralmente. Antes da Sprint 3 começar:
>
> 1. Migrar `mobile/src/core/timer-engine` para importar `EngineId`, `Duration`, `Timestamp`, `EngineState`, `Result`, `EngineError`, `TimerError` do shared-contracts.
> 2. Migrar `mobile/src/core/breath-engine` idem + usar `BreathPhase` canônico.
> 3. Sprint 3 começa com `Protocol Engine` consumindo `Compiler`, `ProtocolSource`, `ExecutionPlan`, `PhaseStep`, `ProtocolCompiledEvent`, `ProtocolError`.

---

## Arquivos Entregues

```
shared-contracts/
├── jest.config.js                              (NOVO)
├── package.json                                (atualizado: jest + ts-jest deps)
├── src/
│   ├── index.ts                                (NOVO — barrel)
│   ├── value-objects/
│   │   ├── validation.ts                       (NOVO)
│   │   ├── ids.ts                              (NOVO)
│   │   ├── numeric.ts                          (NOVO)
│   │   ├── version.ts                          (NOVO)
│   │   └── index.ts                            (NOVO)
│   ├── enums/
│   │   ├── state.ts                            (NOVO)
│   │   ├── breath.ts                           (NOVO)
│   │   ├── priority.ts                         (NOVO)
│   │   ├── types.ts                            (NOVO)
│   │   └── index.ts                            (NOVO)
│   ├── patterns/
│   │   ├── result.ts                           (NOVO)
│   │   ├── option.ts                           (NOVO)
│   │   ├── either.ts                           (NOVO)
│   │   ├── failure.ts                          (NOVO)
│   │   └── index.ts                            (NOVO)
│   ├── utilities/
│   │   ├── readonly.ts                         (NOVO)
│   │   ├── uuid.ts                             (NOVO)
│   │   ├── time-unit.ts                        (NOVO)
│   │   └── index.ts                            (NOVO)
│   ├── interfaces/
│   │   ├── lifecycle.ts                        (NOVO)
│   │   ├── infrastructure.ts                   (NOVO)
│   │   ├── observability.ts                    (NOVO)
│   │   ├── protocol.ts                         (NOVO)
│   │   └── index.ts                            (NOVO)
│   ├── events/
│   │   ├── lifecycle.ts                        (NOVO)
│   │   └── index.ts                            (NOVO)
│   └── errors/
│       ├── base.ts                             (NOVO)
│       └── index.ts                            (NOVO)
├── __tests__/
│   ├── index.test.ts                           (NOVO — public API smoke)
│   ├── value-objects/ (4 files)
│   ├── enums/ (4 files)
│   ├── patterns/ (4 files)
│   ├── utilities/ (3 files)
│   ├── errors/ (2 files)
│   ├── events/ (1 file)
│   └── interfaces/ (4 files)
└── docs/
    ├── docs/AraFlow/37_CORE_CONTRACTS.md       (NOVO)
    ├── docs/AraFlow/37_SPRINT2_5_REPORT.md     (este arquivo)
    └── docs/adr/araflow/021-core-contracts.md  (NOVO)
```

---

**Aprovação para Sprint 3 (Protocol Engine):** aguardando luz verde humana.
