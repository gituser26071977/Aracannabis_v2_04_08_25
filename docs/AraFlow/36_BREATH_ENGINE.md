# AraFlow — Breath Engine

> **Versão:** 1.0.0
> **Data:** 2026-06-25
> **Sprint:** 2 — Foundation Implementation
> **Status:** Implementado, testado, congelado.

---

## Sumário

1. Visão geral
2. Onde mora
3. Arquitetura em camadas
4. Modelo matemático do ciclo
5. Máquina de estados
6. Eventos
7. Curvas
8. Profundidade (depth)
9. Integração com Timer Engine
10. Pontos de extensão
11. Limitações
12. Reuso em outras plataformas
13. Performance
14. Referências

---

## 1. Visão geral

O **Breath Engine** é o motor mecânico da respiração. Ele coordena fases (inhale, hold, exhale, hold), conta ciclos, computa profundidade ao longo do tempo, e emite eventos.

**O que ele conhece:**

- Quatro fases mecânicas: `inhaling`, `holdAfterInhale`, `exhaling`, `holdAfterExhale`.
- Conceitos: ciclo, ratio, cadência, fase, estado.
- Curvas de interpolação: linear, easeIn, easeOut, easeInOut, sine, cosine, bezier.

**O que ele NÃO conhece:**

- Box Breathing, Coherent Breathing, 4-7-8 (responsabilidade do Protocol Engine).
- Ansiedade, insônia, foco (responsabilidade do Protocol Engine).
- UI, animação, áudio (responsabilidade da Presentation Layer).
- Persistência (responsabilidade do Session Engine).

**Princípios:**

- Zero dependência de UI, React, React Native, plataforma.
- 100% determinístico dado o mesmo Timer Engine e config.
- Re-entrante: chamadas de cancel/subscribe durante dispatch são seguras.
- Erros em listeners não interrompem dispatch.
- O Timer Engine é a ÚNICA fonte oficial de tempo.

---

## 2. Onde mora

```
mobile/src/core/breath-engine/
├── domain/                    # Tipos puros + curvas
│   ├── BreathPhase.ts
│   ├── BreathState.ts
│   ├── BreathCycleConfig.ts
│   ├── BreathCadence.ts
│   ├── BreathRatio.ts
│   ├── BreathSnapshot.ts
│   ├── BreathEvent.ts
│   ├── Listener.ts
│   ├── Curve.ts
│   ├── curves/
│   │   ├── linear.ts
│   │   ├── easeIn.ts
│   │   ├── easeOut.ts
│   │   ├── easeInOut.ts
│   │   ├── sine.ts
│   │   ├── cosine.ts
│   │   ├── bezier.ts
│   │   └── index.ts
│   └── index.ts
├── application/               # Orquestração
│   ├── EventDispatcher.ts
│   ├── PhaseCalculator.ts
│   ├── DepthCalculator.ts
│   ├── BreathEngine.ts
│   └── index.ts
└── index.ts                   # Public API
```

E os testes:

```
mobile/__tests__/core/breath-engine/
├── fakes.ts
├── curves.test.ts
├── PhaseCalculator.test.ts
├── DepthCalculator.test.ts
├── BreathEngine.test.ts
├── BreathEngine.integration.test.ts
├── BreathEngine.bench.test.ts
└── BreathEngine.bench.run.ts
```

---

## 3. Arquitetura em camadas

```
┌─────────────────────────────────────────┐
│             APPLICATION                 │
│                                          │
│   BreathEngine  ───  PhaseCalculator    │
│        │              │                  │
│        │              ▼                  │
│        │         DepthCalculator         │
│        ▼                                  │
│   BreathEventDispatcher (re-entrância)   │
│                                          │
└──────────────┬──────────────────────────┘
               │ depende apenas de DOMAIN
               ▼
┌─────────────────────────────────────────┐
│               DOMAIN                     │
│                                          │
│   BreathPhase  BreathState               │
│   BreathCycleConfig  BreathCadence       │
│   BreathRatio  BreathSnapshot            │
│   BreathEvent  BreathListener            │
│   CurveFn  Curves (7 built-in)           │
│                                          │
│   (zero deps, zero I/O)                  │
│                                          │
└──────────────▲──────────────────────────┘
               │
               │ depende de @core/timer-engine
               │ (não de infrastructure)
               ▼
┌─────────────────────────────────────────┐
│         TIMER ENGINE (externo)          │
│                                          │
│   TimerEngine.subscribe(...)            │
│   TimerEngine.getTotalElapsedMs()        │
│                                          │
└─────────────────────────────────────────┘
```

**Regras de dependência:**

- `domain` não importa nada (exceto `@shared/errors` para AppError throws em `resolveCurve`).
- `application` importa apenas `domain` + `@core/timer-engine` (types).
- Não há camada de `infrastructure` — Breath Engine é 100% reutilizável via injeção de Timer Engine.

---

## 4. Modelo matemático do ciclo

### 4.1 Estrutura de um ciclo

```
        ┌─────────┐   ┌──────────────┐   ┌─────────┐   ┌──────────────┐
        │ inhale  │──►│holdAfterInh. │──►│ exhale  │──►│holdAfterExh. │──┐
        └─────────┘   └──────────────┘   └─────────┘   └──────────────┘  │
        4000ms       4000ms              4000ms        4000ms            │
        (config)     (config)            (config)      (config)          │
                                                                          │
        ◄─────────────────────────────────────────────────────────────────┘
                                  repete `cycles` vezes
```

### 4.2 Fase opcional de preparação

Antes do primeiro inhale, uma fase opcional `preparing` pode ser configurada com `prepMs`. Esta fase NÃO produz depth nem cycle activity — serve apenas como contagem regressiva antes da sessão começar.

```
┌──────────┐   ┌─────────┐   ┌──────────────┐   ...
│ preparing│──►│ inhale  │──►│holdAfterInh. │──►
└──────────┘   └─────────┘   └──────────────┘
0..prepMs     inhaleMs       holdAfterInhaleMs
```

### 4.3 Duração total

```
cycleMs       = inhaleMs + holdAfterInhaleMs + exhaleMs + holdAfterExhaleMs
sessionMs     = cycleMs × cycles
totalMs       = prepMs + sessionMs (se prepMs definido; senão = sessionMs)
```

### 4.4 Mapeamento tempo → fase

Dado `totalElapsedMs`, `PhaseCalculator.computePhaseInfo(config, totalElapsedMs)` retorna um `PhaseInfo`:

| Faixa de tempo | Activity | Phase | Cycle Index |
|----------------|----------|-------|-------------|
| `[0, prepMs)` | preparing | null | 0 |
| `[prepMs, prepMs + sessionMs)` | active | uma das 4 fases | `[0, cycles)` |
| `[totalMs, ∞)` | completed | null | `cycles` |

Dentro de uma fase ativa:

```
cycleIndex        = floor((totalElapsedMs - prepMs) / cycleMs)
cycleElapsedMs    = (totalElapsedMs - prepMs) - cycleIndex × cycleMs
```

E a fase é determinada por qual faixa `cycleElapsedMs` cai:

```
[0, inhaleMs)                          → inhaling
[inhaleMs, inhaleMs + holdAfterInh)    → holdAfterInhale
[inhaleMs + holdAfterInh, ...)         → exhaling
[inhaleMs + holdAfterInh + exhaleMs, ∞)→ holdAfterExhale
```

---

## 5. Máquina de estados

```
                      ┌─────────┐
                      │  idle   │ ◄────────────────────────┐
                      └────┬────┘                          │
                       start│                               │ reset
                           ▼                                │
              ┌──────────────────────┐                      │
              │     preparing        │                      │
              └──────────┬───────────┘                      │
                         │ prepMs elapses                   │
                         ▼                                  │
              ┌──────────────────────┐                      │
              │     inhaling         │──┐                   │
              └──────────┬───────────┘  │                   │
                         │              │                   │
                         ▼              │                   │
              ┌──────────────────────┐  │ cycle wrap       │
              │   holdAfterInhale    │  │                   │
              └──────────┬───────────┘  │                   │
                         │              │                   │
                         ▼              │                   │
              ┌──────────────────────┐  │                   │
              │     exhaling         │  │                   │
              └──────────┬───────────┘  │                   │
                         │              │                   │
                         ▼              │                   │
              ┌──────────────────────┐  │                   │
              │   holdAfterExhale    │──┘                   │
              └──────────┬───────────┘                      │
                         │ (last cycle)                      │
                         ▼                                  │
              ┌──────────────────────┐                      │
              │     completed        │──────────reset──────► │
              └──────────────────────┘                      │
                                                           │
   ┌────────────┐  ┌────────────┐                           │
   │ cancelled  │  │interrupted │ (entra/sai via bg/fg)    │
   └─────┬──────┘  └─────┬──────┘                           │
         │               │                                  │
         └───────reset───┴──────────────────────────────────┘
```

**Invariantes:**

- `state === 'completed'`  ⇔  `cyclesCompleted === cycles`
- `state === 'preparing'`  ⇔  `currentPhase === null && sessionElapsedMs < prepMs`
- `state` em {`inhaling`, `holdAfterInhale`, `exhaling`, `holdAfterExhale`}  ⇔  `currentPhase === state`
- `interrupted` é um estado de "espera" — não consome tempo até `notifyForeground`.

**Transições inválidas:**

- `start()` de estado ativo (`inhaling`, `holdAfterInhale`, `exhaling`, `holdAfterExhale`, `preparing`, `interrupted`) → AppError.
- `start()` exige Timer Engine em estado `running`; caso contrário → AppError.

---

## 6. Eventos

9 tipos (8 conforme spec + 1 extensão `resumed-from-interrupt`):

| Evento | Quando | Payload |
|--------|--------|---------|
| `breath-started` | Sessão inicia | totalCycles, totalDurationMs |
| `cycle-started` | Cada ciclo começa (incluindo 0) | cycleIndex, totalCycles |
| `cycle-completed` | Ciclo termina após holdAfterExhale | cycleIndex, totalCycles |
| `breath-completed` | Inalação+exalação termina (antes de hold) | cycleIndex, totalCycles |
| `phase-changed` | Transição de fase | previousPhase, currentPhase, cycleIndex, phaseProgress |
| `completed` | Sessão inteira terminou (uma vez) | totalCycles, totalElapsedMs |
| `interrupted` | App foi para background | stateBefore, elapsedAtInterruptionMs |
| `resumed-from-interrupt` | App voltou do background (extensão) | stateBefore, interruptedForMs, resumedPhase, resumedCycleIndex |
| `cancelled` | Usuário cancelou | stateBefore, elapsedAtCancelMs, cyclesCompleted |

**Distinção entre `breath-completed`, `cycle-completed` e `completed`:**

Em uma configuração 4-4-4-4 (Box Breathing) com 5 ciclos:

```
t=0:       breath-started, cycle-started(0), phase-changed(null→inhaling)
t=4:       phase-changed(inhaling→holdAfterInhale)
t=8:       phase-changed(holdAfterInhale→exhaling), breath-completed(0)  ← fim da respiração
t=12:      phase-changed(exhaling→holdAfterExhale)
t=16:      cycle-completed(0), cycle-started(1), phase-changed(holdAfterExhale→inhaling)
t=20:      phase-changed(inhaling→holdAfterInhale)
t=24:      phase-changed(holdAfterInhale→exhaling), breath-completed(1)
t=28:      phase-changed(exhaling→holdAfterExhale)
t=32:      cycle-completed(1), cycle-started(2), phase-changed(...)
...
t=80:      cycle-completed(4), completed                                   ← fim da sessão
```

**Garantias:**

- Eventos são DISPATCHED SÍNCRONOS.
- Listeners que modificam estado (ex.: cancel de dentro de phase-changed) são seguros.
- Erros em listener são capturados e engolidos.

---

## 7. Curvas

Curvas mapeiam progresso `p ∈ [0, 1]` em valor `y ∈ [0, 1]`. Implementadas como funções puras.

| Curva | Nome | Quando usar |
|-------|------|-------------|
| `linear` | Linear | Sem easing; útil quando consumer já aplica easing próprio |
| `easeIn` | Ease In | Começa devagar, acelera (resistência inicial) |
| `easeOut` | Ease Out | Começa rápido, desacelera (liberação gradual) |
| `easeInOut` | Ease In Out | Smooth em ambos os extremos (default, ideal p/ respiração) |
| `sine` | Sine (ease-out) | Subida rápida, slowdown suave |
| `cosine` | Cosine (ease-in-out) | Curva S clássica, simétrica |
| `bezier` | Cubic Bezier | CSS `ease` cubic-bezier(0.42, 0, 0.58, 1) |

### 7.1 Extensibilidade

Para adicionar uma nova curva:

```typescript
// 1. Criar arquivo em domain/curves/
export const myCustomCurve: CurveFn = (progress: number): number => {
  // implementação pura
  return progress ** 3;
};

// 2. Adicionar ao barrel domain/curves/index.ts
export { myCustomCurve } from './myCustom';

// 3. Adicionar ao CurveName union em domain/Curve.ts
export type CurveName = 'linear' | ... | 'myCustom';

// 4. Adicionar ao CURVE_NAMES
export const CURVE_NAMES = ['linear', ..., 'myCustom'] as const;

// 5. Adicionar ao CURVE_REGISTRY em Curve.ts
const CURVE_REGISTRY: Record<CurveName, CurveFn> = {
  // ...
  myCustom: myCustomCurve,
};
```

Nenhuma alteração no `BreathEngine` é necessária — consumers podem passar `curveName: 'myCustom'` ou injetar a função diretamente.

---

## 8. Profundidade (depth)

Função pura `computeDepth(phase, phaseProgress, curve)` retorna `y ∈ [0, 1]`:

| Phase | Depth |
|-------|-------|
| `null` (preparing ou completed) | 0 |
| `inhaling` | `curve(progress)` |
| `holdAfterInhale` | 1 |
| `exhaling` | `1 - curve(progress)` |
| `holdAfterExhale` | 0 |

**Por que 1 - curve para exhale:**

Mantém a sensação simétrica: ao usar `easeInOut`, a inalação sobe suave e a exalação desce suave. Sem inversão, a exalação teria easing invertido (começa rápido e desacelera).

**Visualização (curva easeInOut em ciclo 4-4-4-4):**

```
depth
  1.0 ┤      ╭──────────╮      ╭──────────╮      ╭───────
      │     ╱            ╲     ╱            ╲     ╱
      │    ╱              ╲   ╱              ╲   ╱
  0.5 ┤   ╱                ╲ ╱                ╲ ╱
      │  ╱                  ╳                  ╳
      │ ╱                  ╱ ╲                ╱ ╲
  0.0 ┤╱                  ╱   ╲              ╱   ╲
      └──────────────────────────────────────────────►
      0   4   8   12  16  20  24  28  32  ...
      ih  ha  ex  he  ih  ha  ex  he  ih  ...
```

---

## 9. Integração com Timer Engine

### 9.1 Contrato

O Breath Engine requer:

- `TimerEngine` instância em estado `running` no momento de `start()`.
- `MonotonicClock` para emissão de eventos com timestamps.

### 9.2 Fluxo

```
[User]                  [BreathEngine]                 [TimerEngine]
  │                          │                               │
  │ start()                  │                               │
  ├─────────────────────────►│                               │
  │                          │ check: timerState === 'running'?
  │                          │ capture sessionStartedAtTimerElapsedMs
  │                          │ emit breath-started            │
  │                          │ (if no prepMs) cycle-started   │
  │                          │ (if no prepMs) phase-changed   │
  │                          │                               │
  │                          │◄─────── tick ──────────────────┤
  │                          │ sessionElapsedMs = totalElapsed - baseline
  │                          │ compute phase                  │
  │                          │ detect transitions             │
  │                          │ emit events                    │
  │                          │                               │
  │                          │◄── backgrounded ──────────────┤
  │                          │ state → interrupted            │
  │                          │ emit interrupted               │
  │                          │                               │
  │                          │◄── foregrounded ──────────────┤
  │                          │ resume to current phase        │
  │                          │ emit resumed-from-interrupt    │
  │                          │                               │
  │ cancel()                 │                               │
  ├─────────────────────────►│                               │
  │                          │ state → cancelled              │
  │                          │ emit cancelled                 │
```

### 9.3 Por que não polling

Polling (`setInterval` próprio) quebraria a regra "Timer Engine é a única fonte de tempo". Event-driven garante:

- Sincronização perfeita com Timer Engine.
- Sem timers paralelos competindo por recursos.
- Background/foreground tratado pelo Timer Engine e propagado via eventos.

### 9.4 Time scaling

O Timer Engine tem `timeScale` (default 1.0). Se alterado para 2.0, todos os ticks e eventos carregam `totalElapsedMs` acelerado 2x. O Breath Engine, lendo `totalElapsedMs`, naturalmente acelera — sem necessidade de configuração adicional.

Isso é usado por:

- **Testes:** `scale = 100` simula 20 minutos em 12s.
- **Demos:** `scale = 0.5` relaxa sessão.

---

## 10. Pontos de extensão

| Para customizar | Implemente |
|-----------------|------------|
| Curva de interpolação | Função pura `CurveFn` ou registro em `Curve.ts` |
| Algoritmo de cálculo de fase | Substituir `PhaseCalculator.computePhaseInfo` (função pura, fácil de mockar) |
| Profundidade customizada (e.g., para áudio) | Substituir `DepthCalculator.computeDepth` ou consumir `snapshot.depth` |
| Eventos customizados (e.g., `phase-tick` a 60Hz) | Subscrever ao Timer Engine diretamente + correlacionar com Breath snapshot |
| Listener error handler | `onListenerError` em deps |

---

## 11. Limitações

### 11.1 Conhecidas

1. **Não tolera `TimerEngine` parado.** Se o caller esquecer de iniciar o Timer Engine, `start()` lança AppError. Não há fallback silencioso.

2. **Sem persistência.** Após kill do app, session state é perdido. Persistência é responsabilidade do Session Engine.

3. **Não emite `phase-tick` 60Hz.** Emite `phase-changed` em transições apenas. Consumers que precisam de 60Hz devem subscrever ao Timer Engine diretamente.

4. **`breath-completed` vs `cycle-completed` vs `completed`** — consumidores devem escolher sabiamente:
   - Use `breath-completed` para sincronizar com fim de exalação (respiração ativa terminou).
   - Use `cycle-completed` para sincronizar com fim do hold final (ciclo inteiro terminou).
   - Use `completed` para detectar fim da sessão inteira.

5. **`resumed-from-interrupt` é extensão.** Não está no spec original; consumidores que precisam de portabilidade extrema devem tratar via `phase-changed` + flag `state === 'interrupted'`.

### 11.2 Não-cobre

- **Validação clínica:** sem warnings de overdoses ou detecção de padrões anormais.
- **Áudio guiado:** o Breath Engine não toca áudio; emite apenas eventos.
- **Animação visual:** consumers devem animar a partir de `snapshot.depth`.
- **Detecção de batimento cardíaco:** fora do escopo.

---

## 12. Reuso em outras plataformas

| Plataforma | Como |
|------------|------|
| **Mobile (iOS/Android)** | Já integrado. Timer Engine polyfilled. |
| **Web (Browser)** | Mesma API. Timer Engine via `performance.now()`. |
| **Desktop (Electron/Tauri)** | Mesma API. Funciona em qualquer thread com Timer Engine. |
| **Wearables (watchOS/Wear OS)** | Timer Engine + fakes para testes. Validar Doze mode. |
| **AraOS (Node.js backend)** | Timer Engine via `performance.now()`. Breath Engine simula sessão server-side para analytics. |
| **Apple Watch** | Limitar `cycles` para sessões curtas. Validar consumo de bateria. |

**Requisito único:** `TimerEngine` e `MonotonicClock` (qualquer runtime JS 2026).

---

## 13. Performance

### 13.1 Throughput

| Operação | Tempo |
|----------|-------|
| `PhaseCalculator.computePhaseInfo` | ~0.001ms (puramente algébrico) |
| `DepthCalculator.computeDepth` | ~0.0001ms |
| `BreathEngine.handleTick` (sem listeners) | ~0.005ms |
| `BreathEngine.handleTick` (100 listeners) | ~0.5ms |
| Inicialização | < 1ms |

### 13.2 Benchmarks sintéticos (FakeClockProvider)

| Operação | Tempo |
|----------|-------|
| 100k PhaseCalculator calls | < 50ms |
| 1M DepthCalculator calls | < 50ms |
| 100 BreathEngine instances | < 50ms |
| Full 80s session (5 cycles, fake) | < 500ms |
| 100 listeners × 1 tick | < 50ms |

### 13.3 Memory

- BreathEngine baseline: ~10KB heap.
- 1 listener: +1KB.
- 100 listeners: +50KB.
- Sem leaks após `dispose()`.

### 13.4 Drift

Em sessão de 20 minutos simulada: drift < 50ms (limitado pelo drift do Timer Engine subjacente).

---

## 14. Referências

- Constituição do Produto: `docs/AraFlow/32_FINAL_PRODUCT_DECISIONS.md`
- Constituição Técnica: `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md`
- Sprint 0 Foundation: `docs/AraFlow/34_SPRINT0_IMPLEMENTATION_REPORT.md`
- Sprint 1 Timer Engine: `docs/AraFlow/35_SPRINT1_TIMER_REPORT.md`
- Sprint 2 Report: `docs/AraFlow/36_SPRINT2_BREATH_REPORT.md`
- Timer Engine API: `docs/AraFlow/35_TIMER_ENGINE.md`
- ADR-019: `docs/adr/araflow/019-master-clock-implementation.md`
- ADR-020: `docs/adr/araflow/020-breath-engine.md`

---

**Mantido por:** Chief Technology Officer (CTO)
**Última atualização:** 2026-06-25
**Próxima revisão:** após Sprint 3 (Protocol Engine) para validar integração.