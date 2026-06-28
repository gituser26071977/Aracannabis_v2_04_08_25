# Sessions Module (backend)

> **Status:** Sprint 0 — Foundation stub
> **Próxima implementação:** Sprint 9

Endpoint para receber sessões sincronizadas do mobile. Schema validado contra `shared-contracts`.

```
POST /v1/sessions        # Cria sessão
GET  /v1/sessions        # Lista sessões (paginado)
GET  /v1/sessions/:id    # Detalhe
DELETE /v1/sessions/:id  # Soft delete (LGPD)
```

Persistência: Postgres (via AraOS ou schema próprio se isolar).
