# 46 — Audio Engine

> **Sprint 10 — The Multisensory Experience**
> `@core/audio-engine@1.0.0`

O Audio Engine é o componente Core que sincroniza **reprodução de áudio** com o ciclo respiratório do AraFlow. Ele é puramente declarativo: **não toca áudio, não mantém timers, não conhece UI** — apenas reage aos eventos do Runtime e delega a execução para um `AudioAdapter`.

---

## 1. Princípios

| Princípio | Como o Engine o cumpre |
|---|---|
| **Determinismo** | Toda reprodução é dirigida por eventos do Runtime; o Engine não tem timers próprios nem `Date.now()`. O único relógio confiável é o `monotonicMs` de cada evento. |
| **Pureza de domínio** | Camada `domain/` é puramente tipos + funções puras (factories congelados, helpers sem I/O). Camada `util/` é puramente matemática e tabelas. |
| **Swappability** | Toda saída passa por um único seam: a interface `AudioAdapter`. Trocar de backend = trocar a implementação injetada em `AudioEngineDeps`. |
| **Reação, não controle** | O Engine **nunca** decide iniciar áudio por conta própria. Ele reage a eventos de `timer`/`breath` emitidos pelo Runtime. |
| **Sem UI/RN** | Não há imports de `react`, `@mui/*`, `react-native`, `expo-*`. Toda API opera com tipos primitivos. |
| **Sem áudio real (Sprint 10)** | `InMemoryAudioAdapter` registra chamadas — IDs são strings. Backends reais chegam em Sprints futuros. |

---

## 2. As 4 camadas de áudio

Toda reprodução é classificada em uma de quatro camadas ortogonais:

| Camada    | Conteúdo                              | Exemplo de uso                            |
|-----------|REDACTED|REDACTED|
| `guidance`| Frases faladas curtas                 | "Inspire" / "Segure" / "Expire"           |
| `cue`     | Marcadores percussivos                | Sino de entrada, click de fase            |
| `ambient` | Texturas de fundo                     | Chuva suave, branco, oceano               |
| `music`   | Faixas musicais em primeiro plano      | Pads, drones, harmonias longas            |

Cada `AudioClip` pertence a exatamente uma camada. Um `AudioTrack` é uma coleção de `clips` com defaults por camada (`layerDefaults`). Essa modelagem espelha diretamente os conceitos do `AnimationEngine` (slides 41 e 44) — o Engine **não reproduz nada**; só decide **qual clip tocar em qual momento**.

---

## 3. Arquitetura

```
┌──────────────────────────────────────────────────────────────┐
│                        AudioEngine                           │
│                                                              │
│   ┌───────────────┐                                          │
│   │ 7-state FSM   │ uninitialized → loaded → playing →       │
│   │               │ paused → stopped → disposed              │
│   └───────────────┘                                          │
│                                                              │
│   ┌─────────────────┐    ┌─────────────────────────┐          │
│   │ Runtime event   │───▶│  AudioAdapter (seam)    │          │
│   │ subscription    │    │  InMemory / future exp  │          │
│   │ (1 listener)    │    └─────────────────────────┘          │
│   └─────────────────┘                                        │
│                                                              │
│   ┌─────────────────┐    ┌─────────────────────────┐          │
│   │ AudioEventStream│───▶│ 11 tagged-union events  │          │
│   │ (snapshot +     │    │ start/pause/resume/     │          │
│   │  try/catch)     │    │ stop/track/cue/         │          │
│   └─────────────────┘    │ guidance/ambient/music/ │          │
│                          │ volume/mute             │          │
│                          └─────────────────────────┘          │
└──────────────────────────────────────────────────────────────┘
              ▲                       │
              │                       ▼
   ┌──────────────────────┐  ┌─────────────────────────────┐
   │ RuntimeEngine        │  │ AudioEventStream (consumers)│
   │ (timer/breath events)│  │ UI / Session / Analytics    │
   └──────────────────────┘  └─────────────────────────────┘
```

### 3.1 Camadas internas

```
mobile/src/core/audio-engine/
├── index.ts                          public barrel + version
├── domain/
│   ├── AudioLayer.ts                 4 layers + guards
│   ├── AudioLanguage.ts              pt-BR | en-US
│   ├── AudioClip.ts                  clip value type
│   ├── AudioTrack.ts                 track = clips + layerDefaults
│   ├── AudioEngineState.ts           7-state FSM
│   ├── AudioEvent.ts                 11-variant tagged union
│   ├── AudioVolume.ts                master + per-layer [0..1]
│   └── AudioAdapter.ts               the seam
├── application/
│   ├── AudioEngine.ts                main API + Runtime reaction
│   ├── AudioEngineDeps.ts            constructor options
│   └── AudioEventStream.ts           Set + snapshot + onListenerError
├── util/
│   ├── phase-to-cue.ts               phase+language → cue id
│   ├── volume-math.ts                clamp01, effectiveVolume, dB
│   └── default-cue-table.ts          per-language cue tables
└── infra/
    └── InMemoryAudioAdapter.ts       mock — Sprint 10 default
```

---

## 4. Sincronização Runtime → Audio

O Engine assina uma única vez `runtime.subscribe(listener)`. Dentro do listener, discrimina por `event.source` → `event.payload.type`:

| Evento do Runtime                | Reação do AudioEngine                                              |
|----------------------------------|REDACTED|
| `timer.started`                  | `play()` → estado `playing`                                        |
| `timer.paused`                   | `pause()` → estado `paused` (sem chamada ao adapter)               |
| `timer.resumed`                  | `resume()` → estado `playing` (sem chamada ao adapter)             |
| `timer.stopped`                  | `stop()` → estado `stopped` + `adapter.stop` em todas as camadas   |
| `breath.phase-changed to X`      | `adapter.play('cue', phaseToCueId(X, language))` + guidance clip   |
| `breath.breath-started`          | `adapter.play('ambient', ...)` + `adapter.play('music', ...)`      |
| `breath.completed`               | `adapter.stop('ambient')` + `adapter.stop('music')` → `stopped`    |
| `breath.cancelled`               | idem `completed`                                                   |
| `breath.resumed-from-interrupt`  | `adapter.resume()` para guidance/cue/ambient/music                 |
| `idle` (phase)                   | **Sem emissão de cue** (silêncio intencional)                      |

**Regra de ouro:** o Engine nunca inventa áudio fora desses eventos.

---

## 5. Contrato `AudioAdapter` (the seam)

```ts
export interface AudioAdapter {
  readonly id: string;
  load(clip: AudioClip): Promise<Result<void, AudioAdapterError>>;
  play(layer: AudioLayer, clipId: string): Promise<Result<void, AudioAdapterError>>;
  pause(layer: AudioLayer): Promise<Result<void, AudioAdapterError>>;
  resume(layer: AudioLayer): Promise<Result<void, AudioAdapterError>>;
  stop(layer: AudioLayer): Promise<Result<void, AudioAdapterError>>;
  setLayerVolume(layer: AudioLayer, value: number): Promise<Result<void, AudioAdapterError>>;
  setMasterVolume(value: number): Promise<Result<void, AudioAdapterError>>;
  dispose(): Promise<Result<void, AudioAdapterError>>;
}
```

Toda comunicação de saída do Engine passa por aqui. **Sprint 10 fornece `InMemoryAudioAdapter`** — um mock que registra todas as chamadas em arrays (`playLog`, `pauseLog`, etc.) e devolve `Ok`. Backends reais (`expo-av`, `react-native-track-player`, WebAudio) viram adapters adicionais em Sprints futuros **sem alterar** este contrato.

### 5.1 `InMemoryAudioAdapter`

- `id = 'in-memory-v1'`
- Latência opcional via `simulatedLatencyMs` (default 0).
- `dispose()` é idempotente; `failAfterDispose: true` faz cada método devolver `audio_adapter_disposed` após o dispose.
- Sem native deps. Sem sons reais. Sem `expo-av`.

---

## 6. Máquina de estados

```
                              ┌───────────────────┐
                              │  uninitialized    │
                              └────────┬──────────┘
                                       │ loadTrack()
                                       ▼
                              ┌───────────────────┐
              ┌───────────────│     loaded        │───────────────┐
              │               └────────┬──────────┘               │
              │                        │ play()                   │ loadTrack()
              │ stop()                 ▼                          │ (re-load)
              │               ┌───────────────────┐              │
              │               │     playing       │              │
              │               └───┬───────────┬───┘              │
              │              pause()         │ stop()            │
              │                   ▼           ▼                   │
              │            ┌─────────┐  ┌──────────┐              │
              │            │ paused  │  │ stopped  │◀─────────────┘
              │            └────┬────┘  └────┬─────┘
              │       resume()   │  stop()   │
              │                 ▼            │
              │            ┌────────────┐   │
              └───────────▶│  playing   │◀──┘
                           └────────────┘
                                 │
                              dispose()
                                 ▼
                          ┌───────────┐
                          │ disposed  │ (terminal)
                          └───────────┘
```

Regras:

- `uninitialized → loaded | errored | disposed`
- `loaded → loaded (re-track) | playing | stopped | disposed`
- `playing → paused | stopped | errored | disposed`
- `paused → playing | stopped | disposed`  (resume só de `paused`)
- `stopped → loaded | playing | disposed`
- `errored → loaded | disposed`
- `disposed → ∅` (terminal)

---

## 7. Modelo de volumes

```
master ─┐
         ├── effective_volume = clamp01(master) × clamp01(layer) ── audio
layer ───┘   (multiplicado por 0 quando muted)
```

O Engine opera em **linear** (`[0, 1]`). A conversão para dB é responsabilidade do adapter — utilitários `linearToDecibels` / `decibelsToLinear` ficam disponíveis para backends que precisem.

### Eventos emitidos

`volume-changed { layer: AudioLayer | 'master', value: 0..1 }` e `mute-changed { muted: boolean }`.

---

## 8. Mapa de fases → cue

`phaseToCueEntry(phase, language)` é uma função pura. Tabela padrão (`default-cue-table.ts`):

| `AnimationPhase` | PT-BR cueId         | PT-BR text    | EN-US cueId         | EN-US text      |
|------------------|---------------------|---------------|---------------------|-----------------|
| `preparing`      | `cue.bell.soft`     | "Prepare-se"  | `cue.bell.soft`     | "Get ready"     |
| `inhale`         | `cue.bell.inhale`   | "Inspire"     | `cue.bell.inhale`   | "Breathe in"    |
| `hold`           | `cue.bell.hold`     | "Segure"      | `cue.bell.hold`     | "Hold"          |
| `exhale`         | `cue.bell.exhale`   | "Expire"      | `cue.bell.exhale`   | "Breathe out"   |
| `completed`      | `cue.bell.end`      | "Concluído"   | `cue.bell.end`      | "Complete"      |
| `idle`           | *(silenciosa)*      | —             | *(silenciosa)*      | —               |

A tabela é **trackable** (`Object.freeze`). Substituir a tabela inteira é uma operação de camada superior, não responsabilidade deste Engine.

---

## 9. Eventos (11 variantes tagged-union)

```ts
type AudioEvent =
  | { type: 'audio-started';   trackId; layer; monotonicMs }
  | { type: 'audio-paused';    atElapsedMs; monotonicMs }
  | { type: 'audio-resumed';   pausedForMs; monotonicMs }
  | { type: 'audio-stopped';   reason: 'completed' | 'cancelled' | 'errored'; monotonicMs }
  | { type: 'track-loaded';    trackId; layer; clipCount; monotonicMs }
  | { type: 'cue-played';      cueId; layer; monotonicMs }
  | { type: 'guidance-played'; text; language; monotonicMs }
  | { type: 'ambient-started'; trackId; monotonicMs }
  | { type: 'music-started';   trackId; monotonicMs }
  | { type: 'volume-changed';  layer: AudioLayer | 'master'; value; monotonicMs }
  | { type: 'mute-changed';    muted: boolean; monotonicMs };
```

Todos os eventos carregam `monotonicMs` (Number, ms desde um epoch monotônico). O Engine é estritamente sem relógios próprios; o campo é repassado dos eventos do Runtime.

Listeners recebem os eventos via `engine.subscribe(listener)`. Erros em listeners são isolados via `AudioEventStream` (Set + snapshot + try/catch + `onListenerError` sink) — falha de um listener nunca quebra os outros.

---

## 10. Latência & determinismo

| Métrica                          | Target                    | Como é garantido |
|----------------------------------|---------------------------|------------------|
| Latência cue (evento → adapter)  | **< 20 ms**               | Sem timers: o handler é síncrono na callback do Runtime. Em runtime JS síncrono, latência ≈ 0 ms (sem overhead de I/O até `adapter.play()`, que é microtask). |
| Drift                            | **0 ms**                  | Engine nunca calcula tempo por conta própria. `monotonicMs` vem do Runtime. |
| Memory leaks                     | **0**                     | `_unsubscribeRuntime` chamado em `dispose()`. `AudioEventStream` é `clear()`-ado. Adapter recebe `dispose()`. |
| Re-emit                          | **0**                     | Engine assina `runtime.subscribe` **uma vez**; Runtime já deduplica via stream único. |

---

## 11. Limitações declaradas (Sprint 10)

| Limitação                          | Razão                                              | Resolução futura                |
|REDACTED|REDACTED|---------------------------------|
| **Sem áudio reproduzido**          | Sprint 10 entrega só a arquitetura + contrato      | Backend `expo-av` em Sprint 11+ |
| **`InMemoryAudioAdapter` é único adapter** | O brief pediu 1 mock em Sprint 10                | Adapter real em Sprint 11+      |
| **Sem UI de configurações**        | Brief proibiu UI                                   | Tela de settings (Sprint 12+)   |
| **Sem persistência de preferências**| Brief proibiu persistência                         | Sprint 13 (preferences module)  |
| **Sem fallback offline**           | O Engine é puro; sem rede envolvida                | Adapter decide                 |

---

## 12. API pública (consumidores)

```ts
import { createAudioEngine } from '@core/audio-engine';

const engine = createAudioEngine({
  adapter: createInMemoryAudioAdapter(),         // ou um adapter real
  runtime: createRuntimeEngine({...}),           // opcional mas recomendado
  onListenerError: (err, listener) => { ... },   // opcional
  engineId: 'custom',                            // opcional
});

const u = engine.subscribe((event) => { ... });
engine.loadTrack(track);
engine.play();
engine.pause();
engine.resume();
engine.stop();
engine.dispose();

engine.setVolume('cue', 0.7);
engine.setMasterVolumeValue(0.8);
engine.mute();
engine.unmute();
engine.setLanguage('en-US');
engine.getState();         // 'uninitialized' | 'loaded' | 'playing' | ...
engine.getActiveTrack();   // AudioTrack | null
```

---

## 13. Conformidade

| Documento                                | Status |
|REDACTED|--------|
| `32_FINAL_PRODUCT_DECISIONS.md`          | ✅      |
| `33_ENGINEERING_BLUEPRINT.md`            | ✅      |
| `39_*.md` (padrão DDD + camadas)         | ✅      |
| ADR-028 (Animation Renderer pattern)     | Reaproveitado — Engine↔Adapter é a mesma forma |
| ADR-029 (este sprint)                    | Definido em `docs/adr/araflow/029-audio-engine.md` |

---

## 14. Próximos passos (Sprint 11+)

1. **`ExpoAvAudioAdapter`** — adapter real usando `expo-av` ou `react-native-track-player`.
2. **`WebAudioAdapter`** — adapter para Web (plataforma clínica desktop).
3. **Persistência de preferências** — volumes e idioma por usuário.
4. **Tela de configurações** — UI para ajustar volumes por camada.
5. **Mixagem adaptativa** — duck automático entre `ambient` e `guidance` quando uma frase vocal começa.
6. **Detecção de fone / speaker** — mudança de mixagem conforme `AVAudioSession` category.
7. **Telemetria** — métricas de quantas vezes cada cue foi tocado por usuário/protocolo.

**Nada disso está no escopo de Sprint 10.**
