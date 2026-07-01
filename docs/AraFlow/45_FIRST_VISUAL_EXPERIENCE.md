# First Visual Experience — Sprint 9

> **Status:** Entregue (commit pendente)
> **Sprint:** 9 / Fase 2.1 — First Visual Experience
> **Data:** 2026-07-01

## Visão

A Sprint 9 fecha o ciclo Core→Apresentação. Após 8 sprints consolidando
as engines determinísticas (Runtime, Breath, Protocol, Animation), a
**primeira experiência visual** do AraFlow chega à tela: um círculo
respiratório que cresce e diminui sincronizado com uma sessão real de
"Respiração Diafragmática".

Este documento descreve a arquitetura entre o **Animation Engine**
(Sprint 8) e a **Renderização**, mais a **única tela** entregue nesta
sprint.

## Camadas

```
┌─────────────────────────────────────────────────────────────────┐
│  Presentation / Feature                                         │
│                                                                 │
│  src/features/session/FirstBreath/                              │
│    ├─ FirstBreathScreen.tsx   (React: botões + JSX)             │
│    └─ FirstBreathSession.ts   (Pure TS: Runtime → Animation     │
│                                → FrameToScene → Renderer)       │
├─────────────────────────────────────────────────────────────────┤
│  Animation Renderer (Sprint 9 — NOVO)                           │
│                                                                 │
│  src/presentation/animation-renderer/                           │
│    ├─ domain/                                                   │
│    │   ├─ RendererColor.ts       (RGBA value type + helpers)    │
│    │   ├─ RendererPrimitive.ts   (tagged-union draw commands)   │
│    │   ├─ RendererScene.ts       (frozen scene = canvas + list) │
│    │   ├─ AnimationFrameToScene.ts (pure projection)            │
│    │   └─ AnimationRenderer.ts   (interface contract)           │
│    └─ rn/                                                       │
│        └─ ReactNativeRenderer.ts  (RN primitives implementation) │
├─────────────────────────────────────────────────────────────────┤
│  Core (Sprints 1–8) — intocado                                  │
│                                                                 │
│  @core/runtime → @core/animation-engine → AnimationFrame         │
└─────────────────────────────────────────────────────────────────┘
```

## Renderer Interface

```ts
// src/presentation/animation-renderer/domain/AnimationRenderer.ts
export interface AnimationRenderer {
  readonly id: string;
  render(scene: RendererScene): void;
  dispose(): void;
}

export const ANIMATION_RENDERER_VERSION = '1.0.0' as const;
```

A interface é **backend-agnóstica**. Implementações possíveis:

| Backend | Status | Notas |
|---------|--------|-------|
| React Native primitives (`Animated` + `View`) | ✅ Sprint 9 | `rn-primitives-v1` |
| Skia (`@shopify/react-native-skia`) | ⏭️ Sprint 10+ | Drop-in replacement |
| SVG (`react-native-svg`) | ⏭️ sob demanda | Web-friendly |
| Canvas 2D (Web) | ⏭️ sob demanda | Browser preview |

A escolha por **React Native primitives** na Sprint 9 foi deliberada
— ver ADR-028 para os detalhes.

## Tagged-union Draw Commands

```ts
export type RendererCommand =
  | { kind: 'circle'; center, radius, fill, stroke, strokeWidth }
  | { kind: 'text'; position, content, size, color, align }
  | { kind: 'arc'; center, radius, startAngle, sweepAngle, color, strokeWidth }
  | { kind: 'rect'; origin, size, fill };
```

Cada `RendererScene` é uma lista ordenada de comandos congelados:

```ts
export interface RendererScene {
  readonly canvasSize: { width: number; height: number };
  readonly commands: readonly RendererCommand[];
  readonly monotonicMs: number;
}
```

## Pure Projection: AnimationFrame → RendererScene

`animationFrameToScene(frame, options)` é uma **função pura** que
projeta um `AnimationFrame` (Sprint 8) em uma `RendererScene` (Sprint
9). Regras:

| Frame field | Scene output |
|-------------|--------------|
| `frame.radius` (0..1) | circle radius = `radius × maxRadiusPx` |
| `frame.opacity` (0..1) | circle fill.a |
| `frame.normalizedProgress` (0..1) | arc sweepAngle |
| `frame.label` | text content (phase label) |
| `frame.remainingTime` (ms) | counter text (MM:SS format) |

A projeção **não toca** em React, RN, ou DOM. É determinística e
testável como pura.

## Implementação React Native

`ReactNativeRenderer` mantém 3 `Animated.Value`s internos:

- `_radiusAnim` — diametro do círculo (borderRadius)
- `_opacityAnim` — opacidade
- `_sweepAnim` — arco de progresso (border-arc trick)

`useNativeDriver: false` é usado porque `borderRadius`/`borderColor`
não são animáveis via driver nativo. Compensamos com transições curtas
(`transitionMs = 16ms` ≈ 1 frame) para chegar a 60 FPS no JS thread.

## Composição: `FirstBreathSession`

`FirstBreathSession` é **pure TypeScript** — sem React. Ele:

1. Cria um `RuntimeEngine` com `runtimeId = 'araflow-first-breath-v1'`.
2. Compila a fonte JSON do protocolo.
3. Cria um `AnimationEngine` via `createAnimation({ runtime })`.
4. Subscreve aos eventos `animation-frame`.
5. Projeta cada frame em uma scene e despacha ao `AnimationRenderer`.
6. Dirige `animation.update(now())` via `requestAnimationFrame`.
7. Expõe `pause()`, `resume()`, `stop()` como `Result`-safe.

## Tela: First Breath

Única tela da Sprint 9. Conteúdo:

- **Logo** "AraFlow" (texto placeholder).
- **Nome do protocolo** carregado do JSON.
- **Contador** de tempo restante.
- **Label** de fase: `Inspire` / `Segure` / `Expire`.
- **Círculo respiratório** desenhado pelo `ReactNativeRenderer`.
- **Botões**: Start (Iniciar), Pause (Pausar), Resume (Continuar), Stop (Parar).

**Sem navegação**, sem onboarding, sem login, sem persistência, sem
analytics, sem wearables, sem múltiplas telas, sem configurações.
Sprint 10 trará Audio Engine + experiência multissensorial.

## Demo Protocol: Respiração Diafragmática

```json
{
  "id": "01ARZ3NDEKTSV4RRFFQ69G5FA2",
  "title": "Respiração Diafragmática",
  "breath": {
    "cycles": 6,
    "phases": [
      { "type": "inhale",  "durationMs": 4000, "curve": "ease-in-out" },
      { "type": "hold-in", "durationMs": 4000, "curve": "linear" },
      { "type": "exhale",  "durationMs": 6000, "curve": "ease-in-out" }
    ]
  }
}
```

Total: 14 s × 6 ciclos = 84 s de sessão. Primeira sessão curta o
suficiente para validar end-to-end.

## Critérios de aceitação

| Critério | Como verificar |
|----------|----------------|
| Core untouched | nenhum arquivo em `mobile/src/core/**` foi modificado |
| AnimationFrame é a única entrada de animação | UI não tem cálculos de easing/radius/progress próprios |
| Renderer é swappable | trocar `createReactNativeRenderer` por `createSkiaRenderer` (futuro) não exige mudanças em `FirstBreathSession` |
| Cobre comandos circle/text/arc | testes cobrem cada variante |
| Compila em RN | typecheck zero erros nos arquivos novos |
| Único caminho até a UI | `Runtime → Animation Engine → Renderer` — não há desvios |
| Sem rede, sem I/O | nenhuma chamada a AsyncStorage, fetch, ou APIs externas |

## Próximos passos (Sprint 10)

1. **Audio Engine** — projétil multissensorial.
2. **Skia renderer** (drop-in) para animações mais sofisticadas.
3. **Múltiplas telas** e navegação.

## Cross-references

- ADR-028: `docs/adr/araflow/028-animation-renderer.md`
- Sprint 8 doc: `docs/AraFlow/44_ANIMATION_ENGINE.md`
- Sprint 8 report: `docs/AraFlow/44_SPRINT8_ANIMATION_REPORT.md`
- Constituição Técnica: `docs/araflow-constituicao-tecnica/`