# Breath Engine

> **Status:** Sprint 0 — Foundation stub
> **Próxima implementação:** Sprint 2

## Responsabilidade

O Breath Engine controla o **ciclo respiratório em tempo real**. É o coração clínico do app. Define fases (inhale, hold-in, exhale, hold-out), transições, e progresso.

## O que ele faz

- Mantém estado da fase atual.
- Calcula progresso 0-1 dentro de uma fase.
- Transiciona entre fases baseado no protocolo.
- Emite eventos de respiração para outros engines.
- Suporta cancel, pause, resume, complete.

## Estrutura

```
breath-engine/
├── domain/            # BreathPhase, BreathCycle, BreathSession, BreathEngineState
├── application/       # StartSession, PauseSession, ResumeSession, CancelSession
└── infrastructure/    # TimerAdapter (consome Timer Engine)
```

## Dependências

- Timer Engine (sincronização).
- Protocol Engine (qual protocolo executar).

## Consumidores

- Audio Engine (cues de voz).
- Animation Engine (círculo respiratório).
- Session Engine (persistência).
- Safety Engine (limites).

## Documentação adicional

Ver `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md` §6 (Motor Respiratório).
