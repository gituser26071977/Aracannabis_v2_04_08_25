# AraFlow RC1 — Deployment Checklist

**Versão:** 1.0.0
**Data:** 2026-07-03

Use este checklist ANTES de cada deploy manual no VPS. Marque cada item como ✅/❌ e anexe ao report final.

---

## A. Pré-CI (código)

- [ ] Branch `main` (ou `rc1` cut) sem commits WIP.
- [ ] `mobile/package.json` contém `react-native-web`, `webpack`, `babel-loader`, `html-webpack-plugin` em devDeps.
- [ ] `backend/Dockerfile.araflow.api` e `backend/Dockerfile.araflow.web` presentes na raiz.
- [ ] `backend/nginx.araflow.conf` presente.
- [ ] `backend/scripts/araflow-api-entrypoint.sh` presente e executável (755).
- [ ] `docker-compose.araflow.yml` presente.
- [ ] `.env.araflow.example` presente (template).
- [ ] `.github/workflows/cd-araflow.yml` presente.

## B. Local — sanity build (opcional mas recomendado)

- [ ] `cd mobile && npm run build:web` → `mobile/web/dist/index.html` existe.
- [ ] `cd backend && npm test` → todos verdes.
- [ ] `docker build -f backend/Dockerfile.araflow.api -t araflow-api:test .` exit 0.
- [ ] `docker build -f backend/Dockerfile.araflow.web -t araflow-web:test .` exit 0.
- [ ] `docker compose -f docker-compose.araflow.yml --env-file .env.araflow.example config` exit 0.
- [ ] `docker run --rm araflow-api:test` + `wget -qO- http://127.0.0.1:5005/health` retorna JSON.

## C. AraOS non-impact gate (OBRIGATÓRIO)

- [ ] `docker compose -f docker-compose.prod.yml config > /tmp/araos-before.yml` exit 0.
- [ ] `docker compose -f docker-compose.prod.yml -f docker-compose.araflow.yml config > /tmp/araos-after.yml` exit 0.
- [ ] Diff de serviços AraOS: `diff` entre os dois configs para `siap-backend`, `siap-frontend`, `siap-db`, `siap-redis`, `siap-anonymization` retorna **vazio**.
- [ ] `grep -E "araflow-" /tmp/araos-before.yml` retorna **vazio** (zero vazamento em prod).
- [ ] `docker ps --format '{{.Names}}\t{{.Status}}' | grep siap-` mostra os 5 containers `siap-*` rodando há > 0 dias.

## D. CI (GitHub Actions)

- [ ] `cd-araflow.yml` é visível na aba Actions.
- [ ] Disparar `workflow_dispatch` (ou via UI).
- [ ] Job 1 (Lint) verde.
- [ ] Job 2 (Typecheck) verde.
- [ ] Job 3 (Test) verde.
- [ ] Job 4 (Build web bundle) verde — `mobile/web/dist/index.html` no artifact.
- [ ] Job 5 (Docker push) verde:
  - [ ] `ghcr.io/gituser26071977/araflow-api:rc1-<sha>` publicada.
  - [ ] `ghcr.io/gituser26071977/araflow-api:rc1-latest` atualizada.
  - [ ] `ghcr.io/gituser26071977/araflow-web:rc1-<sha>` publicada.
  - [ ] `ghcr.io/gituser26071977/araflow-web:rc1-latest` atualizada.

## E. Pacotes GHCR — visibilidade

- [ ] `araflow-api` package: **public** (Settings → Packages → Change visibility).
- [ ] `araflow-web` package: **public**.
- [ ] `docker pull ghcr.io/gituser26071977/araflow-api:rc1-latest` funciona sem login.

## F. VPS — pré-deploy

- [ ] Tailscale autenticado: `tailscale status` retorna host online.
- [ ] DNS: `dig +short flow.arapath.com.br` retorna `147.93.33.253`.
- [ ] Docker daemon saudável: `docker ps` responde.
- [ ] Rede `web` existe: `docker network ls | grep web`.
- [ ] Diretório `/opt/araflow` criado e pertencente ao usuário de deploy.
- [ ] `/opt/araflow/.env.araflow` populado (não commitar).
- [ ] `docker-compose.araflow.yml` copiado para `/opt/araflow/`.

## G. VPS — deploy

- [ ] `cd /opt/araflow && docker compose -f docker-compose.araflow.yml --env-file .env.araflow pull` exit 0.
- [ ] `docker compose -f docker-compose.araflow.yml --env-file .env.araflow up -d` exit 0.
- [ ] `docker compose -f docker-compose.araflow.yml --env-file .env.araflow ps` mostra `araflow-api` (healthy) e `araflow-web` (healthy).

## H. VPS — smoke público

- [ ] `curl -fsS https://flow.arapath.com.br/health | jq` retorna:
  - [ ] HTTP 200
  - [ ] `status: "ok"`
  - [ ] `version: "1.0.0"`
  - [ ] `commit` não-vazio
  - [ ] `build` não-vazio
  - [ ] `uptime` numérico
- [ ] `curl -fsSI https://flow.arapath.com.br/` retorna:
  - [ ] HTTP 200
  - [ ] `Strict-Transport-Security: max-age=63072000`
  - [ ] `X-Frame-Options: DENY`
  - [ ] `Content-Security-Policy` presente
- [ ] `curl -fsSI http://flow.arapath.com.br/` retorna 301/308 (redirect HTTPS).

## I. AraOS — não-impact verificado

- [ ] `curl -fsS https://api.visualsmartflow.com.br/api/health` ainda retorna 200.
- [ ] `docker ps --format '{{.Names}}\t{{.Status}}' | grep siap-` mostra os 5 containers sem restart (< 1 minuto de uptime > 0 dias anterior).
- [ ] Nenhum log de erro do Traefik sobre `siap-*` desde o deploy do araflow.

## J. Pós-deploy — comunicação

- [ ] Report RC1 (`48_DEPLOYMENT_REPORT.md`) atualizado com timestamp e SHA deployed.
- [ ] Canal #araflow-internal notificado com URL `https://flow.arapath.com.br`.

---

## Decisão Go/No-Go

**GO** se todos os itens A-G e H1, H2, H3, I1 estão ✅.

**NO-GO** se qualquer item da seção C (AraOS non-impact gate) falhar — investigar antes de prosseguir.

**NO-GO** se DNS não propagou ou Tailscale em NeedsLogin — sem acesso SSH externo, deploy manual é arriscado.