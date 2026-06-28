# Animation Engine

> **Status:** Sprint 0 — Foundation stub
> **Próxima implementação:** Sprint 6

## Responsabilidade

Renderiza **animações visuais sincronizadas** com o Breath Engine. No MVP, apenas o círculo respiratório.

## O que ele faz

- Renderiza círculo respiratório em 60fps.
- Aplica curva de easing à progressão.
- Sincroniza com Breath Engine.
- Pausa em background; retoma do estado correto.

## Estrutura

```
animation-engine/
├── domain/            # AnimationState, EasingFunction
├── application/       # StartAnimation, StopAnimation, UpdateProgress
└── infrastructure/    # SkiaRenderer (ou Reanimated quando adotarmos)
```

## Dependências

- Timer Engine.
- Breath Engine.

## Consumidores

- UI (tela de sessão).

## Documentação adicional

Ver `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md` §9 (Sistema de Animação).
