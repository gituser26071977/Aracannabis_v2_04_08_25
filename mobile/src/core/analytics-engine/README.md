# Analytics Engine

> **Status:** Sprint 0 — Foundation stub
> **Próxima implementação:** Sprint 7

## Responsabilidade

Coleta e envia **eventos de uso** para o backend. Opt-in por categoria (LGPD compliance).

## O que ele faz

- Recebe eventos de qualquer engine.
- Enriquece com contexto (userId, sessionId, appVersion).
- Fila local para offline.
- Envia para backend com backoff exponencial.
- Honra opt-in/opt-out por categoria.

## Estrutura

```
analytics-engine/
├── domain/            # AnalyticsEvent, EventCategory
├── application/       # Track, Flush, EnableCategory, DisableCategory
└── infrastructure/    # EventQueue, HttpUploader, ConsentStore
```

## Dependências

- Nenhuma (consumidor passivo de outros engines).

## Consumidores

- Backend (analytics aggregator).
- LGPD consent store.

## Documentação adicional

Ver `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md` §14 (Observabilidade).
