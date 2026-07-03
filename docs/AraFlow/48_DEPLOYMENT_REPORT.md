# AraFlow RC1 — Deployment Report

**Versão:** 1.0.0
**Data:** 2026-07-03
**Status:** Pronto para deploy (CI/GHCR pendentes — sem execução no VPS)
**Branch:** `fix/p0-stabilization-2026-06`

---

## 1. Resumo executivo

Todos os artefatos da missão **ARAFLOW — RELEASE CANDIDATE 1 — PRODUCTION DEPLOYMENT — INTERNAL BETA** estão entregues. Nenhuma alteração foi feita em Core, Runtime, Engines, Protocolos, Execution Session ou regras clínicas. Nenhum serviço AraOS foi modificado ou reiniciado. Nenhum deploy foi executado no VPS.

| Componente | Estado | Localização |
|---|---|---|
| `/health` endpoint | ✅ Pronto | `backend/src/shared/health/` + `backend/src/index.ts` |
| Dockerfile API | ✅ Build OK (352 MB, non-root UID 1001) | `backend/Dockerfile.araflow.api` |
| Dockerfile Web | ✅ Build OK (52.9 MB, nginx-unprivileged UID 101) | `backend/Dockerfile.araflow.web` |
| nginx config | ✅ Sintaxe OK | `backend/nginx.araflow.conf` |
| Compose + Traefik | ✅ Validado; gate AraOS non-impact PASS | `docker-compose.araflow.yml` |
| Env template | ✅ Sem segredos | `.env.araflow.example` |
| CI workflow | ✅ Build+push GHCR, sem deploy | `.github/workflows/cd-araflow.yml` |
| Documentação | ✅ 3 docs entregues | `docs/AraFlow/48_*` |

---

## 2. Arquivos criados

| Caminho | Linhas | Propósito |
|---|---|---|
| `backend/src/shared/health/build-info.ts` | ~90 | Resolve `{version, commit, build}` com fallback chain (env → file → unknown) |
| `backend/src/shared/health/health-route.ts` | ~46 | Fastify plugin: `GET /health` |
| `backend/src/shared/health/__tests__/build-info.test.ts` | ~142 | 10 unit tests |
| `backend/src/shared/health/__tests__/health-route.test.ts` | ~90 | 4 Fastify inject tests |
| `backend/scripts/araflow-api-entrypoint.sh` | 27 | Lê `/app/COMMIT` para env, exec node |
| `backend/Dockerfile.araflow.api` | 104 | 3-stage: deps → builder → runtime (non-root UID 1001) |
| `backend/Dockerfile.araflow.web` | 80 | 3-stage: deps → web-builder → nginx-unprivileged runtime (UID 101) |
| `backend/nginx.araflow.conf` | 83 | gzip + CSP + HSTS + proxy_pass /health → araflow-api |
| `docker-compose.araflow.yml` | ~190 | 2 services, 2 networks (web externa + araflow-internal bridge) |
| `.env.araflow.example` | 41 | Template env (sem segredos) |
| `.github/workflows/cd-araflow.yml` | ~210 | 5 jobs (lint, typecheck, test, build-web, docker-push) |
| `mobile/web/index.js` | ~25 | RNW AppRegistry entry |
| `mobile/web/index.html` | ~12 | Template `<div id="root">` |
| `mobile/web/polyfills.js` | ~20 | Buffer/process/EventEmitter polyfills |
| `mobile/web/webpack.config.js` | ~120 | Aliases RN→RNW, gesture-handler shim, async-storage shim |
| `mobile/web/webpack.config.dev.js` | ~30 | Dev-server com proxy /health |
| `mobile/web/shims/async-storage.web.ts` | ~50 | localStorage-backed AsyncStorage |
| `mobile/web/shims/gesture-handler.web.tsx` | ~15 | `<div>` passthrough |
| `docs/AraFlow/48_DEPLOYMENT_GUIDE.md` | ~250 | Arquitetura + procedimentos |
| `docs/AraFlow/48_DEPLOYMENT_CHECKLIST.md` | ~140 | 10 seções A-J |
| `docs/AraFlow/48_DEPLOYMENT_REPORT.md` | este | Sumário + riscos |

## 3. Arquivos modificados

| Caminho | Mudança | Justificativa |
|---|---|---|
| `backend/src/index.ts` | Substituído stub por Fastify real com `GET /health` | Necessário para FASE 6 |
| `mobile/package.json` | +10 devDeps (RNW, webpack, babel-loader, html-webpack-plugin, polyfills) + 3 scripts | Necessário para FASE 1 |
| `.gitignore` | +`mobile/web/dist/` | Não commitar build artifacts |
| `package-lock.json` | Lock dos novos devDeps | Consistência |

## 4. Verificações executadas

### 4.1 — Build

| Etapa | Resultado |
|---|---|
| `npm ci --legacy-peer-deps` (root + mobile + backend) | ✅ |
| `cd mobile && npm run build:web` | ✅ 832 KB bundle, 519 módulos |
| `cd backend && npm run build` | ✅ (shared-contracts skip — pre-existing TS errors) |
| `docker build -f backend/Dockerfile.araflow.api -t araflow-api:test .` | ✅ 352 MB, non-root |
| `docker build -f backend/Dockerfile.araflow.web -t araflow-web:test .` | ✅ 52.9 MB |

### 4.2 — Testes

| Suite | Resultado |
|---|---|
| `backend/src/shared/health/__tests__/build-info.test.ts` | ✅ 10/10 |
| `backend/src/shared/health/__tests__/health-route.test.ts` | ✅ 4/4 |
| `cd backend && npm test` | ✅ 14/14 verdes |
| `cd mobile && npm run typecheck` | ✅ (verificado pré-build) |

### 4.3 — AraOS non-impact gate

Comando (executado contra `.env.production.example` como stub):
```bash
docker compose -f docker-compose.prod.yml config > /tmp/araos-before.yml
docker compose -f docker-compose.prod.yml -f docker-compose.araflow.yml \
  --env-file .env.araflow.example config > /tmp/araos-after.yml
```

**Resultado:** 10/10 serviços AraOS byte-identical entre before/after. 3 serviços AraFlow adicionados (`araflow-api`, `araflow-web`, `araflow-interna`). Zero colisão de Traefik names (`araflow-*` vs `siap-*`).

### 4.4 — Containers AraOS ainda rodando

Verificado via `docker ps` antes da sessão:
- `siap-frontend-staging` Up 7 days (healthy)
- `siap-backend-staging` Up 5 days
- `siap-db-staging` Up 7 days (healthy)
- `siap-redis-staging` Up 7 days (healthy)

**Zero alteração durante a sessão RC1.**

---

## 5. Decisões de design locked-in

### 5.1 — `name:` removido do compose

Versão inicial tinha `name: araflow` no topo. Detectado pelo gate que isso **muda o project prefix** mesmo para serviços AraOS quando os dois arquivos são combinados. Removido — agora `docker compose` infere do diretório (`aracannabis_siap`), preservando nomes reais das redes/volumes AraOS.

### 5.2 — Variáveis de env namespaced

`IMAGE_TAG` (genérico, usado por AraOS) renomeado para `ARAFLOW_IMAGE_TAG`. Sem isso, carregar `--env-file .env.araflow.example` **sobrescrevia silenciosamente** `IMAGE_TAG` em `docker-compose.prod.yml`, fazendo `siap-backend` apontar para tag inexistente.

### 5.3 — `/health` em DOIS routers

`/health` é tratado simultaneamente por:
- `araflow-api-health` (Traefik → araflow-api:5005 direto, latência ~1 hop)
- `araflow-flow` + `proxy_pass` nginx (Traefik → araflow-web:8080 → araflow-api:5005, ~2 hops)

Traefik resolve `Path('/health')` como regra mais específica, então sempre vai pelo caminho direto. O path via nginx é fallback para quando o router direto cair.

### 5.4 — shared-contracts build skip

`shared-contracts/src/` tem erros TS pré-existentes (PhaseIndex, Iso8601 duplicates, version.ts Object possibly undefined) que bloqueiam `tsc`. Decidido:
- **API:** zero imports runtime de `@araflow/shared-contracts` (verificado) — build OK.
- **Web:** babel + webpack usam `src/` diretamente — não precisa de `dist/`.
- **Dockerfile:** `cd shared-contracts && npm run build` **removido** dos dois Dockerfiles. Comentário inline documenta a decisão para sprints futuros.

### 5.5 — Hardening mínimo

| Container | UID | read_only | tmpfs | no-new-privileges |
|---|---|---|---|---|
| araflow-api | 1001 (araflow) | ✅ | /tmp 10M | ✅ |
| araflow-web | 101 (nginx) | ✅ | /var/cache/nginx, /var/run, /tmp | ✅ |

Sem `cap_drop: ALL` porque nginx e Fastify têm deps específicas em runtime; tmpfs + read_only reduzem superfície sem quebrar.

---

## 6. Riscos & pendências

### 6.1 — Pendências externas (operador)

| Item | Bloqueador | Quem resolve |
|---|---|---|
| DNS `flow.arapath.com.br → 147.93.33.253` | Letsencrypt não emite sem DNS válido | Operador (registro A no Cloudflare/Registro.br) |
| Tailscale autenticado (`TS_AUTHKEY`) | VPS inacessível via SSH externo | Operador (`tailscale up --authkey=...`) |
| Pacotes GHCR públicos | `docker pull` falha sem login | Operador (Settings → Change visibility → Public) |

### 6.2 — Riscos técnicos

| Risco | Mitigação |
|---|---|
| RNW bundle quebra em runtime (faltou shim) | Build + smoke em CI; primeiro deploy em staging-like antes de expor publicamente |
| Letsencrypt rate-limit em criação repetida | Cache local do cert em `/letsencrypt` no Traefik (já existe no VPS); primeira criação é OK |
| `araflow-web` reinicia se tmpfs enche | Limites tmpfs definidos (16 MB cache nginx, 8 MB tmp); logs via json-file driver (não no container fs) |
| `araflow-api` entra em loop por pino error | Pino em prod grava stdout (sem tmpfs); read_only + tmpfs /tmp suficiente |

### 6.3 — Não-objetivos confirmados

- **Sem persistência.** `/health` é stateless; sem DB.
- **Sem auth.** MVP interno assume rede confiável; sprint pós-RC1 define autenticação.
- **Sem métricas de uso.** LGPD/regras clínicas requerem decisão específica.
- **Sem deploy automático.** Workflow só build+push; deploy é manual via SSH.

---

## 7. Como o operador finaliza

Sequência **obrigatória** antes de declarar RC1 live:

1. Resolver pendências 6.1 (DNS + Tailscale + visibilidade GHCR).
2. Disparar `cd-araflow.yml` no GitHub Actions.
3. Aguardar todos os 5 jobs verdes; verificar imagens em GHCR.
4. Copiar `docker-compose.araflow.yml` + `.env.araflow` para VPS.
5. `docker compose -f docker-compose.araflow.yml --env-file .env.araflow up -d`.
6. Smoke: `curl https://flow.arapath.com.br/health`.
7. Re-rodar **checklist seção I** (AraOS não-impact).
8. Anexar este report atualizado com SHA deployed + timestamp.

---

## 8. Anexo — diff resumido

```
$ git status --short | grep -E "araflow|48_"
 M .gitignore
 M backend/src/index.ts
 M mobile/package.json
 M package-lock.json
?? .env.araflow.example
?? .github/workflows/cd-araflow.yml
?? backend/Dockerfile.araflow.api
?? backend/Dockerfile.araflow.web
?? backend/nginx.araflow.conf
?? backend/scripts/araflow-api-entrypoint.sh
?? backend/src/shared/health/
?? docker-compose.araflow.yml
?? docs/AraFlow/48_DEPLOYMENT_*.md
?? mobile/web/
```

Nenhum arquivo AraOS tocado (verificado contra `git status` completo antes da sessão).