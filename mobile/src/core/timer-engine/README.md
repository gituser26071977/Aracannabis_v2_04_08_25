# Timer Engine

> **Status:** Sprint 0 — Foundation stub
> **Próxima implementação:** Sprint 1

## Responsabilidade

O Timer Engine é a **fonte de verdade temporal** do AraFlow. Ele é o "relógio mestre" do qual todos os outros engines (Breath, Audio, Animation) derivam seu tempo.

## O que ele faz

- Fornece **relógio monotonic** (imune a mudanças de wall clock).
- Fornece **wall clock** (afetado por mudanças, usado em timestamps persistentes).
- Emite **tick events** em frequência configurável (default 60Hz para animação; 1Hz para sessão).
- Faz **drift correction** após longos períodos em background.
- Persiste estado para recuperação após kill do app.

## Estrutura

```
timer-engine/
├── domain/            # Tipos puros (MonotonicMs, WallClockMs, TickEvent)
├── application/       # Casos de uso (StartTimer, StopTimer, GetElapsed)
└── infrastructure/    # Adaptadores (MonotonicClock, WallClock, HighResTimer)
```

## Dependências

- Nenhuma (Timer Engine é o "nível mais baixo" do Core).

## Consumidores

- Breath Engine
- Session Engine
- Audio Engine
- Animation Engine
- Analytics Engine

## Documentação adicional

Ver `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md` §10 (Sincronização Áudio-Animação-Timer) e §6 (Motor Respiratório).
