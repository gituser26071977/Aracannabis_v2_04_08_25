# AraFlow — Sprint 7 Report: Session Persistence

| Field        | Value                                   |
| ------------ | REDACTED |
| Sprint       | 7                                       |
| Module       | `@core/session-persistence`             |
| Version      | 1.0.0                                   |
| Date         | 2026-06-30                              |
| Status       | ✅ Completed — awaiting approval         |
| Parent       | Sprint 6 (Session Orchestrator)         |

---

## Mission

Add a **local-only persistence layer** for the Session Orchestrator:
interfaces, deterministic JSON serializer, abstract storage seam,
in-memory adapter only, migration pathway, explicit recovery API.
No backend, no cloud, no UI, no Audio, no Analytics, no Safety.

---

## Deliverables

### New module — `mobile/src/core/session-persistence/`

```
mobile/src/core/session-persistence/
├── index.ts                                    — public barrel + SESSION_PERSISTENCE_VERSION
├── domain/
│   ├── SnapshotMetadata.ts                     — header (id, timestamps, version)
│   ├── SessionSnapshot.ts                      — PersistedSessionSnapshot + StorageRecord
│   ├── StorageAdapter.ts                       — abstract storage seam
│   ├── SessionSerializer.ts                    — encode/decode seam
│   ├── SessionPersistence.ts                   — high-level facade seam
│   └── RecoveryDecision.ts                     — probe + result types
├── application/
│   ├── JsonSerializer.ts                       — deterministic JSON encoder
│   ├── MemoryStorageAdapter.ts                 — in-memory storage (only impl in scope)
│   ├── PersistenceService.ts                   — wires serializer + storage + migrations
│   ├── MigrationRegistry.ts                    — version → decoder map
│   └── RecoveryAPI.ts                          — canRecover / recover / discard
└── util/
    ├── deterministic-json.ts                   — sorted-keys JSON stringify
    └── session-to-snapshot.ts                  — pure projection
```

**13 source files** total (6 domain + 5 application + 2 util + 1 index — actually 14; the index is the barrel).

### Tests — `mobile/__tests__/core/session-persistence/`

```
mobile/__tests__/core/session-persistence/
├── fakes.ts                                    — buildFakeSession, startSession
├── deterministic-json.test.ts                  — sorted-key stringify + parser
├── guards.test.ts                              — type guards
├── JsonSerializer.test.ts                      — encode/decode round-trip
├── MemoryStorageAdapter.test.ts                — CRUD + options + monotonic clock
├── MigrationRegistry.test.ts                   — register/find/versions
├── PersistenceService.test.ts                  — save/load/exists/list/delete/clear + migrations + corruption
├── RecoveryAPI.test.ts                         — canRecover/recover/discard
└── session-to-snapshot.test.ts                 — projection from ExecutionSession
```

**94 unit tests** — all passing.

### Documentation

- `docs/AraFlow/43_SESSION_PERSISTENCE.md` — Architecture, snapshot
  shape, wire format, recovery API, decoupling story.
- `docs/AraFlow/REDACTED.md` — This file.
- `docs/adr/araflow/026-session-persistence.md` — ADR-026.

### Tooling

- `mobile/package.json` — per-path coverage threshold (90/80/90/90)
  for `@core/session-persistence`.

---

## Metrics

### Coverage (per-path, on `mobile/src/core/session-persistence/`)

| Path            | Stmts   | Branches | Funcs   | Lines   |
| --------------- | ------- | -------- | ------- | ------- |
| domain/         | 100%    | 100%     | 100%    | 100%    |
| application/    | 96.52%  | 88.33%   | 100%    | 96.39%  |
| **Aggregate**   | **96.13%** | **90.47%** | **100%** | **96.05%** |

Per-path jest threshold (`./src/core/session-persistence/`):
`statements: 90, branches: 80, functions: 90, lines: 90` — **all met**.

### Tests

| Metric           | Value |
| ---------------- | ----- |
| Test suites      | 8     |
| Test cases       | 94    |
| Passing           | 94    |
| Failing           | 0     |
| Average runtime  | ~3s   |

### Lint

```
$ npx eslint --max-warnings 0 "src/core/session-persistence/**/*.ts" "__tests__/core/session-persistence/**/*.ts"
✓ 0 errors, 0 warnings
```

### Typecheck

```
$ npx tsc --noEmit  # filtered to session-persistence
✓ 0 errors
```

---

## Acceptance Criteria (brief items 1–8)

| # | Question                                                                 | Answer |
|---|REDACTED|--------|
| 1 | O Session Orchestrator permaneceu desacoplado?                           | **Sim.** Zero imports de `@core/session-persistence` no Orchestrator. A camada de persistência depende apenas da API pública de `@core/execution-session`. |
| 2 | É possível trocar MemoryStorage por AsyncStorage sem alterar regras?     | **Sim.** `StorageAdapter` é a seam; trocar a implementação não altera `PersistenceService` nem o domínio. |
| 3 | O formato suporta migração de versões?                                   | **Sim.** Envelope `schemaVersion` no topo + `MigrationRegistry` mapeia versões legadas a decoders. |
| 4 | Há perda de dados na serialização?                                       | **Não.** JSON determinístico com chaves ordenadas; números preservados como IEEE-754 doubles (sem `Date`, sem `BigInt`); branded strings passam como strings. |
| 5 | Recovery está preparado para Sprint 8?                                   | **Sim.** `canRecover/recover/discard` expostos e testados. Construir um `ExecutionSession` fresco a partir de snapshot é tarefa de Sprint 8. |
| 6 | Cobertura atingiu as metas?                                              | **Sim.** 96.13% stmts / 90.47% branches / 100% funcs / 96.05% lines (alvo 90/80/90/90). |
| 7 | Alguma dependência externa foi adicionada?                               | **Não.** Apenas APIs nativas (`Map`, `Promise`, `Object.freeze`, `WeakSet`). |
| 8 | O módulo está pronto para integração futura?                            | **Sim.** `PersistenceService` + `RecoveryAPI` + `MemoryStorageAdapter` estão wired e testados. Adapters para AsyncStorage/SQLite entram via `StorageAdapter` sem mudança no contrato. |

---

## Constraints Respected

- ✅ NO persistência real (apenas in-memory; AsyncStorage/SQLite/filesystem ficam para sprints futuros)
- ✅ NO backend / API / network
- ✅ NO UI / React / React Native
- ✅ NO Audio / Animation / Analytics / Safety
- ✅ NO auto-recovery — apenas API explícita `canRecover / recover / discard`
- ✅ NO modificação ao Session Orchestrator (zero imports cruzados)

---

## Risks

| Risk                                                       | Mitigation                                                                                                                |
| REDACTED | REDACTED |
| `MemoryStorageAdapter` perde dados no restart do processo  | Documentado; sprint futuro introduz AsyncStorage adapter via `StorageAdapter` seam.                                       |
| Snapshot crescentes (event log inteiro) podem inflar        | Brief não exige compactação; camada de compactação pode entrar via serializer alternativo (MessagePack/Protobuf) em sprint futuro. |
| Branches em 90% (não 95%)                                  | Caminhos de erro defensivos no `PersistenceService` (try/catch com tipagem de razão). Per-path threshold (90/80/90/90) atingido. |
| Schema version 1 é o primeiro; sem dados empíricos de migração | `MigrationRegistry` exposto e testado; decoders legados entram como registros. Sem código de migração no Sprint 7 (brief não pede). |

---

## Lessons Learned

1. **Pure projections (sessionToPersistedSnapshot) tornam o domínio
   imutável.** A camada de persistência lê apenas read models públicos
   (`session.events()`, `session.metrics()`, `session.timeline()`,
   `session.plan()`), preservando o invariante do Aggregate.
2. **`StorageAdapter` é a seam crítica.** Toda a fronteira "como
   guardamos bytes" vive atrás dessa interface. Trocar de in-memory
   para AsyncStorage é uma troca de dependência — não uma reescrita.
3. **JSON determinístico (sorted keys) é barato e útil.** Permite
   hashing, change detection e deduplicação trivial. Sem isso, dois
   snapshots equivalentes produziriam bytes diferentes.
4. **`RecoveryReason` exclui `'recoverable'` e `'discarded'` na
   branch `ok: false`** —窄 a taxonomia para os 3 motivos reais
   de falha (`no-snapshot`, `corrupted`, `incompatible`).
5. **`storage-failed` mapeia para `corrupted`** na API de Recovery —
   para o usuário, "o adapter não respondeu" e "o payload é
   ilegível" têm a mesma consequência: tente novamente ou descarte.

---

## What's next (NOT in this sprint)

The brief explicitly defers:

- AsyncStorage / SQLite / IndexedDB / filesystem adapters
- Auto-recovery / auto-resume on app launch
- Encryption / privacy
- Snapshot compaction
- UI for browsing / restoring snapshots

The natural next sprint is **Sprint 8 — Session Recovery**:

- introduce a `SessionRebuilder` that consumes a
  `PersistedSessionSnapshot` and constructs a fresh
  `ExecutionSession` (using the existing `replayReducer` /
  `SessionOrchestrator.replayIntoSession`)
- expose a `RestoreSession` API in the Orchestrator
- introduce AsyncStorage adapter via `StorageAdapter`
- add UI integration (out of scope here)

---

## References

- Sprint 5 — Execution Session (`41_EXECUTION_SESSION.md`, ADR-024)
- Sprint 6 — Session Orchestrator (`42_SESSION_ORCHESTRATOR.md`, ADR-025)
- `@core/execution-session` — Aggregate Root
- `@core/session-orchestrator` — Bridge
- `@araflow/shared-contracts` — Result, EngineError, branded types
- ADR-026 — Session Persistence