# 47 — Sprint 11 Report — Clinical MVP

> **The Multisensory Experience — Phase 3.0 — Integration**
> Período: 2026-06-27 → 2026-07-01
> Status: **Concluído — aguardando aprovação humana**

---

## 1. Resumo executivo

A Sprint 11 entregou o **primeiro MVP clínico end-to-end** do AraFlow.
Pela primeira vez desde o início do projeto, todas as engines Core
(Timer, Breath, Runtime, ExecutionSession, SessionOrchestrator,
Persistence, AnimationEngine, AudioEngine) foram **conectadas em uma
única tela**, e essa tela é usável: um clínico pode abrir o app, escolher
um protocolo, executar a sessão, pausar, retomar, parar e registrar
feedback subjetivo — tudo local, sem backend, sem login, sem áudio real.

A Sprint cumpre **exatamente** o escopo aprovado:

- **Uma única tela clínica** com 3 fases internas (`select → session → feedback`).
- **3 protocolos** (Respiração Diafragmática, Box 4-4-4-4, Suspiro Fisiológico).
- **Nenhuma modificação** em qualquer módulo `@core/*` ou `@presentation/*`.
- **Nenhum Engine novo** — apenas composição sobre os módulos congelados.
- **InMemoryAudioAdapter** como única implementação de áudio (Sprint 12 traz `expo-av`).
- **AsyncStorage local** para feedback (sem backend).
- **32 testes novos passando** (3 suítes: unit + e2e + storage).
- **Documentação**: arquitetura + este relatório.

---

## 2. Entregas

### 2.1 Código (`mobile/src/features/session/Clinical/`)

| Caminho                                                            | Linhas | Tipo        |
|REDACTED|-------:|-------------|
| `index.ts`                                                         |     48 | barrel      |
| `ClinicalScreen.tsx`                                               |    482 | RN screen   |
| `ClinicalSession.ts`                                               |    327 | pure TS orchestrator |
| `ClinicalSessionHandle.ts`                                         |     47 | type        |
| `protocols/index.ts`                                               |     80 | barrel      |
| `protocols/diaphragmatic-breathing.json`                           |     29 | protocol JSON |
| `protocols/box-4-4-4-4.json`                                       |     31 | protocol JSON |
| `protocols/physiological-sigh.json`                                |     30 | protocol JSON |
| `feedback/FeedbackStorage.ts`                                      |    153 | AsyncStorage wrapper |
| `feedback/FEELING_AFTER_OPTIONS.ts`                                |     38 | enum        |

**Total src:** ~1265 linhas (TS + TSX + JSON).

### 2.2 Testes (`mobile/src/features/session/Clinical/__tests__/`)

| Arquivo                                | Casos | Cobre                                                                |
|REDACTED|------:|REDACTED|
| `ClinicalSession.test.ts`              |    18 | construção, start, pause, resume, stop, frame+update, dispose       |
| `ClinicalSession.e2e.test.ts`          |     3 | fluxo completo do brief (choice → start → pause → resume → stop → feedback) + persistência onPersist + smoke dos 3 protocolos |
| `FeedbackStorage.test.ts`              |    11 | save/list/clear + sanitização + `isFeedbackRecord` + 5 opções `FeelingAfter` |

**Total:** **32 casos** (todos passando).

### 2.3 Configuração

| Arquivo                | Mudança                                                                       |
|------------------------|REDACTED|
| `mobile/src/App.tsx`   | Renderiza `ClinicalScreen` (substitui `PlaceholderScreen`)                    |
| `mobile/package.json`  | Coverage threshold 90/95/95/95 para `./src/features/session/Clinical/`        |
| `mobile/jest.setup.ts` | Mock oficial de `@react-native-async-storage/async-storage`                  |

### 2.4 Documentação

| Arquivo                                                | Conteúdo                                          |
|REDACTED|REDACTED|
| `docs/AraFlow/47_CLINICAL_MVP.md`                      | Arquitetura completa + mapa de integração + limitações aceitas |
| `docs/AraFlow/47_SPRINT11_CLINICAL_MVP_REPORT.md`      | **Este relatório**                                |

---

## 3. Métricas

### 3.1 Cobertura do módulo `features/session/Clinical/`

| Métrica      | Threshold | Resultado    |
|--------------|----------:|--------------|
| Statements   |       95  | acima        |
| Branches     |       90  | acima        |
| Functions    |       95  | acima        |
| Lines        |       95  | acima        |

> Cobertura exata por arquivo disponível via
> `npx jest --coverage --testPathPattern="features/session/Clinical"`.

### 3.2 Testes (escopo da Sprint 11)

- **Total:** 32 testes ✅
- **Passando:** 32 ✅
- **Falhando:** 0
- **Suítes:** 3

### 3.3 Status do mobile completo

- **Total:** 1243 testes
- **Passando:** 1232
- **Falhando:** 11 (todas em testes de Core pré-existentes —
  `timer-engine` e `breath-engine`, **não regressões da Sprint 11**;
  reproduzido em stash com mudanças revertidas).

### 3.4 Build & gates

| Gate                                                                              | Resultado |
|REDACTED|-----------|
| `npx tsc --noEmit -p tsconfig.json` no módulo                                      | ✅ sem erros |
| `npx jest --coverage --testPathPattern="features/session/Clinical"`               | ✅ 32 / 32 |
| `grep -rE ': any\b' src/features/session/Clinical`                                 | ✅ 0 ocorrências |
| `grep -rE 'TODO\|FIXME\|XXX' src/features/session/Clinical`                       | ✅ 0 ocorrências |
| `grep -rE 'expo-av' src/features/session/Clinical`                                 | ✅ 0 ocorrências |
| `git diff --stat mobile/src/core/`                                                | ✅ vazio (Core intocado) |
| `grep -rE 'react-navigation\|@react-navigation' src/features/session/Clinical`     | ✅ 0 ocorrências (uma única tela) |

---

## 4. Decisões durante a Sprint

### 4.1 Sem `SessionOrchestrator(audio/animation)` — múltiplos subscribers no Runtime

A Sprint 10 confirmou que o Runtime deduplica o stream de eventos
(`AudioEventStream` + `AnimationEventStream` + `Runtime.subscribe` são
todos independentes e seguros). Portanto, `ClinicalSession` conecta:

- `AnimationEngine` direto no Runtime (como `FirstBreathSession` Sprint 9).
- `AudioEngine` direto no Runtime (Sprint 10).
- `SessionOrchestrator` direto no Runtime (Sprint 6).

Três subscribers no mesmo Runtime. Cada um recebe cada evento uma vez.
Sem acoplamento entre eles — composição pura.

### 4.2 `currentFrame()` pode ser `null` em rajada

`animation.currentFrame()` retorna `null` antes do primeiro tick de
Runtime e em transições instantâneas (`idle` → primeira phase). A UI
trata `frame === null` como "manter último frame" sem quebrar. Os testes
unit refletem isso: a asserção aceita `null` OU frame com `phase` em
string.

### 4.3 `SessionId` precisa ser ULID válido

`SessionOrchestrator` recebe um `SessionId` branded. `ClinicalSession`
constrói via `buildClinicalSessionUlid(now, randTail)` — gerador próprio
de 26 chars Crockford base32 — e embrulha com `SessionId(...)` do
`@araflow/shared-contracts/value-objects/ids`. Nenhuma dep da lib `ulid`
— o módulo é autocontido.

### 4.4 ULIDs dos 3 protocolos exigem 26 chars exatos

Encontramos no fim da Sprint: dois protocolos foram gerados com 27 chars
(`01ARZ3NDEKTSV4RRFFQ69G5FB0X`, `01ARZ3NDEKTSV4RRFFQ69G5SIGH`). O
constructor `ProtocolId` exige **exatamente 26 chars** (`ULID_PATTERN`
em `@araflow/shared-contracts`). Corrigidos para:

- box: `01ARZ3NDEKTSV4RRFFQ69G5FBX` (drop `0`)
- sigh: `01ARZ3NDEKTSV4RRFFQ69G5PHY` (drop `I`/`G`/`H`, lê como "physio")

Aprendizado: **a regex `^[0-9A-HJKMNP-TV-Z]{26}$` é estrita quanto ao
length, não só quanto ao charset**. Lição: ao gerar IDs, sempre gerar
26 chars com prefixo de 24 + sufixo de 2.

### 4.5 Cancelamento não persiste

`onPersist` é invocado **somente** em `runtime.completed`. `stop()` emite
`runtime.cancelled` (que faz teardown) mas **não** chama o callback.
A tela de feedback ainda aparece após `stop()` (UX consistente), mas o
`FeedbackRecord` carrega `completed: false`.

### 4.6 Sem roteador

Brief diz "uma única tela clínica". Implementamos 3 fases internas via
`useState<'select' | 'session' | 'feedback'>`, sem `@react-navigation/*`.
Mantém a árvore leve, evita dependência para uma tela só, e atende ao
brief literalmente.

---

## 5. Conformidade com o brief original

| Requisito do brief                                                    | Status |
|REDACTED|--------|
| Tela única, fluxo select→session→feedback                             | ✅      |
| 3 protocolos: Diafragmática, Box 4-4-4-4, Suspiro Fisiológico        | ✅      |
| Testes para o fluxo completo do brief                                 | ✅ (e2e: 3 casos) |
| Salvar feedback local (AsyncStorage)                                  | ✅      |
| Sem `expo-av` — só `InMemoryAudioAdapter`                              | ✅      |
| Sem login / backend / sync / analytics / wearables / IA               | ✅      |
| Sem múltiplas telas / múltiplos idiomas além de pt-BR / en-US         | ✅      |
| Sem modificar `@core/*`                                                | ✅      |
| Sem criar novos Engines                                                | ✅      |
| Sem adicionar protocolos além dos 3                                    | ✅      |
| Documentação: arquitetura + relatório                                 | ✅      |
| Cobertura ≥ 90/95/95/95 no módulo                                     | ✅      |
| Zero `any` / `TODO` / `FIXME`                                          | ✅      |

---

## 6. Riscos & mitigações

| Risco                                                              | Mitigação                                                |
|REDACTED|REDACTED|
| AsyncStorage mock desatualizado quebra testes                       | Mock oficial `@react-native-async-storage/async-storage/jest/async-storage-mock` (registrado em `jest.setup.ts`) |
| Múltiplos subscribers no Runtime duplicam eventos                  | `RuntimeEventStream` deduplica (provas em Sprints 5-7, 10) |
| Sessões que nunca terminam travam o app                            | `handle.dispose()` libera adapters e limpa orchestrator; UI desmonta o effect no unmount |
| Persistência in-memory some no reload                              | Aceito pelo MVP; documentado em `47_CLINICAL_MVP.md` §10. Próxima Sprint traz `AsyncStorageAdapter` real |
| ULIDs errados passam em unit mas falham em runtime                 | `ProtocolId` constructor (`shared-contracts`) valida com regex estrito; testes exercem o caminho real de `compile` |

---

## 7. Pendências e próximos passos

| Item                                                                              | Sprint       |
|REDACTED|--------------|
| `ExpoAvAudioAdapter` (iOS + Android) — substituir `InMemoryAudioAdapter`          | 12           |
| `AsyncStorageAdapter` real (substituir `MemoryStorageAdapter`)                    | 12           |
| Tela de configurações (volume, idioma)                                            | 13           |
| Multi-tenancy / login básico                                                      | 14           |
| Telemetria clínica agregada (sessões/dia, feedback médio)                        | 15           |
| Export / relatório PDF para o clínico                                            | 16           |
| Detox / Maestro E2E no CI                                                        | 13           |
| Auditoria de acessibilidade WCAG 2.1 AA                                           | 13           |

Nada disso está no escopo de Sprint 11. O MVP clínico está pronto
para validação interna com pacientes reais assim que o áudio real
chegar (Sprint 12).

---

## 8. Aprendizados

1. **ULIDs com sufixo mnemônico são úteis mas armadilha.** `SIGH` parece
   ótimo até lembrar que `I` é inválido em Crockford. **Regra:** prefixo
   de 24 chars + sufixo aleatório de 2. Não tente encaixar palavras.
2. **A separação Engine↔Adapter + Runtime-only sync é o que destrava
   Sprints de integração.** Sprint 11 não tocou Core nenhum — provando
   que a arquitetura está madura o suficiente para composição externa.
3. **3 subscribers no Runtime não é problema** porque `RuntimeEventStream`
   deduplica. Foi confirmado nos testes de integração da Sprint 10.

---

## 9. Comandos usados

```bash
cd mobile
npx tsc --noEmit -p tsconfig.json                                # ✅ sem erros
npx jest --coverage --testPathPattern="features/session/Clinical" # ✅ 32 / 32
npx prettier --check "src/features/session/Clinical/**/*.ts*" \
                       "__tests__/features/session/Clinical/**/*.ts" # ✅
```

---

## 10. Conclusão

Sprint 11 cumpre o brief original sem desvios. O MVP clínico está
completo, testado e documentado. **Nenhuma linha de Core foi tocada.**
A próxima sprint (12) substitui os dois adapters Mock pelos reais
(`expo-av` para áudio, `AsyncStorage` para persistência) e libera o MVP
para validação clínica interna com pacientes.

**PARA.** Conforme instruído pelo brief:

> "PARE. Não adicionar novas funcionalidades. O próximo passo será
> substituir o Mock AudioAdapter por um Adapter real (Expo Audio/Expo AV)
> e iniciar os testes clínicos internos."

Aguardando aprovação humana para abrir Sprint 12 (Real Audio Adapter
+ Real Persistence Adapter).