# 028 — Animation Renderer (separação Engine ↔ Renderer)

- **Status:** Accepted
- **Data:** 2026-07-01
- **Sprint:** 9 / Fase 2.1 — First Visual Experience

## Contexto

A Sprint 8 introduziu o **Animation Engine** como uma camada pura de
projeção: dado `Runtime + Breath + Timer + Session`, emite
`AnimationFrame`s normalizados (radius/opacity/normalizedProgress em
[0,1]). O Engine é completamente agnóstico de renderização — não
sabe o que é Skia, React Native, SVG, Canvas, ou Lottie.

A Sprint 9 precisa **mostrar** esses frames em uma tela. A escolha
arquitetural crítica é: **onde mora o código de renderização?**

## Decisão

### 1. Renderer separado do Engine

O Renderer é um **módulo independente** (`@presentation/animation-renderer`)
que vive na Presentation layer, fora do Core. O Engine **não conhece**
o Renderer; o Renderer consome `AnimationFrame`s via uma interface
pura (`AnimationRenderer`).

```
Core                                          Presentation
─────────                                     ─────────────
Runtime ──┐                                   @presentation/animation-renderer
Breath  ──┼─→ AnimationEngine ── AnimationFrame ──→ frameToScene ──→ Renderer
Timer   ──┘                                                 (RN / Skia / SVG)
```

### 2. Interface mínima: `render(scene) + dispose()`

```ts
export interface AnimationRenderer {
  readonly id: string;
  render(scene: RendererScene): void;
  dispose(): void;
}
```

A interface é **deliberadamente minimalista**. Não há "setText",
"setCircle", "beginFrame" — o Renderer recebe uma `RendererScene`
completa e é livre para interpretá-la como quiser.

### 3. Tagged-union `RendererCommand`

```ts
export type RendererCommand =
  | { kind: 'circle'; ... }
  | { kind: 'text'; ... }
  | { kind: 'arc'; ... }
  | { kind: 'rect'; ... };
```

Cada variante é um **value object imutável**. A Renderer
responsabilidade é traduzir comandos para chamadas nativas do backend
escolhido.

### 4. Projeção pura: `animationFrameToScene(frame, opts) → scene`

A conversão `AnimationFrame → RendererScene` é uma **função pura**,
sem side effects. Isso permite:

- Testes sem mock de animação;
- Reuso por múltiplos backends (mesma scene, RN vs Skia);
- Debug visual imprimindo a scene como JSON.

### 5. Implementação Sprint 9: React Native primitives

A implementação atual usa `Animated` API + `View` com `borderRadius`
para círculos. **Decisão consciente** contra
`@shopify/react-native-skia`. Razões:

| Razão | Detalhe |
|-------|---------|
| Sem rebuild nativo | Skia requer `pod install` + `gradle` build, fora do escopo da Sprint 9 |
| Perf aceitável | `Animated.timing` em JS thread com 16ms transition chega a 60 FPS |
| Drop-in replacement | Skia renderer pode entrar depois sem mudar o contrato |
| Validar pipeline | Sprint 9 valida o pipeline Core→Renderer→Tela, não a tecnologia gráfica |

Quando a Sprint 10+ introduzir efeitos mais sofisticados (shaders,
partículas), o backend Skia substitui este via `createSkiaRenderer()`
— o contrato `AnimationRenderer` permanece.

## Alternativas consideradas

### A. Renderer dentro do Engine

**Rejeitado.** Mistura Core (puro, determinístico, testável) com
rendering (efeitos colaterais, dependências nativas). O Engine
perderia sua portabilidade para outros frontends (web, TV, watch).

### B. Engine conhece o Renderer (callback direto)

**Rejeitado.** Cria acoplamento bidirecional entre Core e
Presentation. Limitaria reuso do Engine em pipelines não-visuais
(analytics, telemetria, replay).

### C. Skia desde a Sprint 9

**Rejeitado.** Sprint 9 é a primeira experiência visual — o objetivo
é validar o pipeline end-to-end, não maximizar a tecnologia gráfica.
Skia entra na Sprint 10+ com critérios de qualidade visual mais
exigentes.

### D. SVG ou Canvas 2D

**Rejeitado.** SVG é lento em RN; Canvas 2D não está disponível nativamente
no mobile sem polyfills.

## Consequências

### Positivas

- **Backend swap trivial.** Trocar RN primitives por Skia é mudar
  uma factory — `FirstBreathSession` não sabe a diferença.
- **Testes isolados.** A projeção pura (`frameToScene`) tem 100% de
  cobertura sem precisar de renderer real.
- **Engine permanece puro.** Core não importa `react-native` em
  momento algum.
- **Reuso web.** Se a AraFlow ganhar versão web (Expo), um renderer
  Canvas pode ser plugado sem reescrever a lógica de sessão.

### Negativas

- **Latência de 1 frame** entre projection e render. Aceitável: a
  pipeline inteira roda dentro de 16ms (1 frame a 60 FPS).
- **Trade-off vs Skia.** Sem shaders ou path effects até a Sprint 10.
  Suficiente para o círculo respiratório atual.

## Compliance

- **Constituição Técnica §02 Clean Architecture + Feature-Based**:
  Renderer em `presentation/`, orquestração em `features/session/`.
- **§17 TypeScript strict + branded types**: nenhum `any` na interface
  pública; comandos são unions discriminados por `kind`.
- **§19 Master Clock**: a sessão usa o clock do Timer Engine; o
  Renderer recebe `monotonicMs` da scene, sem `Date.now()` interno.

## Notas de implementação

- `transitionMs = 16` é o default — pode ser afinado por dispositivo.
- `useNativeDriver: false` é necessário para `borderRadius` e
  `borderColor`. Trade-off explícito; aceitável pelo volume de
  elementos (1-3 por frame).
- A scene é construída uma vez por frame; o Renderer apenas
  atualiza valores animados. Não há recriação de View.

## Cross-references

- ADR-027: `docs/adr/araflow/027-animation-engine.md` (o Engine)
- Sprint 9 doc: `docs/AraFlow/45_FIRST_VISUAL_EXPERIENCE.md`
- Sprint 9 report: `docs/AraFlow/45_SPRINT9_FIRST_VISUAL_REPORT.md`