# Session Engine

> **Status:** Sprint 0 — Foundation stub
> **Próxima implementação:** Sprint 4

## Responsabilidade

Gerencia o **ciclo de vida da sessão**: created, running, paused, completed, cancelled.

## O que ele faz

- Cria sessão com ID único.
- Coordena Breath Engine durante a sessão.
- Persiste estado localmente (offline-first).
- Sincroniza com servidor quando online.
- Mantém histórico local (últimas 100) e delega o resto ao servidor.

## Estrutura

```
session-engine/
├── domain/            # Session, SessionState machine
├── application/       # CreateSession, StartSession, PauseSession, etc.
└── infrastructure/    # LocalSessionRepository, RemoteSessionSync
```

## Dependências

- Breath Engine.
- Protocol Engine.
- Timer Engine.

## Consumidores

- UI (tela de sessão, histórico).
- Analytics Engine (eventos de sessão).
- Safety Engine (validação de limites).

## Documentação adicional

Ver `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md` §11 (Persistência) e §12 (Sincronização).
