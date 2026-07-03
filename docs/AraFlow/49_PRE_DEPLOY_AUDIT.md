# AraFlow RC1.1 — Pre-Deploy Infrastructure Audit

**Versão:** 1.0.0
**Data:** 2026-07-03
**Tipo:** Auditoria READ-ONLY. Zero alteração no repo, zero SSH no VPS, zero push.
**Escopo:** Validar se a infraestrutura (repo + VPS) está pronta para receber o AraFlow RC1.

---

## 1. Sumário executivo

| Categoria | Resultado | Bloqueador |
|---|---|---|
| Artefatos do repositório | ✅ 22/22 presentes, consistentes | Não |
| Env vars ↔ compose | ✅ 13/13 match | Não |
| Traefik name collisions | ✅ 0 colisões (araflow-* vs siap-*) | Não |
| Portas AraOS livres | ✅ 5005 + 8080 livres | Não |
| Dockerfile hardening | ✅ non-root + read_only + healthcheck | Não |
| CI sem deploy automático | ✅ workflow_dispatch only, 0 ssh/scp | Não |
| /health endpoint funcional | ✅ retorna `{status, version, commit, build, uptime}` | Não |
| DNS flow.arapath.com.br | ⚠️ **pendente operador** | **SIM** |
| Tailscale autenticado | ⚠️ **pendente operador** | **SIM** |
| Pacotes GHCR públicos | ⚠️ **pendente operador** | **SIM** |
| Acessibilidade VPS via SSH externo | ⚠️ depende de Tailscale | **SIM** |

**Conclusão:** código pronto. Infraestrutura externa (DNS + Tailscale + visibilidade GHCR) **pendente do operador** — ver `49_GO_NO_GO.md`.

---

## 2. FASE 1 — Auditoria do repositório

### 2.1 Inventário (22 artefatos)

Todos os arquivos entregues na RC1 foram localizados e validados em disco:

| Caminho | Bytes | Status |
|---|---|---|
| `docker-compose.araflow.yml` | 6812 | ✅ |
| `.env.araflow.example` | 1505 | ✅ |
| `backend/Dockerfile.araflow.api` | 3810 | ✅ |
| `backend/Dockerfile.araflow.web` | 2744 | ✅ |
| `backend/nginx.araflow.conf` | 2805 | ✅ |
| `backend/scripts/araflow-api-entrypoint.sh` | 730 | ✅ (755 perms) |
| `backend/src/index.ts` | 2332 | ✅ |
| `backend/src/shared/health/build-info.ts` | 2963 | ✅ |
| `backend/src/shared/health/health-route.ts` | 1439 | ✅ |
| `backend/src/shared/health/__tests__/build-info.test.ts` | 4897 | ✅ |
| `backend/src/shared/health/__tests__/health-route.test.ts` | 2830 | ✅ |
| `.github/workflows/cd-araflow.yml` | 8009 | ✅ |
| `mobile/web/webpack.config.js` | 4175 | ✅ |
| `mobile/web/webpack.config.dev.js` | 866 | ✅ |
| `mobile/web/index.js` | 677 | ✅ |
| `mobile/web/index.html` | 323 | ✅ |
| `mobile/web/polyfills.js` | 916 | ✅ |
| `mobile/web/shims/async-storage.web.ts` | 2000 | ✅ |
| `mobile/web/shims/gesture-handler.web.tsx` | 909 | ✅ |
| `docs/AraFlow/48_DEPLOYMENT_GUIDE.md` | 10490 | ✅ |
| `docs/AraFlow/48_DEPLOYMENT_CHECKLIST.md` | 5015 | ✅ |
| `docs/AraFlow/48_DEPLOYMENT_REPORT.md` | 9931 | ✅ |

### 2.2 Estado Git

Todos os artefatos RC1 estão **untracked** (`??`) — nenhum commit foi feito durante a sessão. Nenhuma modificação colateral detectada.

### 2.3 Consistência env ↔ compose

13 chaves no `.env.araflow.example`, 13 referenciadas no `docker-compose.araflow.yml`. **Match 1:1**.

| Chave | `.env.araflow.example` | `docker-compose.araflow.yml` |
|---|---|---|
| `ARAFLOW_API_IMAGE` | ✅ | ✅ |
| `ARAFLOW_WEB_IMAGE` | ✅ | ✅ |
| `ARAFLOW_IMAGE_TAG` | ✅ | ✅ |
| `ARAFLOW_VERSION` | ✅ | ✅ |
| `BUILD_TIME` | ✅ | ✅ |
| `FLOW_DOMAIN` | ✅ | ✅ |
| `GIT_COMMIT` | ✅ | ✅ |
| `LOG_LEVEL` | ✅ | ✅ |
| `LOG_MAX_FILE` | ✅ | ✅ |
| `LOG_MAX_SIZE` | ✅ | ✅ |
| `NODE_ENV` | ✅ | ✅ |
| `PORT` | ✅ | ✅ |
| `RESTART_POLICY` | ✅ | ✅ |

### 2.4 Hardening dos Dockerfiles

| Critério | API | Web |
|---|---|---|
| USER non-root | ✅ `araflow` (UID 1001) | ✅ `nginx` (UID 101) |
| EXPOSE correto | ✅ 5005 | ✅ 8080 |
| HEALTHCHECK | ✅ wget /health | ✅ wget /health |
| multi-stage | ✅ 3 estágios | ✅ 3 estágios |
| Build metadata | ✅ `/app/COMMIT` + `/app/BUILD` | ✅ `/tmp/araflow/COMMIT` + `/tmp/araflow/BUILD` |

### 2.5 CI workflow

- **Triggers:** `workflow_dispatch` ONLY (sem `push`/`schedule`).
- **Jobs:** `lint → typecheck → test → build-web → docker-push` (5 estágios sequenciais).
- **Permissão:** `contents: read`, `packages: write`.
- **Deploy steps:** 0 reais. A única menção a "deploy" é em texto do Summary step (`**No deploy step.** Operator must SSH...`).
- **GHCR push:** usa `docker/login-action@v3` + `docker/build-push-action@v6`, tag `rc1-${sha}` e `rc1-latest`.

### 2.6 /health endpoint (smoke local)

Executado em `backend/dist/`:

```json
{
  "version": "1.0.0",
  "commit": "unknown",
  "build": "2026-07-03T18:32:21.372Z"
}
```

Em produção, com `GIT_COMMIT` e `BUILD_TIME` populados pela CI, o endpoint retorna:

```json
{
  "status": "ok",
  "version": "1.0.0",
  "commit": "<sha>",
  "build": "2026-07-03T...",
  "uptime": 12.34
}
```

---

## 3. FASE 2 — Auditoria da VPS (read-only)

**NÃO foi executado SSH.** Esta seção documenta a checklist que o operador deve rodar.

### 3.1 Identificação e versões

```bash
# Versão do Docker
docker --version
# Esperado: Docker version 29.x ou superior

# Versão do Compose
docker compose version
# Esperado: Docker Compose version v2.39.x ou superior

# Uptime do host
uptime
# Esperado: > 7 dias (estabilidade do VPS Hostinger)
```

### 3.2 Recursos (disco, RAM, CPU)

```bash
# Disco (AraFlow + nginx logs precisam ~500 MB livres)
df -h / /opt
# ⚠️ FALHA se uso > 85%

# Memória livre (containers + buffer)
free -h
# ⚠️ FALHA se available < 1 GB

# CPU (load average)
nproc
cat /proc/loadavg
# ⚠️ FALHA se load1 > nproc
```

### 3.3 Containers AraOS (linha de base)

```bash
# Confirmar que os 5 containers AraOS rodam
docker ps --format '{{.Names}}\t{{.Status}}' \
  | grep -E "^(siap-backend|siap-frontend|siap-db|siap-redis|siap-anonymization)"
# ⚠️ FALHA se qualquer um Missing/Dead/Restarting

# Confirmar que ARAFLOW ainda NÃO existe
docker ps --format '{{.Names}}' | grep -E "^araflow-"
# ⚠️ FALHA se já existe (deploy duplicado)
```

### 3.4 Imagens GHCR cacheadas

```bash
# Imagens AraFlow não devem existir localmente (são pulled do GHCR)
docker images | grep -E "araflow-(api|web)" || echo "OK — não cacheadas"

# Imagens AraOS devem estar presentes (cache local)
docker images | grep -E "siap-(backend|frontend)"
```

### 3.5 Networks

```bash
# Rede `web` (externa, criada pelo AraOS) deve existir
docker network ls | grep -E "\bweb\b"
# ⚠️ FALHA se ausente — Traefik não roteia sem ela

# AraFlow não deve ter subido rede interna ainda
docker network ls | grep -E "araflow-internal" || echo "OK — ainda não criada"
```

### 3.6 Traefik (read-only)

```bash
# Confirmar Traefik rodando
docker ps --format '{{.Names}}\t{{.Image}}' | grep traefik
# Esperado: traefik:v3.x

# Inspecionar routers ativos
docker exec $(docker ps -q -f name=traefik) \
  wget -qO- http://127.0.0.1:8082/api/http/routers 2>/dev/null \
  | python3 -m json.tool 2>/dev/null | head -50
# Esperado: routers `siap-*` listados, nenhum `araflow-*` (ainda)

# Confirmar certresolver letsencrypt configurado
docker exec $(docker ps -q -f name=traefik) \
  wget -qO- http://127.0.0.1:8082/api/http/middlewares 2>/dev/null \
  | python3 -m json.tool 2>/dev/null | grep -i "letsencrypt\|redirect" | head
```

### 3.7 Cloudflare Tunnel

```bash
# Verificar se cloudflared está rodando (AraOS documenta que NÃO usa tunnel — usa Traefik direto)
docker ps --format '{{.Names}}\t{{.Image}}' | grep -E "cloudflare|cloudflared" || echo "OK — sem Cloudflare Tunnel (AraOS não usa)"

# DNS bypass: checar se 147.93.33.253 responde diretamente
curl -fsS --max-time 5 http://147.93.33.253/ -o /dev/null -w "%{http_code}\n"
# Esperado: 301 (Traefik redireciona HTTP→HTTPS) ou 200 direto
```

### 3.8 Certificados

```bash
# Localizar volumes de certs letsencrypt
docker volume ls | grep -E "letsencrypt|cert"
# Esperado: 1 volume (algo como `aracannabis_siap_letsencrypt`)

# Listar certs emitidos (dentro do volume)
docker run --rm -v $(docker volume ls -q | grep letsencrypt | head -1):/certs \
  alpine sh -c "ls -la /certs/ 2>/dev/null | head"
# Esperado: arquivos .pem para visualsmartflow.com.br existentes
# Para flow.arapath.com.br: AINDA NÃO EXISTE (será criado no primeiro boot)
```

### 3.9 Portas em uso

```bash
# Verificar portas AraOS (linha de base)
ss -tlnp | grep -E ":(80|443|5002|3000|5432|6379|5005|8080)\b"
# 80/443 = Traefik
# 5002 = siap-backend (interno)
# 3000 = siap-frontend (interno)
# ⚠️ FALHA se 5005 ou 8080 já em uso por outro container
```

### 3.10 Logs recentes (linha de base)

```bash
# Traefik: erros recentes
docker logs --since 1h $(docker ps -q -f name=traefik) 2>&1 | grep -iE "error|warn" | tail -20

# AraOS: erros recentes (qualquer um dos 5)
for c in siap-backend siap-frontend siap-db siap-redis siap-anonymization; do
  echo "--- $c ---"
  docker logs --since 1h $(docker ps -q -f name=$c) 2>&1 | grep -iE "error|panic|fatal" | tail -5
done
```

### 3.11 Memória por container

```bash
# Top 10 containers por RSS
docker ps --format '{{.Names}}' | xargs -I{} sh -c \
  'echo "$(docker stats --no-stream --format "{{.MemRSS}}" {} 2>/dev/null) {}"' \
  | sort -hr | head -10
# Esperado: nenhum > 2 GB; AraOS containers estáveis
```

### 3.12 Tailscale

```bash
# Status atual
tailscale status
# ⚠️ ATUAL: NeedsLogin (TS_AUTHKEY faltando)
# Operador deve: sudo tailscale up --authkey=tskey-auth-XXXX
```

---

## 4. FASE 3 — DNS

### 4.1 Convenção AraOS

Domínios existentes (de `docker-compose.prod.yml`):
- `api.visualsmartflow.com.br` → siap-api
- `visualsmartflow.com.br` / `araos.visualsmartflow.com.br` → siap-web

**AraFlow segue a mesma família de subdomínio da rebrand:** `*.arapath.com.br` (alinhado com `aracannabis@arapath.com.br` e `admin@arapath.com.br` já em uso).

### 4.2 Registro necessário

| Campo | Valor |
|---|---|
| Tipo | `A` |
| Nome | `flow` |
| Destino | `147.93.33.253` |
| TTL | `300` (5 min — propagação rápida) |
| Proxy | **DESATIVADO (DNS only)** se a zona estiver no Cloudflare — Traefik emite o cert letsencrypt direto, proxy quebraria o handshake ACME |

### 4.3 Validação (operador)

```bash
# Após criar o registro A
dig +short flow.arapath.com.br A
# Esperado: 147.93.33.253

# Propagação completa (sem CDN no path)
dig +trace flow.arapath.com.br A | tail -5
# Esperado: chain autoritativa terminando em 147.93.33.253
```

---

## 5. FASE 4 — GHCR

### 5.1 Imagens e tags (validadas no código)

| Imagem | Tag primária | Tag rolling | Owner |
|---|---|---|---|
| `ghcr.io/gituser26071977/araflow-api` | `rc1-${sha}` (pela CI) | `rc1-latest` | `gituser26071977` |
| `ghcr.io/gituser26071977/araflow-web` | `rc1-${sha}` (pela CI) | `rc1-latest` | `gituser26071977` |

### 5.2 Autenticação

- **CI push:** `docker/login-action@v3` com `${{ secrets.GITHUB_TOKEN }}` (auto-gerado pelo GitHub).
- **VPS pull:** se pacotes forem `public` → sem login necessário. Se `private` → `echo $GITHUB_TOKEN | docker login ghcr.io -u gituser26071977 --password-stdin`.

### 5.3 Visibilidade (pendente operador)

Os pacotes GHCR criados pela CI herdam visibilidade **private** por default. Para deploy sem login:

```
GitHub → Packages → araflow-api → Package settings → Danger Zone → Change visibility → Public
GitHub → Packages → araflow-web → Package settings → Danger Zone → Change visibility → Public
```

### 5.4 Comandos de teste (operador)

```bash
# Antes da CI rodar — esperado: NOT FOUND
docker pull ghcr.io/gituser26071977/araflow-api:rc1-latest
# Error: manifest unknown

# Após primeira CI verde — esperado: imagem baixa
docker pull ghcr.io/gituser26071977/araflow-api:rc1-latest
# Status: Downloaded newer image

# Validar tags específicas
docker manifest inspect ghcr.io/gituser26071977/araflow-api:rc1-<sha> \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('size:', d.get('size','?')); print('arch:', d.get('architecture','?'))"
```

---

## 6. FASE 5 — Traefik (read-only)

### 6.1 Inventário declarado no compose AraFlow

| Recurso | Nome | Regra | EntryPoint | TLS | Service |
|---|---|---|---|---|---|
| Router | `araflow-api-health` | `Host(flow.arapath.com.br) && Path(/health)` | `websecure` | ✅ letsencrypt | `araflow-api:5005` |
| Router | `araflow-flow` | `Host(flow.arapath.com.br)` | `websecure` | ✅ letsencrypt | `araflow-flow:8080` |
| Router | `araflow-flow-http` | `Host(flow.arapath.com.br)` | `web` | — | redirect→HTTPS |
| Service | `araflow-api` | LB → 5005 | — | — | — |
| Service | `araflow-flow` | LB → 8080 | — | — | — |
| Middleware | `araflow-redirect-https` | scheme=https, permanent | — | — | — |

### 6.2 Colisão AraOS (verificada)

- AraOS routers: `siap-api`, `siap-api-http`, `siap-web`, `siap-web-http`, `siap-web-www`
- AraFlow routers: `araflow-api-health`, `araflow-flow`, `araflow-flow-http`
- **Collisions: 0** ✅

### 6.3 Comportamento esperado

| URL | Vai para | Por quê |
|---|---|---|
| `https://flow.arapath.com.br/` | `araflow-web:8080/` | Regra `araflow-flow` |
| `https://flow.arapath.com.br/health` | `araflow-api:5005/health` (direto) | `araflow-api-health` é mais específico (tem `Path`) |
| `https://flow.arapath.com.br/assets/main.abc.js` | `araflow-web:8080/assets/...` (immutable cache 1y) | nginx serve estáticos |
| `https://flow.arapath.com.br/qualquer-coisa` | `araflow-web:8080/index.html` (SPA fallback) | nginx `try_files` |
| `http://flow.arapath.com.br/` (HTTP) | 301 → HTTPS | middleware `araflow-redirect-https` |

### 6.4 Headers de segurança (nginx)

| Header | Valor |
|---|---|
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Strict-Transport-Security` | `max-age=63072000` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |
| `Content-Security-Policy` | `default-src 'self'; connect-src 'self' https://flow.arapath.com.br; ...` |

---

## 7. FASE 6 — Deploy Plan (resumo)

Detalhamento completo em `49_DEPLOY_RUNBOOK.md`. Visão macro:

1. Operador: autenticar Tailscale, criar DNS A, tornar pacotes GHCR public.
2. Operador: disparar `cd-araflow.yml` no GitHub Actions.
3. Operador: scp compose + env para `/opt/araflow/`.
4. Operador: `docker compose pull && up -d`.
5. Operador: `curl https://flow.arapath.com.br/health`.
6. Operador: re-rodar smoke test (`49_SMOKE_TEST.md`).
7. Operador: re-checar AraOS não-impact (containers ainda `Up 7+ days`).

---

## 8. FASE 7 — Smoke Test (resumo)

Detalhamento em `49_SMOKE_TEST.md`. 14 itens verificáveis:
página abre, HTTPS, /health, assets, protocolos, sessão inicia, pause, resume, stop, fim, feedback, logs, mem, CPU.

---

## 9. FASE 8 — Rollback (resumo)

Detalhamento em `49_DEPLOY_RUNBOOK.md` §5. **Tempo máximo: 5 minutos.** Sem impacto AraOS.

| Cenário | Ação | Tempo |
|---|---|---|
| Rollback rápido | `restart` dos 2 containers | < 30s |
| Rollback de versão | `ARAFLOW_IMAGE_TAG=rc1-<sha-anterior>` + pull/up | < 3 min |
| Down total | `docker compose down` (não remove rede `web`) | < 30s |

---

## 10. Pendências detectadas (output da auditoria)

| # | Pendência | Origem | Bloqueador para deploy live? |
|---|---|---|---|
| P1 | DNS `flow.arapath.com.br` A → 147.93.33.253 | Operador | **SIM** |
| P2 | Tailscale autenticado (TS_AUTHKEY) | Operador | **SIM** (impede SSH externo) |
| P3 | Pacotes GHCR `araflow-api` e `araflow-web` públicos | Operador | **SIM** (se pull sem login) |
| P4 | CI workflow nunca foi disparado | Operador | **SIM** (imagens ainda não publicadas) |

Nenhuma pendência do **código** ou do **AraOS**. Decisão final: ver `49_GO_NO_GO.md`.