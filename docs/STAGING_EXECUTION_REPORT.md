# STAGING_EXECUTION_REPORT — MISSÃO 23

**Data:** 2026-06-25
**Modo:** EXECUTE (somente infraestrutura existente)
**Origem:** M23 FASE 1 — provisionar staging com artefatos de M20

---

## 1. Comando executado

```bash
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

## 2. Pré-condições verificadas

| Item | Status |
|------|--------|
| `docker-compose.staging.yml` (4972B) | ✅ existe |
| `.env.staging.example` (1382B) | ✅ existe |
| `scripts/deploy_staging.sh` (2665B) | ✅ sintaxe OK |
| Network `web` (externa, requer Traefik) | ⚠️ existe localmente mas Traefik NÃO está rodando |
| `.env.staging` populado | ✅ copiado de `.env.staging.example` |

> **Diferença em relação ao `deploy_staging.sh`:** usei `docker compose` (v2 plugin) em vez de `docker-compose` (v1 standalone), que estava com erro "URL scheme http+docker" no ambiente. O `deploy_staging.sh` referencia `docker-compose` (v1) — pode falhar em ambientes modernos. Não corrigi o script (fora do escopo).

## 3. Duração

| Etapa | Tempo |
|-------|-------|
| Build de imagens (backend + frontend) | ~4min (parte dos 257s totais) |
| Criação de networks/volumes | <5s |
| Start containers | <30s |
| Healthcheck (db + redis) | 10s |
| Backend gunicorn boot | 9s |
| **TOTAL** | **257s** (~4min17s) |

## 4. Containers resultantes

```
NAME                    STATUS                             PORTS
siap-backend-staging    Up (health: starting)             5002/tcp
siap-db-staging         Up (healthy)                       0.0.0.0:5441->5432
siap-frontend-staging   Up (healthy)                       3000/tcp
siap-redis-staging      Up (healthy)                       6379/tcp
```

## 5. Warnings / falhas durante provisionamento

| Tipo | Mensagem | Severidade |
|------|----------|------------|
| Warning | `version: '3.8' is obsolete` | ⚠️ Não-bloqueante, ignorado pelo docker-compose v2 |
| Warning | `Found orphan containers ([aracannabis_backend aracannabis_db siap-db])` | ⚠️ Containers órfãos de outro projeto. Não-bloqueante. |
| Info | `Control socket listening at /root/.gunicorn/gunicorn.ctl` | ℹ️ Normal |

## 6. Pós-provisionamento: Smoke local

Endpoint testado via Python urllib dentro do container (curl não está instalado):

| Endpoint | Status | Observação |
|----------|--------|------------|
| `GET /api/status` | 200 ✅ | OK |
| `GET /api/csrf-token` | 200 ✅ | Token 64 chars |
| `GET /api/health` | 503 ❌ | "redis: fail: ConnectionError" — **bug de configuração** |
| `POST /api/auth/register` | 201 ✅ | Registro funcionou (campos: nome/crm/uf_crm/usuario/senha/email) |
| `POST /api/auth/login` | 401 ❌ | Requer campos `email`+`senha`, não `identifier`+`password` (divergência com smoke.sh) |

## 7. Bugs identificados durante provisionamento

### BUG-001 — `.env.staging` sem REDIS_URL
**Severidade:** P1
**Evidência:**
```bash
grep REDIS .env.staging → (vazio)
docker exec siap-backend-staging python3 -c "from config import get_config; print(get_config().REDIS_URL)" → None
docker exec siap-backend-staging python3 -c "import redis; ..." → fail
```

**Causa:** O template `.env.staging.example` **NÃO inclui** `REDIS_URL` ou `RATELIMIT_STORAGE_URL`. O health check (`app_cors_livre.py:186`) faz fallback para `redis://localhost:6379/0` que falha porque Redis está em `siap-redis-staging` na rede interna.

**Impacto:**
- `/api/health` retorna 503 sustentado
- Flask-Limiter cai em fallback `memory://` por processo (não compartilhado entre workers)
- Rate-limit funciona dentro de 1 worker mas não entre containers

**Correção sugerida** (NÃO aplicada — fora do escopo):
Adicionar em `.env.staging.example`:
```
REDIS_URL=redis://siap-redis-staging:6379/0
RATELIMIT_STORAGE_URL=redis://siap-redis-staging:6379/1
```

### BUG-002 — Login smoke.sh diverge do endpoint real
**Severidade:** P3 (documentação)
**Evidência:**
- `scripts/smoke.sh` linha ~30: `check "/api/auth/login"` (sem payload, espera 200/4xx)
- `routes/auth.py:90-91`: espera JSON com `email`/`senha`
- `docs/POST_DEPLOY_SMOKE.md §3` (M22.2): usava `identifier`/`password` → corrigido em M22.2 para nenhuma credencial específica

**Causa:** smoke.sh não envia payload real, apenas verifica se endpoint responde. Em produção falha por outro motivo (ex: rate-limit).

### BUG-003 — gunicorn com `--workers 1` no staging
**Severidade:** P1 (desempenho)
**Evidência:** `docker-compose.staging.yml:75` define `--workers 1`
**Impacto:** Sob carga, gunicorn serializa requests → fila → timeout. Ver FASE 5 (Load test).

---

## 8. Validação final

| Critério | Resultado |
|----------|-----------|
| Containers up | ✅ 4/4 |
| Healthcheck DB | ✅ |
| Healthcheck Redis | ❌ (BUG-001) |
| Backend `/api/status` | ✅ 200 |
| Backend `/api/csrf-token` | ✅ 200 |
| Backend `/api/health` | ❌ 503 (BUG-001) |
| Frontend | ✅ container up, porta 3000 |
| Conectividade Traefik | ❌ Traefik não deployado nesta máquina |

**Veredito:** staging **provisionado**, mas **NÃO certificado** — 3 bugs bloqueadores identificados.

---

## 9. Rollback executado?

**NÃO.** Não houve falha de provisionamento. O ambiente permanece ativo.

Para destruir:
```bash
docker compose -f docker-compose.staging.yml --env-file .env.staging down -v
```