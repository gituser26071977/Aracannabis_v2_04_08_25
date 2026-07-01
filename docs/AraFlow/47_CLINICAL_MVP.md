# 47 — Clinical MVP — Architecture

> **The Multisensory Experience — Phase 3.0 — Integration**
> Período: 2026-07-01
> Status: **Concluído — aguardando aprovação humana**

---

## 1. Propósito

Documentar a arquitetura do **primeiro MVP clínico end-to-end** do AraFlow:
uma única tela capaz de conduzir uma sessão respiratória completa do início
ao fim, capturando o feedback subjetivo do paciente. Este documento é o
companheiro técnico do relatório executivo
[`47_SPRINT11_CLINICAL_MVP_REPORT.md`](47_SPRINT11_CLINICAL_MVP_REPORT.md).

A única métrica de sucesso do brief:

> *"Um médico deverá conseguir abrir o aplicativo e concluir uma sessão
> respiratória completa sem auxílio técnico."*

---

## 2. Restrições do brief (escopo invertido)

| NÃO fazer                                                       | Status |
|REDACTED|--------|
| Login / onboarding                                              | ✅ |
| Backend / sincronização                                         | ✅ |
| Analytics / wearables / IA                                      | ✅ |
| Múltiplas telas / múltiplos idiomas além de pt-BR / en-US       | ✅ |
| `expo-av` / áudio real                                          | ✅ |
| Modificar QUALQUER módulo do `@core/*`                          | ✅ (frozen) |
| Criar novos Engines                                             | ✅ |
| Adicionar protocolos além dos 3                                 | ✅ |

Toda a Sprint 11 vive em **`mobile/src/features/session/Clinical/`** e em
alterações cirúrgicas em `App.tsx` / `package.json`. Nada além disso.

---

## 3. Visão geral

```
┌──────────────────────────────────────────────────────────────────────┐
│                         ClinicalScreen.tsx                            │
│                       (React Native, 3 phases)                        │
│                                                                       │
│   phase = 'select'                                                    │
│       │                                                               │
│       │ tap card                                                      │
│       ▼                                                               │
│   phase = 'session'                                                   │
│       │                                                               │
│       │ start / pause / resume / stop                                 │
│       │   (rAF tick → handle.update() → renderer.render(scene))       │
│       │                                                               │
│       │ terminal status                                               │
│       ▼                                                               │
│   phase = 'feedback'                                                  │
│       │                                                               │
│       │ tap emoji                                                     │
│       │   saveFeedback()  ──────────────►  AsyncStorage                │
│       ▼                                                               │
│   phase = 'select'  (loop)                                            │
└──────────────────────────────────────────────────────────────────────┘
            │
            │ startClinicalSession({ protocol, audioAdapter, storageAdapter })
            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       ClinicalSession.ts                              │
│                  (Pure TS — no React, no RN, no UI)                  │
│                                                                       │
│   ┌──────────────┐   ┌──────────────────┐   ┌────────────────────┐    │
│   │ RuntimeEngine│──►│ AnimationEngine  │──►│ currentFrame()     │    │
│   │  @core/      │   │  @core/          │   │ (returned to UI)   │    │
│   │  runtime     │   │  animation-engine│   └────────────────────┘    │
│   └──────┬───────┘   └──────────────────┘                            │
│          │ event stream (deduped)                                     │
│          ├──────────────► AudioEngine (@core/audio-engine)            │
│          │                  └─► InMemoryAudioAdapter                  │
│          │                                                            │
│          ├──────────────► SessionOrchestrator (@core/...)             │
│          │                  └─► ExecutionSession (aggregate)          │
│          │                                                            │
│          └──────────────► AnimationRenderer (@presentation/...)       │
│                            └─► RN primitives (no Skia)                │
│                                                                       │
│   on natural completion ─► PersistenceService.save(snapshot)          │
└──────────────────────────────────────────────────────────────────────┘
```

**Princípios:**

1. **Core é intocado.** Todo o trabalho é composição em `features/`.
2. **Engine reage, não orquestra.** `ClinicalSession` só conecta engines
   já existentes; nenhum timer próprio, nenhuma chamada a `Date.now()`.
3. **Cancellation ≠ completion.** Apenas a conclusão natural dispara
   `onPersist`; cancelamentos saem sem persistir.

---

## 4. Os três protocolos

| id (ULID)                          | Nome                        | Ciclos | Fases                                          | Total |
|REDACTED|-----------------------------|-------:|REDACTED|------:|
| `01ARZ3NDEKTSV4RRFFQ69G5FA2`       | Respiração Diafragmática    |      6 | inhale 4 s · hold-in 4 s · exhale 6 s          | ~84 s |
| `01ARZ3NDEKTSV4RRFFQ69G5FBX`       | Respiração Quadrada 4-4-4-4 |      6 | inhale 4 s · hold-in 4 s · exhale 4 s · hold-out 4 s | ~96 s |
| `01ARZ3NDEKTSV4RRFFQ69G5PHY`       | Suspiro Fisiológico         |      8 | inhale 2 s · inhale 0,5 s · exhale 6 s          | ~68 s |

Cada JSON traz `version`, `metadata.references` (Huberman / NIH / Cell
Reports Medicine), `evidenceLevel: A`, `approvedAt: 2026-07-01`. Os ULIDs
são válidos segundo o pattern Crockford base32 de 26 caracteres exigido
pelo `ProtocolId` constructor (`@araflow/shared-contracts`).

---

## 5. Fluxo de uma sessão

```
clinical.start({ protocol, audioAdapter, storageAdapter })
   │
   ├─► runtime.compile(JsonSource(protocol.source))
   │
   ├─► runtime.subscribe(handler)
   │      │
   │      ├─ phase-changed ─► animation + audio + orchestrator reagem
   │      ├─ breath-started
   │      ├─ timer-started
   │      ├─ runtime-completed  ─► ClinicalSession dispara onPersist
   │      └─ runtime-cancelled  ─► ClinicalSession NÃO dispara onPersist
   │
   ├─► animation.subscribe(frame => handle._frame = frame)
   │
   └─► handle retornado à UI: start / pause / resume / stop / dispose
```

A UI faz **um único** `rAF tick`:

```ts
useEffect(() => {
  if (phase !== 'session') return;
  let raf = 0;
  const tick = () => {
    const frame = handle.update();        // ClinicalSession.update()
    if (frame !== null) {
      const scene = animationFrameToScene(frame);
      renderer.render(scene);
    }
    if (isTerminal(handle.status())) {
      setPhase('feedback');
      return;
    }
    raf = requestAnimationFrame(tick);
  };
  raf = requestAnimationFrame(tick);
  return () => cancelAnimationFrame(raf);
}, [phase, handle]);
```

`animationFrameToScene` e o renderer (`ReactNativeRenderer`) vêm do
Sprint 9 — não foram modificados.

---

## 6. Mapa de integração

| Componente (Sprint)                       | Como Sprint 11 o usa                              |
|REDACTED|REDACTED|
| `@core/runtime` (3)                       | Hospeda o protocolo; emite eventos               |
| `@core/protocol-compiler` (3)             | `JsonSource(...)` → ProtocolPlan                 |
| `@core/execution-session` (5)             | Aggregate root do estado da sessão               |
| `@core/session-orchestrator` (6)          | Bridge Runtime ↔ ExecutionSession                |
| `@core/session-persistence` (7)           | `createMemoryStorageAdapter` (in-memory MVP)     |
| `@core/animation-engine` (8)              | `createAnimation({ runtime })` → breath circle   |
| `@presentation/animation-renderer` (9)    | `createReactNativeRenderer` + `animationFrameToScene` |
| `@core/audio-engine` (10)                 | `createAudioEngine` + `createInMemoryAudioAdapter` |
| `@araflow/shared-contracts/value-objects/ids` | `SessionId(ulid)` — branded type              |
| `mobile/src/shared/theme/tokens.ts`       | Cores / espaçamento / raio / motion              |
| `mobile/src/shared/i18n/I18nProvider.tsx` | `useTranslation('common')` para labels           |

**Zero linhas foram alteradas em qualquer `@core/*` ou `@presentation/*`
durante a Sprint 11.** Verificado por `git diff --stat mobile/src/core/`
(retorna vazio).

---

## 7. Feedback storage (local-only)

`features/session/Clinical/feedback/FeedbackStorage.ts` envolve
`AsyncStorage` (mock oficial
`@react-native-async-storage/async-storage/jest/async-storage-mock` em
testes).

| Operação        | Chave                                  | Conteúdo                       |
|-----------------|REDACTED|--------------------------------|
| `saveFeedback`  | `araflow.feedback.<sanitized-iso>`     | JSON do `FeedbackRecord`       |
| índice          | `araflow.feedback.index`               | array de chaves                |
| `listFeedback`  | (varre o índice)                       | array de `FeedbackEntry`       |
| `clearAllFeedback` | remove todas as chaves + índice     | (uso de teste / debug)         |

`FeelingAfter` é uma union literal de 5 valores, **sem strings livres**:

```ts
type FeelingAfter = 'much-worse' | 'worse' | 'same' | 'better' | 'much-better';
```

`isFeedbackRecord` rejeita qualquer valor fora do conjunto, provando que
dados parciais / corrompidos em AsyncStorage não conseguem entrar no
shape do app.

> **Limitação documentada:** `AsyncStorage` é apagado pelo usuário ao
> desinstalar o app. Não há migração para backend nesta Sprint. Ver §10.

---

## 8. Identidade de sessão

`ClinicalSession` gera um ULID de 26 caracteres via
`buildClinicalSessionUlid(monotonicMs, randomTail)` — implementação
própria (Crockford base32, exclui `I`, `L`, `O`, `U`), mantendo o módulo
independente da lib `ulid` no Core. O resultado é embrulhado pelo
constructor branded:

```ts
import { SessionId } from '@araflow/shared-contracts/value-objects/ids';
const sessionId = SessionId(buildClinicalSessionUlid(now, randTail));
```

`SessionId` é o mesmo tipo aceito por `SessionOrchestrator` e
`PersistenceService`, garantindo que a sessão gerada pelo MVP é
serializável quando um adapter real de persistência chegar.

---

## 9. Erros e cancelamento

`startClinicalSession` retorna `Result<ClinicalSessionHandle, EngineError>`.
Erros prováveis:

| `code`                  | Causa                                      |
|-------------------------|REDACTED|
| `invalid_protocol_id`   | JSON com id fora do pattern ULID           |
| `protocol_compile_failed` | JSON não casa o schema do compilador     |
| `audio_adapter_error`   | Adapter já disposed                        |

**Política de cancelamento:** se o usuário chama `handle.stop()` (botão
"Pular" / "Sair"), a sessão:

1. Para Runtime + Audio + Animation.
2. Dispara `runtime.cancelled`.
3. **NÃO** chama `onPersist` — não há snapshot persistido.

A UI ainda mostra a tela de feedback após `stop()`, mas o registro gravado
carrega `completed: false` para distinguir cancelamento de conclusão
natural.

---

## 10. Limitações aceitas pelo MVP

| Limitação                                         | Aceito por | Próximo passo        |
|REDACTED|-----------:|----------------------|
| Persistência in-memory (não sobrevive ao reload)  |   Sprint 11 | `AsyncStorageAdapter` real em Sprint 12 |
| `InMemoryAudioAdapter` (sem áudio real)           |   Sprint 11 | `ExpoAvAudioAdapter` em Sprint 12 |
| Sem roteamento (uma única tela)                   | brief       | Sprint 13+           |
| Sem login / multi-tenant                          | brief       | Fora de escopo       |
| Sem telemetria clínica                            | brief       | Sprint 14+           |
| Sem export / PDF clínico                          | brief       | Sprint 15+           |
| Sem acessibilidade WCAG completa                  |   Sprint 11 | Auditar em Sprint 13 |
| Sem testes E2E Detox / Maestro                    |   Sprint 11 | Sprint 13            |

---

## 11. Como rodar localmente

```bash
cd mobile
npm install                       # se ainda não rodou
npx jest --testPathPattern="features/session/Clinical"   # 32 / 32
npx jest --coverage --testPathPattern="features/session/Clinical"
```

A cobertura por camada (`features/session/Clinical/`):
- statements ≥ 95
- branches ≥ 90
- functions ≥ 95
- lines ≥ 95

(O threshold está registrado em `mobile/package.json` em
`jest.coverageThreshold`.)

---

## 12. Leitura adicional

| Documento                                              | Conteúdo                           |
|REDACTED|REDACTED|
| [`46_AUDIO_ENGINE.md`](46_AUDIO_ENGINE.md)             | Engine de áudio (Sprint 10)        |
| [`45_FIRST_VISUAL_EXPERIENCE.md`](45_FIRST_VISUAL_EXPERIENCE.md) | Renderer RN (Sprint 9)   |
| [`44_ANIMATION_ENGINE.md`](44_ANIMATION_ENGINE.md)     | Animation Engine (Sprint 8)        |
| [`43_SESSION_PERSISTENCE.md`](43_SESSION_PERSISTENCE.md) | Persistência (Sprint 7)          |
| [`42_SESSION_ORCHESTRATOR.md`](42_SESSION_ORCHESTRATOR.md) | Bridge Runtime↔Session (Sprint 6) |
| [`47_SPRINT11_CLINICAL_MVP_REPORT.md`](47_SPRINT11_CLINICAL_MVP_REPORT.md) | Relatório da Sprint |