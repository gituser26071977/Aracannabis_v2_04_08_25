# Protocols Module (backend)

> **Status:** Sprint 0 — Foundation stub
> **Próxima implementação:** Sprint 3

Gerencia catálogo de protocolos versionados.

```
GET    /v1/protocols
GET    /v1/protocols/:id
GET    /v1/protocols/:id/versions
POST   /v1/protocols           # admin only
PUT    /v1/protocols/:id       # admin only
```

Versionamento: semver. Apenas o servidor publica novas versões; clientes consomem.
