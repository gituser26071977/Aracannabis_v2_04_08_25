# AraFlow RC1 — Deployment Guide

**Versão:** 1.0.0
**Data:** 2026-07-03
**Domínio:** https://flow.arapath.com.br
**Stack:** 2 containers Docker isolados (araflow-api + araflow-web)
**CI:** `.github/workflows/cd-araflow.yml` (build + push GHCR; **sem deploy**)

---

## 1. Arquitetura

```
                          ┌─────────────────────────────────────────┐
                          │ VPS 147.93.33.253 (Hostinger)            │
                          │ Traefik v3 + docker-compose.prod.yml     │
                          │   rede externa: web                      │
                          └────────────────┬────────────────────────┘
                                           │
                                           │ TLS (letsencrypt)
                                           ▼
                          ┌─────────────────────────────────────────┐
                          │ flow.arapath.com.br                      │
                          │ routers Traefik: prefixo `araflow-*`     │
                          └────────────┬───────────────────┬────────┘
                                       │ /                  │ /health
                                       ▼                    ▼
                ┌──────────────────────────────┐  ┌──────────────────────────┐
                │ araflow-web                  │  │ araflow-api              │
                │ nginx-unprivileged 1.27      │  │ Fastify 4 / Node 20      │
                │ UID 101 / read-only + tmpfs  │  │ UID 1001 / read-only     │
                │ :8080 interno                │  │ :5005 interno            │
                │ serve mobile/web/dist        │  │ GET /health → JSON       │
                │ gzip + CSP + HSTS            │  │ env: GIT_COMMIT/BUILD    │
                └──────────────────────────────┘  └──────────────────────────┘
                                       │
                                       │ proxy_pass /health
                                       ▼
                            (rede interna araflow-internal)
```

**Características críticas:**

- **Isolamento AraOS:** AraFlow NÃO monta volumes AraOS, NÃO lê `.env.production`, NÃO inclui serviços AraOS. A única interface com AraOS é a rede externa `web` (criada por `docker-compose.prod.yml`).
- **Convenção de nomes Traefik:** todo router/service/middleware usa prefixo `araflow-*` (verificado por grep — zero colisão com `siap-*`).
- **Hardening:** ambos containers rodam com `read_only: true`, `no-new-privileges:true`, tmpfs para `/tmp`. API roda como UID 1001, web como UID 101.
- **Sem deploy automático:** o workflow `cd-araflow.yml` apenas constrói e publica imagens no GHCR. O operador dispara o deploy manualmente.

---

## 2. Pré-requisitos VPS

### 2.1 — Infraestrutura existente (verificada)

| Recurso | Estado | Comando de verificação |
|---|---|---|
| Docker 29+ | OK | `docker --version` |
| Compose v2.39+ | OK | `docker compose version` |
| Traefik v3 rodando | OK | `docker ps --filter "label=traefik.enable=true"` |
| Rede `web` externa | OK | `docker network ls \| grep -E "^.*\sweb\s"` |
| DNS A `flow.arapath.com.br → 147.93.33.253` | **pendente** | `dig +short flow.arapath.com.br` |
| Tailscale autenticado | **pendente** | `tailscale status` (atualmente `NeedsLogin`) |

### 2.2 — DNS (ação do operador)

Apontar `flow.arapath.com.br` (registro A) para `147.93.33.253`. Aguardar propagação (TTL recomendado: 300s). Letsencrypt no Traefik cuida do certificado automaticamente.

### 2.3 — Tailscale (ação do operador)

```bash
sudo tailscale up --authkey=tskey-auth-XXXXXXXXXXXX
```

Até esse passo, **não há como acessar o VPS via SSH externo** — usar o console de Hostinger.

---

## 3. Subir local (smoke test)

Útil para validar a build antes de promover para produção:

```bash
# 1. Build local
cd /path/to/Aracannabis_SIAP
docker build -f backend/Dockerfile.araflow.api -t araflow-api:test --build-arg GIT_COMMIT=local --build-arg BUILD_TIME=$(date -u +%Y-%m-%dT%H:%M:%S.000Z) .
docker build -f backend/Dockerfile.araflow.web -t araflow-web:test --build-arg GIT_COMMIT=local --build-arg BUILD_TIME=$(date -u +%Y-%m-%dT%H:%M:%S.000Z) .

# 2. Compose isolado
cp .env.araflow.example .env.araflow
docker compose -f docker-compose.araflow.yml --env-file .env.araflow up -d

# 3. Smoke
sleep 5
curl -s http://127.0.0.1:5005/health  # não funciona local — porta interna
docker exec araflow-api wget -qO- http://127.0.0.1:5005/health  # funciona
docker exec araflow-web wget -qO- http://127.0.0.1:8080/health   # proxied
```

> **Limitação local:** sem Traefik + rede `web`, os labels não têm efeito. O smoke é apenas **interno aos containers**.

---

## 4. Subir no VPS (produção)

### 4.1 — Disparar CI

```bash
# No GitHub:
gh workflow run cd-araflow.yml
# Ou via UI: Actions → CD — AraFlow RC1 → Run workflow
```

A CI vai:
1. Lint, typecheck, test (mobile + backend).
2. Build do bundle RNW (artefato de 7 dias).
3. Build + push de `ghcr.io/gituser26071977/araflow-api:rc1-<sha>` e `...:rc1-latest` (idem web).

### 4.2 — Preparar VPS

```bash
ssh deploy@147.93.33.253

sudo mkdir -p /opt/araflow
sudo chown deploy:deploy /opt/araflow

# Env file (NÃO commitar — gitignored)
cat > /opt/araflow/.env.araflow <<EOF
FLOW_DOMAIN=flow.arapath.com.br
ARAFLOW_API_IMAGE=ghcr.io/gituser26071977/araflow-api
ARAFLOW_WEB_IMAGE=ghcr.io/gituser26071977/araflow-web
ARAFLOW_IMAGE_TAG=rc1-latest
NODE_ENV=production
PORT=5005
LOG_LEVEL=info
GIT_COMMIT=unknown
BUILD_TIME=unknown
ARAFLOW_VERSION=1.0.0
RESTART_POLICY=unless-stopped
LOG_MAX_SIZE=10m
LOG_MAX_FILE=3
EOF

# Compose file (scp do repo)
# A partir da máquina local:
scp docker-compose.araflow.yml deploy@147.93.33.253:/opt/araflow/
```

### 4.3 — Subir

```bash
ssh deploy@147.93.33.253
cd /opt/araflow
docker compose -f docker-compose.araflow.yml --env-file .env.araflow pull
docker compose -f docker-compose.araflow.yml --env-file .env.araflow up -d
docker compose -f docker-compose.araflow.yml --env-file .env.araflow ps
```

### 4.4 — Smoke público

```bash
curl -fsS https://flow.arapath.com.br/health | jq
# Esperado:
# {
#   "status": "ok",
#   "version": "1.0.0",
#   "commit": "<sha>",
#   "build": "2026-07-03T...",
#   "uptime": 12.34
# }

curl -fsSI https://flow.arapath.com.br/ | head -10
# Esperado: 200, Strict-Transport-Security, X-Frame-Options DENY, etc.
```

---

## 5. Rollback

### 5.1 — Rollback rápido (mesma imagem)

```bash
ssh deploy@147.93.33.253
cd /opt/araflow
docker compose -f docker-compose.araflow.yml --env-file .env.araflow restart
```

### 5.2 — Rollback de versão

```bash
# 1. Listar tags disponíveis no GHCR
docker manifest inspect ghcr.io/gituser26071977/araflow-api:rc1-abc12345

# 2. Editar env
sed -i 's/^ARAFLOW_IMAGE_TAG=.*/ARAFLOW_IMAGE_TAG=rc1-abc12345/' /opt/araflow/.env.araflow

# 3. Re-deploy
cd /opt/araflow
docker compose -f docker-compose.araflow.yml --env-file .env.araflow pull
docker compose -f docker-compose.araflow.yml --env-file .env.araflow up -d
```

### 5.3 — Down total

```bash
cd /opt/araflow
docker compose -f docker-compose.araflow.yml --env-file .env.araflow down
# NÃO remove a rede `web` (externa, pertence ao AraOS).
```

---

## 6. Troubleshooting

| Sintoma | Causa provável | Ação |
|---|---|---|
| `curl https://flow.arapath.com.br/health` → 404 | DNS não propagado ou Traefik não enxergou o container | `dig +short flow.arapath.com.br`; `docker network inspect web \| grep araflow` |
| `/health` 502 | nginx não resolve `araflow-api` | `docker exec araflow-web wget -qO- http://araflow-api:5005/health` (teste interno); checar `docker network inspect araflow-internal` |
| `/health` retorna 200 mas sem `commit`/`build` | Env vars GIT_COMMIT/BUILD_TIME não chegaram | Re-rodar CI com `--build-arg` populados; ou setar no `.env.araflow` |
| `docker compose pull` falha com `denied` | GHCR image privada | Tornar o pacote GHCR **public** (Settings → Packages → araflow-api/araflow-web → Change visibility) ou autenticar `docker login ghcr.io` no VPS |
| `permission denied` ao subir compose | `deploy` user não está no grupo `docker` | `sudo usermod -aG docker deploy && newgrp docker` |
| Traefik emite certificado mas navegador rejeita | DNS aponta para IP errado | Confirmar `dig +short flow.arapath.com.br` retorna `147.93.33.253` |
| `araflow-api` reinicia em loop | `read_only: true` + log write em `/tmp` falha | `docker logs araflow-api` — verificar erro de EROFS; tmpfs `/tmp:10m` está configurado |
| Bundle RNW não renderiza | Build rodou em dev mode | Confirmar que CI rodou job 4 com `npm run build:web` (production); checar `mobile/web/dist/assets/*.js` é minificado |

---

## 7. Observabilidade

- **Health endpoint:** `GET https://flow.arapath.com.br/health` retorna JSON com `version`, `commit`, `build`, `uptime`.
- **Logs:** `docker logs araflow-api` e `docker logs araflow-web` (json-file driver, max 10 MB × 3 arquivos).
- **Traefik dashboard:** acesso via Tailscale (URL e credenciais definidas em `docker-compose.prod.yml` do AraOS).

---

## 8. Limites e não-objetivos

- **Não há persistência.** O `/health` é stateless — nenhuma rota de DB.
- **Não há autenticação.** MVP é beta interno; produção com auth fica para sprint pós-RC1.
- **Não há analytics.** Coleta de métricas de uso requer decisão clínica/LGPD.
- **Não há backup.** Sem estado = sem backup.

---

## 9. Próximos passos (fora do escopo RC1)

1. Sprint 12+ — autenticação (escopo a definir com produto).
2. Sprint 12+ — analytics opt-in.
3. Sprint 13+ — segundo domínio (`flow-staging.arapath.com.br`) para validação antes de mudanças em regras clínicas.
4. Migração do bundle para SSR ou framework nativo web se performance for insuficiente.