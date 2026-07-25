# SSH_DEPLOY_CHECKLIST — AraOS SIAP RC1

**Versão:** 2.0 (2026-06-28)
**Origem:** M36 — Operator Handoff Package
**Hardening:** M37 — Operator Package Hardening (pre-deploy)
**Audiência:** Operador executor do deploy (1 pessoa com SSH ao VPS)
**Duração:** ~35 minutos (janela de 60 min reservada)
**Pré-requisito:** `docs/OPERATOR_RUNBOOK.md` lido integralmente

---

## Instruções de uso

- Marque cada item conforme executa: `[ ]` → `[x]`
- Se um item FALHAR: **PARE** no item que falhou, registre evidência, decida ABORT/CONTINUE com base em `OPERATOR_RUNBOOK.md` §6
- Não pule itens
- Não invente atalhos
- Cada comando tem **Resultado esperado** — se diferente, ABORTAR
- Todos os comandos deste documento usam as **Variáveis Operacionais** abaixo

---

## Variáveis Operacionais

> **Defina estas variáveis UMA VEZ no início do deploy.** Todos os comandos abaixo assumem que elas já estão exportadas no shell atual do operador.
>
> Copie o bloco abaixo **inteiro** e cole no seu terminal antes de começar:

```bash
# ── Identidade ──
export VPS_HOST="147.93.33.253"
export VPS_USER="root"
export SSH_KEY="$HOME/.ssh/id_ed25519"
export SSH_TARGET="${VPS_USER}@${VPS_HOST}"
export SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:?defina a URL do webhook Slack}"

# ── Diretórios ──
export PROJECT_DIR="/root/projetos/araos"
export BACKUP_DIR="/var/backups/siap"
export LOG_DIR="/var/log/siap"

# ── Docker / Compose ──
export COMPOSE_FILE="docker-compose.prod.yml"
export COMPOSE_BASE="docker compose -f ${PROJECT_DIR}/${COMPOSE_FILE}"

# ── Containers (com descoberta dinâmica opcional) ──
# Estático (fallback):
export BACKEND_CONTAINER="siap-backend"
export FRONTEND_CONTAINER="siap-frontend"
export DB_CONTAINER="siap-db"
export REDIS_CONTAINER="siap-redis"
# Dinâmico (recomendado — execute uma vez para descobrir):
# export DB_CONTAINER=$(ssh $SSH_TARGET "docker ps --filter 'name=siap-db' --format '{{.Names}}' | head -1")

# ── Banco de dados ──
export DB_NAME="aracannabis"
export DB_USER="siap_user"

# ── URLs externas ──
export HEALTH_URL="https://api.visualsmartflow.com.br/api/health"
export SCHEMA_URL="https://api.visualsmartflow.com.br/api/schema-version"

# ── Release / Git ──
export TAG_NAME="v1.0.0-rc.1"
export RC1_HEAD="REDACTED"
export RC1_BRANCH="fix/p0-stabilization-2026-06"
export GITHUB_REPO="gituser26071977/Aracannabis_v2_04_08_25"

# ── Helpers (SSH wrapper + Docker wrapper) ──
ssh_vps() { ssh -i "$SSH_KEY" "$SSH_TARGET" "$@"; }
```

**Validação imediata das variáveis:**

```bash
echo "VPS: $SSH_TARGET | DB: $DB_CONTAINER | Tag: $TAG_NAME"
```

**Esperado:** `VPS: root@147.93.33.253 | DB: siap-db | Tag: v1.0.0-rc.1`.

---

## FASE 0 — Setup terminal (5 min)

### 0.1 [ ] Exportar variáveis operacionais

```bash
# (colar aqui o bloco de Variáveis Operacionais acima)
```

**Esperado:** sem erros de export.

---

### 0.2 [ ] Abrir terminal limpo

```bash
clear
date '+%Y-%m-%d %H:%M:%S %Z'
```

**Esperado:** data/hora atual exibida.

---

### 0.3 [ ] Validar ferramentas locais

```bash
ssh -V && psql --version && docker --version && docker compose version && curl --version | head -1 && git --version
```

**Esperado:** 6 linhas, todas com versões >= requisitos do runbook §1.1.

**Falha:** instalar ou trocar de máquina.

---

### 0.4 [ ] Conectar ao VPS

```bash
ssh_vps "hostname && uptime && whoami"
```

**Esperado:**
```
aracannabis
up N days, ...
root
```

**Falha:** chave errada, hostname errado, VPS offline → ABORTAR.

---

### 0.5 [ ] Validar Docker daemon remoto

```bash
ssh_vps "docker ps --filter 'name=siap' --format 'table {{.Names}}\t{{.Status}}'"
```

**Esperado (antes do deploy):**
```
NAME                STATUS
siap-db             Up ...
siap-backend        Up ...
siap-frontend       Up ...
siap-redis          Up ...
```

**Falha:** containers não rodando, `Exited`, ou faltando → ABORTAR.

---

## FASE 0.5 — Pre-flight check (OBRIGATÓRIO, 2 min)

> **Execute ANTES de começar o deploy.** Se QUALQUER item falhar: ABORTAR imediatamente.

### 0.5.1 [ ] Ferramentas locais

```bash
command -v ssh && command -v git && command -v docker && command -v curl && command -v psql && docker compose version >/dev/null 2>&1
```

**Esperado:** exit code 0.

---

### 0.5.2 [ ] Memória livre >= 1 GB

```bash
free -g | awk '/^Mem:/ { if ($4+0 < 1) { print "FAIL"; exit 1 } else { print "OK:", $4"GB free" } }'
```

**Esperado:** `OK: NGB free` com N >= 1.

---

### 0.5.3 [ ] Espaço em disco >= 5 GB livres

```bash
df -BG "${PROJECT_DIR}" "${BACKUP_DIR}" "${LOG_DIR}" 2>/dev/null | awk 'NR>1 { gsub("G",""); if ($4+0 < 5) { print "FAIL:", $6" tem só "$4"G"; exit 1 } } END { print "OK" }'
```

**Esperado:** `OK`.

---

### 0.5.4 [ ] Containers ativos detectados

```bash
ssh_vps "docker ps --filter 'name=siap' --format '{{.Names}}' | wc -l"
```

**Esperado:** valor >= 3 (db, backend, frontend, redis).

---

### 0.5.5 [ ] Acesso ao banco (SELECT 1)

```bash
ssh_vps "docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c 'SELECT 1 AS ok;'"
```

**Esperado:** linha com `1 | ok`.

**Se falhar:** contêiner DB nome pode ter mudado. Execute descoberta:
```bash
ssh_vps "docker ps --filter 'name=siap-db' --format '{{.Names}}' | head -1"
```
Atualize `DB_CONTAINER` com o nome real.

---

### 0.5.6 [ ] Diretório de backup existe e é gravável

```bash
ssh_vps "test -d ${BACKUP_DIR} && test -w ${BACKUP_DIR} && echo OK || (echo 'FAIL: criando'; sudo mkdir -p ${BACKUP_DIR} && sudo chown ${VPS_USER}:${VPS_USER} ${BACKUP_DIR})"
```

**Esperado:** `OK`.

---

### 0.5.7 [ ] Diretório de logs existe

```bash
ssh_vps "test -d ${LOG_DIR} || mkdir -p ${LOG_DIR}"
```

**Esperado:** diretório criado se não existia.

---

### 0.5.8 [ ] Permissões sudo sem senha (para rollback emergencial)

```bash
ssh_vps "sudo -n true && echo 'OK: passwordless sudo' || echo 'FAIL: precisa de senha'"
```

**Esperado:** `OK: passwordless sudo`.

**Se FAIL:** operador precisa estar com senha; ou rollback pode falhar.

---

### 0.5.9 [ ] Webhook Slack válido

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$SLACK_WEBHOOK_URL" -H "Content-Type: application/json" -d '{"text":"[pre-flight] AraOS SIAP RC1 deploy pre-flight OK"}'
```

**Esperado:** `200`.

---

### 0.5.10 [ ] Pre-flight summary

```bash
echo "Pre-flight completo em $(date). Continuar? (s/N)"
```

**Esperado:** operador digita `s` para continuar.

**Se QUALQUER item falhou:** ABORTAR (não prossiga para FASE 1).

---

## FASE 1 — Backup pré-deploy (5 min)

### 1.1 [ ] Validar diretório de backup

```bash
ssh_vps "ls -ld ${BACKUP_DIR}"
```

**Esperado:** `drwxr-xr-x 2 ... siap` (diretório existe).

**Falha:** `No such file or directory` → `ssh_vps "sudo mkdir -p ${BACKUP_DIR} && sudo chown ${VPS_USER}:${VPS_USER} ${BACKUP_DIR}"`. Se falhar: ABORTAR.

---

### 1.2 [ ] Executar backup

```bash
ssh_vps "cd ${PROJECT_DIR} && ./scripts/backup.sh --env=production 2>&1 | tee ${LOG_DIR}/backup_pre_deploy.log"
```

**Esperado:**
```
START: ...
pg_dump: writing ...
END: ...
SUCCESS: ${BACKUP_DIR}/aracannabis_<timestamp>.sql.gz
```

**Falha:** qualquer erro → ABORTAR.

---

### 1.3 [ ] Validar tamanho do backup

```bash
ssh_vps "ls -lah ${BACKUP_DIR}/ | tail -5 && du -sh ${BACKUP_DIR}/aracannabis_*.sql.gz | tail -1"
```

**Esperado:** arquivo `aracannabis_<timestamp>.sql.gz` com tamanho > 0 bytes **e consistente com último backup** (compare com `du -sh` de um backup anterior conhecido).

**Falha:** arquivo 0 bytes ou ausente → ABORTAR.

---

### 1.4 [ ] Anotar nome do backup

```bash
export BACKUP_FILE=$(ssh_vps "ls -t ${BACKUP_DIR}/aracannabis_*.sql.gz | head -1 | xargs basename")
echo "BACKUP_FILE=${BACKUP_FILE}"
```

**Esperado:** variável definida com nome do arquivo. **Anote em papel** para uso no rollback.

---

## FASE 2 — Migration B-001 (1 min)

### 2.1 [ ] Conectar ao PostgreSQL de produção

```bash
ssh_vps "docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c '\\dt' | head -20"
```

**Esperado:** lista de tabelas (pacientes, profissionais, consultas, etc.).

**Falha:** `peer authentication failed` ou `connection refused` → `ssh_vps "docker logs ${DB_CONTAINER} --tail 20"` para diagnosticar.

---

### 2.2 [ ] Verificar se coluna já existe (idempotência)

```bash
ssh_vps "docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c \"SELECT column_name FROM information_schema.columns WHERE table_name='pacientes' AND column_name='data_revogacao';\""
```

**Esperado:** `0 rows` (coluna NÃO existe — B-001 ainda ativo).

**Aceitável:** `1 row` com `data_revogacao` (já foi aplicada — pular para FASE 3).

**Falha:** erro de conexão → ABORTAR.

---

### 2.3 [ ] Aplicar migration (idempotente)

```bash
ssh_vps "docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c 'ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;'"
```

**Esperado:** `ALTER TABLE` (sem erro).

**Falha:** `permission denied` → ABORTAR (contatar DBA).

---

### 2.4 [ ] Confirmar coluna criada

```bash
ssh_vps "docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c \"\\d pacientes\" | grep data_revogacao"
```

**Esperado:** `data_revogacao | timestamp` na saída.

**Falha:** coluna ausente → ABORTAR (migration não aplicou).

---

## FASE 3 — Tag e push (1 min)

### 3.1 [ ] Confirmar working tree limpo

```bash
git status
```

**Esperado:** `nothing to commit, working tree clean` ou apenas docs não commitados.

---

### 3.2 [ ] Criar tag `${TAG_NAME}`

```bash
git tag -a "${TAG_NAME}" "${RC1_HEAD}" \
  -m "${TAG_NAME}: AraOS SIAP first release candidate"
git tag -l "${TAG_NAME}"
```

**Esperado:** `${TAG_NAME}` listado.

---

### 3.3 [ ] Push da tag

```bash
git push origin "${TAG_NAME}"
```

**Esperado:** `* [new tag] ${TAG_NAME} -> ${TAG_NAME}`.

**Falha:** tag existe localmente mas push falha (sem permissão) → ABORTAR (contatar admin do remote).

---

## FASE 4 — Build da imagem (5-10 min)

### 4.1 [ ] Disparar build

```bash
curl -X POST "https://api.github.com/repos/${GITHUB_REPO}/dispatches" \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.everest-preview+json" \
  -d "{\"event_type\": \"deploy-rc1\", \"client_payload\": {\"tag\": \"${TAG_NAME}\"}}"
```

**Esperado:** HTTP 204.

**Alternativa:** se pipeline é disparado por tag push, pular este passo (já foi disparado em 3.3).

---

### 4.2 [ ] Acompanhar CI

URL: `https://github.com/${GITHUB_REPO}/actions`

**Esperado:** workflow `CD — Production (9-stage pipeline + auto-rollback)` em execução, leva 5-10 min.

**Falha:** workflow falhou → ABORTAR (verificar logs no GitHub Actions).

---

### 4.3 [ ] Confirmar imagem publicada

```bash
curl -s "https://ghcr.io/v2/${GITHUB_REPO}/siap-backend/tags/list" | python3 -c "import json,sys; d=json.load(sys.stdin); print([t for t in d.get('tags',[]) if 'rc.1' in t])"
```

**Esperado:** lista com `prod-<sha>` ou `${TAG_NAME}`.

**Falha:** tag ausente → aguardar mais 2 min, se persistir ABORTAR.

---

## FASE 5 — Pull e restart no VPS (5 min)

### 5.1 [ ] Pull da imagem nova

```bash
ssh_vps "cd ${PROJECT_DIR} && ${COMPOSE_BASE} pull backend frontend 2>&1 | tail -10"
```

**Esperado:** `Pulling backend ... Pulled` e `Pulling frontend ... Pulled`.

**Falha:** `unauthorized` → ABORTAR (renovar credenciais GHCR).

---

### 5.2 [ ] Restart dos serviços

```bash
ssh_vps "cd ${PROJECT_DIR} && ${COMPOSE_BASE} up -d backend frontend 2>&1 | tail -10"
```

**Esperado:**
```
Container ${REDIS_CONTAINER}    Running
Container ${DB_CONTAINER}       Running
Container ${BACKEND_CONTAINER}  Recreated
Container ${FRONTEND_CONTAINER} Recreated
```

**Falha:** `Container ... Failed` → ABORTAR (ver logs com `ssh_vps "docker logs ${BACKEND_CONTAINER}"`).

---

### 5.3 [ ] Aguardar estabilização

```bash
sleep 30
ssh_vps "docker ps --filter 'name=siap' --format 'table {{.Names}}\t{{.Status}}'"
```

**Esperado:** todos `Up` e `(healthy)`.

**Falha:** `(unhealthy)` ou `Restarting` → ABORTAR (rollback).

---

## FASE 6 — Healthchecks (1 min)

### 6.1 [ ] Health endpoint

```bash
curl -s -o /dev/null -w "%{http_code}\n" "${HEALTH_URL}"
```

**Esperado:** `200`.

**Falha:** `5xx` ou timeout → ABORTAR.

---

### 6.2 [ ] Schema version endpoint

```bash
curl -s "${SCHEMA_URL}" | python3 -m json.tool
```

**Esperado:**
```json
{
  "schema_version": "...",
  "columns_ok": true,
  "migrations_ok": true,
  "missing_columns": [],
  "head_revision": "REDACTED"
}
```

**Falha:** `columns_ok: false` ou `migrations_ok: false` → ABORTAR (deploy guard falhou).

---

### 6.3 [ ] Deploy guard log

```bash
ssh_vps "docker logs ${BACKEND_CONTAINER} --since 1m 2>&1 | grep -E '(deploy_guard|schema|migration)' | head -20"
```

**Esperado:** linhas mostrando `run_all_checks passed` ou similar.

**Falha:** `ABORT: schema divergente` → ROLLBACK (voltar para imagem anterior).

---

## FASE 7 — Smoke completo (5 min)

### 7.1 [ ] Executar smoke

```bash
ssh_vps "cd ${PROJECT_DIR} && ./scripts/smoke.sh --env=production 2>&1 | tee ${LOG_DIR}/smoke_rc1.log"
```

**Esperado:** smoke **sem falhas críticas** (todos endpoints críticos verdes; falhas em itens já documentados como esperados — ex: tenant isolation pré-fix P1) são aceitáveis.

**Falha:** falhas críticas em endpoints críticos (auth, pacientes, consultas, LGPD básico) → ROLLBACK.

---

### 7.2 [ ] Resumo do smoke

```bash
grep -E "(PASS|FAIL|ERROR)" ${LOG_DIR}/smoke_rc1.log | tail -20
```

**Esperado:** maioria `PASS`, falhas limitadas às categorias pré-conhecidas (LGPD revogar + tenant isolation documentadas em M34).

---

### 7.3 [ ] Latência p95 (SLA)

```bash
grep -E "p95|latency" ${LOG_DIR}/smoke_rc1.log | tail -5
```

**Esperado:** p95 dentro do SLA definido em `RELEASE_MANIFEST.md` §7 (p95 < 500ms).

**Falha:** p95 acima do SLA → ROLLBACK.

---

## FASE 8 — Carga leve (2 min)

### 8.1 [ ] Executar carga reduzida

```bash
ssh_vps "cd ${PROJECT_DIR} && locust -f tests/load/locustfile.py --headless --host=https://api.visualsmartflow.com.br -u 5 -r 1 -t 90s --html ${LOG_DIR}/load_rc1.html 2>&1 | tail -20"
```

**Esperado:** taxa de erro dentro do SLA (≤ 1%), RPS consistente com baseline.

**Falha:** taxa de erro > 5% → ROLLBACK.

---

### 8.2 [ ] Validar relatório

```bash
ssh_vps "grep -E '(Error|Median|95%|99%|RPS)' ${LOG_DIR}/load_rc1.log"
```

**Esperado:** erros dentro do SLA, p95 dentro do SLA.

---

## FASE 9 — Decisão GO/NO-GO (5 min)

### 9.1 [ ] Critérios funcionais verificados

| # | Critério funcional | OK? |
|---|--------------------|-----|
| 1 | Backup válido (arquivo > 0 bytes, consistente com baseline) | [ ] |
| 2 | Migration B-001 aplicada (coluna `data_revogacao` existe) | [ ] |
| 3 | Tag `${TAG_NAME}` criada e pushed | [ ] |
| 4 | Imagem nova puxada (sha bate) | [ ] |
| 5 | Todos containers do compose `Up (healthy)` | [ ] |
| 6 | `${HEALTH_URL}` retorna 200 | [ ] |
| 7 | `${SCHEMA_URL}` retorna `columns_ok: true` | [ ] |
| 8 | Schema validado pelo deploy_guard | [ ] |
| 9 | Smoke sem falhas críticas em endpoints críticos | [ ] |
| 10 | Latência p95 dentro do SLA | [ ] |
| 11 | Carga leve com taxa de erro dentro do SLA | [ ] |

**Se todos OK:** DECISÃO = **GO** (avançar para 9.2).
**Se 1-2 falham:** DECISÃO = **GO CONDICIONAL** (documentar e abrir issue).
**Se 3+ falham:** DECISÃO = **NO-GO** (executar rollback).

---

### 9.2 [ ] Notificar Slack

```bash
curl -X POST "${SLACK_WEBHOOK_URL}" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"✅ AraOS SIAP ${TAG_NAME} deployed to production. Smoke: sem falhas críticas. p95: <X>ms. Monitoring passivo até amanhã 8h.\"}"
```

**Esperado:** `#deploys` recebe a mensagem.

---

### 9.3 [ ] Arquivar logs

```bash
ssh_vps "tar czf ${LOG_DIR}/deploy_${TAG_NAME}_$(date +%Y%m%d_%H%M).tar.gz ${LOG_DIR}/backup_pre_deploy.log ${LOG_DIR}/smoke_rc1.log ${LOG_DIR}/load_rc1.log"
```

**Esperado:** arquivo `.tar.gz` criado.

---

## Resumo pós-deploy

| Item | Resultado |
|------|-----------|
| Decisão | GO / GO CONDICIONAL / NO-GO |
| Hora início | T+00:00 |
| Hora fim | T+__:__ |
| Duração total | ___ min |
| Próximo passo | Monitoring passivo por 24h; médicos beta entram dia seguinte às 8h |

---

**Fim do SSH_DEPLOY_CHECKLIST.** Em caso de rollback, abrir `docs/EMERGENCY_ROLLBACK.md`.