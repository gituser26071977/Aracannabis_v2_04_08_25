# Analytics Module (backend)

> **Status:** Sprint 0 — Foundation stub
> **Próxima implementação:** Sprint 7

Recebe eventos de analytics do mobile, com opt-in LGPD por categoria.

```
POST /v1/analytics/events    # batch
GET  /v1/analytics/aggregate # admin only
```

Não armazena PII. Eventos identificam o usuário por `userId` (hashable) apenas quando categoria está opted-in.
