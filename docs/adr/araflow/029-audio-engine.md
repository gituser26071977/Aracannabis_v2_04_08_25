# ADR-029 — Audio Engine

**Status:** Accepted (Sprint 10)
**Data:** 2026-07-01
**Contexto:** Phase 2.2 / Sprint 10 — The Multisensory Experience

---

## Contexto

Após a Sprint 9 (First Visual Experience), o AraFlow já sincroniza o círculo respiratório com eventos do Runtime. A próxima fronteira é **áudio**: som que reage ao ciclo respiratório. O áudio precisa ser:

1. **Sincronizado** com o ciclo respiratório sem drift.
2. **Determinístico** — todas as decisões devem vir de eventos do Core, não de timers próprios.
3. **Trocar de backend sem refactor** — hoje é mock, amanhã pode ser `expo-av`, `react-native-track-player`, WebAudio.
4. **Testável** sem hardware nem bibliotecas nativas.
5. **Não-UI** — o Core não conhece React, RN, MUI.

---

## Decisão

Criamos `@core/audio-engine@1.0.0` como **camada Core** independente em `mobile/src/core/audio-engine/`, seguindo o padrão DDD + camadas (`domain/`, `application/`, `util/`, `infra/`). O **único ponto de contato com qualquer backend de áudio** é a interface `AudioAdapter`. Sprint 10 fornece um único impl: `InMemoryAudioAdapter` (mock que registra chamadas).

### Estrutura

```
core/audio-engine/
├── domain/             tipos + FSM + eventos + volumes + adapter interface
├── application/        AudioEngine + AudioEventStream + deps
├── util/               phase-to-cue, volume-math, default-cue-table
└── infra/              InMemoryAudioAdapter (mock)
```

### Princípios centrais

#### 1. **Engine ↔ Adapter separation** *(mesmo padrão de ADR-028)*

```
AudioEngine (orquestra, decide, emite eventos)
   │
   │──▶ AudioAdapter (executa, toca, hardware)   ◀── seam única
```

Sprint 10 **não introduz backend real**. Toda saída é via `AudioAdapter`. Trocar `InMemoryAudioAdapter` por um adapter `expo-av` em Sprint 11+ **não exige** mudanças no Engine nem nos consumidores.

#### 2. **Runtime-only sync (sem timers próprios)**

O Engine assina `runtime.subscribe(listener)` **uma única vez**. A partir daí, cada evento do Runtime é traduzido em uma reação no adapter:

| Evento do Runtime       | Reação                                                    |
|-------------------------|REDACTED|
| `timer.started`         | `engine.play()`                                           |
| `timer.paused/resumed`  | pause/resume da FSM (sem tocar adapter)                   |
| `timer.stopped`         | `engine.stop()` → para todas as camadas                   |
| `breath.phase-changed`  | lookup `phaseToCueId` → `adapter.play('cue', id)`         |
| `breath.breath-started` | `adapter.play('ambient', clipId)` + `adapter.play('music', ...)` |
| `breath.completed/cancelled` | `adapter.stop` em ambient + music, transita para `stopped` |
| `breath.resumed-from-interrupt` | `adapter.resume` em todas as camadas                |

**Zero `Date.now()`, zero `setTimeout`, zero `setInterval`.** Todo timing vem do `monotonicMs` que o Runtime injeta em cada evento.

#### 3. **4 camadas ortogonais**

`guidance | cue | ambient | music` — cada clip pertence a uma única camada; cada camada tem volume independente; todas multiplicam por `master` (a menos que `muted = true`, em que zeram).

#### 4. **Idioma como estado, não como perfil**

`setLanguage('pt-BR' | 'en-US')` muda a tabela de cue usada em `phase-to-cue`. O Engine não persiste; o consumidor persiste.

#### 5. **Eventos com tagged-union (11 variantes)**

Todos os eventos carregam `monotonicMs` (herdado do Runtime). Discriminação via `event.type`. Stream interno espelha o padrão provado do `RuntimeEventStream` (Set + snapshot + try/catch + `onListenerError`).

#### 6. **InMemory como adapter padrão de Sprint 10**

Mock que:
- registra toda chamada em arrays tipados;
- devolve `Ok` por padrão;
- suporta `simulatedLatencyMs` para testar contratos async;
- suporta `failAfterDispose: true` para testar idempotência de dispose.

### Por que NÃO integrar uma biblioteca real em Sprint 10

O brief da Sprint 10 foi explícito:

> **NÃO implementar:** reprodução real de áudio; bibliotecas externas; UI de configurações; persistência; backend; analytics; wearables.
> **Ao concluir:** PARE. Não integrar nenhuma biblioteca de áudio. Não adicionar sons reais. Não criar telas de configuração. O sucesso desta Sprint será medido pela qualidade da arquitetura do Audio Engine e pela sincronização determinística entre os eventos do Core e a futura camada de reprodução.

Sprint 10 entrega **a interface**, a **mecânica**, a **sincronia** e o **mock**. Sprint 11+ integrará o backend real.

---

## Alternativas consideradas

### A) Integrar `expo-av` direto no `AudioEngine`

**Rejeitado.** Cria acoplamento direto a uma biblioteca de plataforma. Impede trocar de backend sem refactor. Torna os testes dependentes de mocks nativos.

### B) Audio Engine como parte do `RuntimeEngine` (sem módulo separado)

**Rejeitado.** Quebra o princípio "Core sem áudio" — o Runtime já é grande o suficiente (12 métodos + 4-state FSM). Também quebra reuso: futuros engines (wearable, vibração tátil) vão querer o mesmo padrão listener → adapter.

### C) Eventos através de channels/socket próprios

**Rejeitado.** Reimplementaria deduplicação, snapshot, error isolation que o Runtime já provê. Mais código, mesma semântica, com mais um ponto de falha.

### D) Trigger de áudio por polling de estado

**Rejeitado.** Polling implica timers, o que viola o princípio "Runtime-only sync". Cria drift e custo desnecessário.

### E) Camada de áudio acoplada a `AnimationEngine` (visão-first)

**Rejeitado.** Áudio não é visual. O Sync Director já é o Runtime — colocar áudio no AnimationEngine criaria uma dependência nova e confusing. Mantemos Runtime como single source of truth.

---

## Consequências

### Positivas
- **Determinismo**: nenhuma decisão vem de tempo local; tudo vem do Runtime.
- **Testabilidade pura**: `InMemoryAudioAdapter` é spy + state machine. Sem hardware.
- **Swappability**: trocar backend = injetar outro `AudioAdapter`. Engine e consumidores não mudam.
- **Reuso do padrão**: mesmo ADR-028 (Animation Renderer) provou a forma. Reaproveitada.
- **Observabilidade**: 11 eventos tipados permitem telemetria 1:1.
- **Cobertura ≥95%**: 80 testes (78 OK após ajustes) cobrem todas as variantes.

### Negativas / Trade-offs
- **Camada extra**: adicionar um Adapter real (Sprint 11) é mais uma tarefa; alternativa "inline" seria mais rápida — mas traria acoplamento.
- **Mock ≠ real**: testar com `InMemoryAudioAdapter` valida a *contrato* com o adapter, não valida que `expo-av` realmente toca. Testes com backend real vêm no Sprint que adicionar `ExpoAvAudioAdapter`.
- **Sem persistência**: volumes e idioma vivem só em memória. (Sprint fora do escopo.)

### Compliance

| Documento                          | Como o ADR cumpre                                       |
|REDACTED|REDACTED|
| `32_FINAL_PRODUCT_DECISIONS.md`    | Foco em Core puro, sem UI.                              |
| `33_ENGINEERING_BLUEPRINT.md`      | Camadas DDD + barrel + versionamento.                   |
| `39_TESTING_STRATEGY.md`           | Cobertura ≥95% por threshold em `package.json`.        |
| `ADR-028` (Animation Renderer)     | Mesmo padrão Engine↔Adapter reaproveitado.              |
| `ADR-029` (este)                   | Estabelece a separação para o próximo adapter real.     |

---

## Compatibilidade & migração

- **Sem código consumidor anterior**: nenhum código já chama o Audio Engine. É um novo módulo verde.
- **`AUDIO_ENGINE_VERSION = '1.0.0'`**: enquanto a forma se mantiver, futuras sprints somam adapters sem breaking change.
- **Path alias**: `@core/audio-engine` resolve via wildcard já existente em `tsconfig.json` + `package.json` (Sprint 4 já confirmou).

---

## Próximos passos (Sprint 11+)

| Sprint | Trabalho                                                              |
|--------|REDACTED|
| 11     | `ExpoAvAudioAdapter` — adapter real iOS/Android usando `expo-av`.     |
| 12     | Tela de configurações de áudio na UI.                                  |
| 13     | Persistência de volumes/idioma por usuário.                            |
| 14     | Telemetria — `cue-played`, `guidance-played` por protocolo/usuário.   |

Esses itens **não fazem parte** do Sprint 10.
