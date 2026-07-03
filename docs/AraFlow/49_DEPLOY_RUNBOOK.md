# AraFlow RC1.1 — Deploy Runbook

**Versão:** 1.0.0
**Data:** 2026-07-03
**Audiência:** operador executando o primeiro deploy manual.
**Restrição absoluta:** zero alteração em AraOS; zero impacto em containers `siap-*`.

---

## Convenções usadas neste documento

Cada passo é numerado e contém:
- **Comando** — exatamente o que digitar.
- **Resultado esperado** — como saber que deu certo.
- **Como validar** — verificação adicional (opcional mas recomendada).
- **Como desfazer** — comando de rollback do passo (não do deploy inteiro — ver §5).

---

## 0. Pré-condições (antes de iniciar)

O operador precisa de:

- [ ] Acesso SSH ao VPS via Tailscale (ver `49_PRE_DEPLOY_AUDIT.md` §3.12).
- [ ] Permissão para criar registros DNS no provedor de `arapath.com.br`.
- [ ] Acesso ao GitHub (owner `gituser26071977` ou colaborador com permissão `packages: write`).
- [ ] Senha/conta Cloudflare (se a zona `arapath.com.br` estiver lá) — para setar `Proxy: off`.

---

## 1. Deploy Plan — passo a passo

### Passo 1 — Tailscale up

**Comando:**
```bash
sudo tailscale up --authkey=tskey-auth-XXXXXXXXXXXX
```

**Resultado esperado:**
```
Success.
```

**Como validar:**
```bash
tailscale status
# Esperado: hostname do VPS aparece como "online" (não NeedsLogin)
tailscale ping <seu-ip-local>
# Esperado: pong em < 100ms
```

**Como desfazer:**
```bash
sudo tailscale down
# Não impacta VPS, apenas desconecta do tailnet.
```

---

### Passo 2 — DNS A record

**Comando (Cloudflare, se for o provedor):**
```bash
# Via UI: DNS → Records → Add record
#   Type: A
#   Name: flow
#   IPv4: 147.93.33.253
#   Proxy: OFF (DNS only)
#   TTL: Auto (300s)
```

**Resultado esperado:** registro aparece na lista, proxy cloud cinza (não laranja).

**Como validar:**
```bash
dig +short flow.arapath.com.br A
# Esperado: 147.93.33.253
dig +trace flow.arapath.com.br A | tail -5
# Esperado: chain termina em 147.93.33.253
```

**Como desfazer:** deletar o registro A. Não há efeito colateral.

---

### Passo 3 — Pacotes GHCR públicos

**Comando (UI GitHub):**
1. `https://github.com/gituser26071977?tab=packages` (ou Organization equivalente).
2. Clicar em `araflow-api` → `Package settings` → `Danger Zone` → `Change visibility` → `Public` → confirmar.
3. Repetir para `araflow-web`.

**Resultado esperado:** badge "Public" visível na página do package.

**Como validar:**
```bash
# De uma máquina qualquer (ou do próprio VPS após login):
curl -fsSI https://ghcr.io/v2/gituser26071977/araflow-api/manifests/rc1-latest \
  -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
  | head -1
# Se rc1-latest ainda não foi publicada, retornar 404 (esperado nesta fase).
# Se 200/401, o package existe e é público (auth requerida seria 401; 404 = privado OU não existe).
```

**Como desfazer:** reverter para `Private` (Settings → Change visibility → Private).

> **Por que public?** O VPS não tem credencial GHCR persistente. Manter public simplifica drasticamente. Risco: download-only access (sem push, sem delete).

---

### Passo 4 — Disparar CI

**Comando (UI GitHub):**
1. Repo → Actions → `CD — AraFlow RC1 (build + push GHCR, no deploy)`.
2. `Run workflow` → branch `main` (ou `fix/p0-stabilization-2026-06`) → `Run workflow`.

**Comando (CLI):**
```bash
gh workflow run cd-araflow.yml --ref main
```

**Resultado esperado:** 5 jobs rodam sequencialmente (lint → typecheck → test → build-web → docker-push).

**Como validar:**
- UI: cada job vira ✅ verde em < 25 min total.
- CLI: `gh run watch` (Ctrl-C para sair do watch).
- Após 5/5 verde, conferir imagens:
  ```bash
  # De uma máquina com docker:
  docker pull ghcr.io/gituser26071977/araflow-api:rc1-latest
  docker pull ghcr.io/gituser26071977/araflow-web:rc1-latest
  # Esperado: ambos baixam sem erro
  ```

**Como desfazer:** N/A (CI não tem efeito colateral; pode rerun sem medo).

---

### Passo 5 — SSH no VPS e preparar /opt/araflow

**Comando:**
```bash
ssh deploy@147.93.33.253    # via Tailscale
sudo mkdir -p /opt/araflow
sudo chown deploy:deploy /opt/araflow
```

**Resultado esperado:** diretório criado, ownership `deploy:deploy`.

**Como validar:**
```bash
ls -ld /opt/araflow
# Esperado: drwxr-xr-x deploy deploy /opt/araflow
```

**Como desfazer:**
```bash
sudo rm -rf /opt/araflow
# Não há side-effect (diretório vazio).
```

---

### Passo 6 — Copiar docker-compose.araflow.yml para VPS

**Comando (máquina local → VPS):**
```bash
scp docker-compose.araflow.yml deploy@147.93.33.253:/opt/araflow/
```

**Resultado esperado:** arquivo transferido, `100%` no final do scp.

**Como validar:**
```bash
ssh deploy@147.93.33.253 "head -3 /opt/araflow/docker-compose.araflow.yml"
# Esperado: linhas de comentário iniciadas com #
```

**Como desfazer:**
```bash
ssh deploy@147.93.33.253 "rm /opt/araflow/docker-compose.araflow.yml"
```

---

### Passo 7 — Criar .env.araflow no VPS

**Comando (no VPS):**
```bash
ssh deploy@147.93.33.253
cat > /opt/araflow/.env.araflow <<'EOF'
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
chmod 600 /opt/araflow/.env.araflow
```

**Resultado esperado:** arquivo criado, perms 600.

**Como validar:**
```bash
ls -la /opt/araflow/.env.araflow
# Esperado: -rw------- deploy deploy
cat /opt/araflow/.env.araflow | head -5
# Esperado: 5 linhas começando com FLOW_DOMAIN=, ARAFLOW_API_IMAGE=, etc.
```

**Como desfazer:**
```bash
rm /opt/araflow/.env.araflow
```

---

### Passo 8 — Validar compose antes de subir (DRY RUN)

**Comando (no VPS):**
```bash
cd /opt/araflow
docker compose -f docker-compose.araflow.yml --env-file .env.araflow config
```

**Resultado esperado:** YAML completo impresso, **0 erros**.

**Como validar:**
- 2 services: `araflow-api`, `araflow-web`.
- 1 network nova: `araflow-internal`.
- 1 network externa: `web`.
- Imagens: `ghcr.io/gituser26071977/araflow-{api,web}:rc1-latest`.
- Labels Traefik: 6 (3 routers, 2 services, 1 middleware).

**Como desfazer:** não há (config é read-only).

---

### Passo 9 — Pull das imagens

**Comando:**
```bash
cd /opt/araflow
docker compose -f docker-compose.araflow.yml --env-file .env.araflow pull
```

**Resultado esperado:**
```
✔ araflow-api Pulled
✔ araflow-web Pulled
```

**Como validar:**
```bash
docker images | grep araflow
# Esperado:
# ghcr.io/gituser26071977/araflow-api    rc1-latest    <id>    2 min ago    352MB
# ghcr.io/gituser26071977/araflow-web    rc1-latest    <id>    2 min ago    53MB
```

**Como desfazer:** as imagens ficam em cache; para limpar:
```bash
docker rmi ghcr.io/gituser26071977/araflow-api:rc1-latest
docker rmi ghcr.io/gituser26071977/araflow-web:rc1-latest
```

---

### Passo 10 — Up dos containers

**Comando:**
```bash
cd /opt/araflow
docker compose -f docker-compose.araflow.yml --env-file .env.araflow up -d
```

**Resultado esperado:**
```
✔ Network araflow-internal   Created
✔ Container araflow-api      Started
✔ Container araflow-web      Started
```

**Como validar:**
```bash
docker compose -f docker-compose.araflow.yml --env-file .env.araflow ps
# Esperado:
# NAME                STATUS              PORTS
# araflow-api         Up X seconds (healthy)
# araflow-web         Up X seconds (healthy)
```

**Como desfazer (down sem remover imagens):**
```bash
docker compose -f docker-compose.araflow.yml --env-file .env.araflow down
# NÃO remove a rede `web` (externa) nem imagens.
```

---

### Passo 11 — Smoke /health (interno)

**Comando (no VPS):**
```bash
# Direto da API
docker exec araflow-api wget -qO- http://127.0.0.1:5005/health
# Esperado: {"status":"ok","version":"1.0.0","commit":"<sha>","build":"...","uptime":...}

# Via nginx (proxy)
docker exec araflow-web wget -qO- http://127.0.0.1:8080/health
# Esperado: mesmo JSON
```

**Como validar:** JSON parseável, todos os campos preenchidos.

**Como desfazer:** se /health falhar, ir para §5 (rollback).

---

### Passo 12 — Verificar AraOS não-impact (gate)

**Comando (no VPS):**
```bash
docker ps --format '{{.Names}}\t{{.Status}}' \
  | grep -E "^(siap-backend|siap-frontend|siap-db|siap-redis|siap-anonymization)"
```

**Resultado esperado:** os 5 containers `siap-*` com uptime **inalterado** (Up X days, mesmo X de antes do deploy).

**Como validar:**
```bash
# API AraOS ainda responde?
curl -fsS https://api.visualsmartflow.com.br/api/health -o /dev/null -w "%{http_code}\n"
# Esperado: 200
```

**Como desfazer:** se algo em AraOS quebrar (improvável — verificamos gate em CI), executar rollback AraFlow e investigar logs:
```bash
docker logs --since 5m $(docker ps -q -f name=araflow-)
```

---

### Passo 13 — Smoke público (HTTPS)

**Comando (de qualquer máquina):**
```bash
curl -fsS https://flow.arapath.com.br/health | python3 -m json.tool
```

**Resultado esperado:**
```json
{
    "status": "ok",
    "version": "1.0.0",
    "commit": "<sha>",
    "build": "2026-07-03T...",
    "uptime": 12.34
}
```

**Como validar:**
```bash
# HTTP redireciona para HTTPS
curl -fsSI http://flow.arapath.com.br/ | head -3
# Esperado: HTTP/1.1 301 ... Location: https://...

# Headers de segurança
curl -fsSI https://flow.arapath.com.br/ | grep -iE "strict-transport|x-frame|content-security"
# Esperado: 3 linhas, todos com valores definidos em nginx.araflow.conf

# Assets imutáveis
curl -fsSI https://flow.arapath.com.br/assets/main.8c0b2006.js | head -3
# Esperado: HTTP/1.1 200, Cache-Control: public, immutable
```

**Como desfazer:** se algo falhar, ir para §5.

---

### Passo 14 — Smoke aplicação (RNW)

**Comando (de qualquer máquina):**
```bash
# Página inicial
curl -fsS https://flow.arapath.com.br/ | grep -E "id=\"root\"|<title>"
# Esperado: <div id="root"></div>, <title>AraFlow</title> (ou similar)

# Asset bundle existe e tem content hash
curl -fsSI https://flow.arapath.com.br/assets/main.8c0b2006.js | head -1
# Esperado: 200
```

**Como validar manualmente (browser):**
1. Abrir `https://flow.arapath.com.br/` em janela anônima.
2. Selecionar um protocolo (Diaphragmatic, Box 4-4-4-4, ou Physiological Sigh).
3. Iniciar sessão → verificar animação de respiração.
4. Pause / Resume / Stop.
5. Submeter feedback.
6. Recarregar → feedback deve persistir (AsyncStorage → localStorage).

Detalhamento completo em `49_SMOKE_TEST.md`.

---

### Passo 15 — Anotar SHA deployed

**Comando (no VPS):**
```bash
echo "Deployed $(date -u +%Y-%m-%dT%H:%M:%SZ) — AraFlow RC1" >> /opt/araflow/deployment.log
cat /opt/araflow/deployment.log
```

**Resultado esperado:** log incrementa com timestamp.

**Como validar:** `cat` mostra histórico.

---

## 2. Sequência de validação pós-deploy (resumido)

| # | Verificação | Comando | Esperado |
|---|---|---|---|
| 1 | API interna healthy | `docker exec araflow-api wget -qO- http://127.0.0.1:5005/health` | JSON com status:ok |
| 2 | Web interna proxy | `docker exec araflow-web wget -qO- http://127.0.0.1:8080/health` | Mesmo JSON |
| 3 | AraOS intacto | `docker ps` filtrado por `siap-*` | 5 containers, mesmos uptimes |
| 4 | HTTPS /health | `curl https://flow.arapath.com.br/health` | JSON com status:ok |
| 5 | HTTP→HTTPS | `curl -I http://flow.arapath.com.br/` | 301/308 → https |
| 6 | Página raiz | `curl -fsS https://flow.arapath.com.br/` | HTML com `<div id="root">` |
| 7 | Assets cache | `curl -I .../assets/main.*.js` | 200, immutable |
| 8 | Headers security | grep 3 headers | Todos presentes |
| 9 | Browser manual | Abrir URL | UI carrega, protocolos visíveis |

---

## 3. Comandos diários de saúde

```bash
# Status geral
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' \
  | grep -E "(siap-|araflow-|traefik)"

# Logs API/web últimas 1h
docker logs --since 1h araflow-api 2>&1 | tail -50
docker logs --since 1h araflow-web 2>&1 | tail -50

# Uptime
docker inspect --format='{{.State.StartedAt}} uptime={{.State.StartedAt}}' araflow-api araflow-web

# Memória
docker stats --no-stream araflow-api araflow-web
```

---

## 4. Atualização para nova versão (rolling update)

```bash
# No CI, após mudança no código, rodar cd-araflow.yml — push rc1-<novo-sha>.
# No VPS:
ssh deploy@147.93.33.253
cd /opt/araflow

# Pin nova tag (em vez de rc1-latest, use rc1-<sha> para rollback determinístico)
sed -i 's/^ARAFLOW_IMAGE_TAG=.*/ARAFLOW_IMAGE_TAG=rc1-<novo-sha>/' .env.araflow

docker compose -f docker-compose.araflow.yml --env-file .env.araflow pull
docker compose -f docker-compose.araflow.yml --env-file .env.araflow up -d
docker compose -f docker-compose.araflow.yml --env-file .env.araflow ps

# Validar
curl -fsS https://flow.arapath.com.br/health | jq
# commit deve refletir <novo-sha>
```

---

## 5. Rollback (≤ 5 min, zero impacto AraOS)

### 5.1 — Rollback rápido (mesma imagem, restart)

**Quando usar:** crash imediato após deploy, healthcheck falhando, etc.

**Comando (no VPS):**
```bash
cd /opt/araflow
docker compose -f docker-compose.araflow.yml --env-file .env.araflow restart
```

**Tempo:** < 30s.

**Como validar:** `docker ps` mostra araflow-api/web com `Up X seconds (healthy)`.

---

### 5.2 — Rollback de versão (imagem anterior)

**Quando usar:** bug detectado após alguns minutos, precisa de imagem anterior.

**Comando (no VPS):**
```bash
cd /opt/araflow

# 1. Identificar SHA anterior (do log ou do GHCR)
docker compose -f docker-compose.araflow.yml --env-file .env.araflow down

# 2. Pin SHA anterior
sed -i 's/^ARAFLOW_IMAGE_TAG=.*/ARAFLOW_IMAGE_TAG=rc1-<sha-anterior>/' .env.araflow

# 3. Pull + up
docker compose -f docker-compose.araflow.yml --env-file .env.araflow pull
docker compose -f docker-compose.araflow.yml --env-file .env.araflow up -d
```

**Tempo:** < 3 min (depende da banda para re-pull).

**Como validar:** `curl https://flow.arapath.com.br/health` retorna `commit: <sha-anterior>`.

---

### 5.3 — Down total (kill switch)

**Quando usar:** deploy causando problemas sistêmicos, precisa de zero exposição.

**Comando (no VPS):**
```bash
cd /opt/araflow
docker compose -f docker-compose.araflow.yml --env-file .env.araflow down
```

**Resultado:** containers parados e removidos. **Rede `web` permanece** (é externa, pertence ao AraOS — não tocamos).

**Como validar:**
```bash
docker ps -a | grep araflow
# Esperado: nada (containers removidos)
curl -fsS https://flow.arapath.com.br/health
# Esperado: 404 (Traefik não tem router ativo, OU Traefik retorna connection refused se labels foram limpas via rede)
```

> **Nota sobre Traefik:** enquanto o container está vivo, Traefik vê as labels. Quando o container é destruído, Traefik perde o backend do LB. O router continua configurado, mas aponta para backend inexistente → 502/504. Isso é OK — significa "fora do ar", não "quebrou AraOS".

**Para re-subir:**
```bash
docker compose -f docker-compose.araflow.yml --env-file .env.araflow up -d
# Ou com versão específica (5.2).
```

---

### 5.4 — Limpeza completa (cenário extremo, pós-rollback)

**Quando usar:** após investigação, decidido abandonar o deploy atual.

**Comando (no VPS):**
```bash
cd /opt/araflow
docker compose -f docker-compose.araflow.yml --env-file .env.araflow down --rmi all
# Remove containers + imagens. NÃO remove rede `web`.
```

**Como desfazer:** re-pull e re-up (passos 9-10).

---

## 6. Checklist pós-rollback

Independente do cenário:

- [ ] AraOS ainda intacto: `docker ps` mostra 5 containers `siap-*` rodando.
- [ ] `curl https://api.visualsmartflow.com.br/api/health` retorna 200.
- [ ] Logs Traefik não mostram erros novos relacionados a `araflow-*` (após restart/down).
- [ ] `docker network ls | grep web` ainda mostra a rede.
- [ ] Sem containers araflow órfãos: `docker ps -a | grep araflow` vazio (ou apenas healthy se restart).

---

## 7. Comandos de emergência (1-liners)

```bash
# Status compacto
alias ast='docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(siap-|araflow-|traefik)"'

# Logs últimos 5 min API
docker logs --since 5m araflow-api 2>&1 | tail -30

# Restart imediato
cd /opt/araflow && docker compose -f docker-compose.araflow.yml --env-file .env.araflow restart

# Down de emergência
cd /opt/araflow && docker compose -f docker-compose.araflow.yml --env-file .env.araflow down

# Rollback para SHA anterior conhecido
cd /opt/araflow && sed -i 's/^ARAFLOW_IMAGE_TAG=.*/ARAFLOW_IMAGE_TAG=rc1-<sha>/' .env.araflow \
  && docker compose -f docker-compose.araflow.yml --env-file .env.araflow pull \
  && docker compose -f docker-compose.araflow.yml --env-file .env.araflow up -d
```