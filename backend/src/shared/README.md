# Shared (backend)

> **Status:** Sprint 0 — Foundation stub

Cross-cutting concerns do backend:
- `logger.ts` — pino wrapper
- `errors.ts` — AppError + mapping para HTTP
- `auth.ts` — JWT verify, scope check
- `idempotency.ts` — Idempotency-Key middleware
- `rate-limit.ts` — rate limiting (Fastify plugin)
- `request-context.ts` — request-scoped context (logger, trace, userId)

Implementação: Sprint 9.
