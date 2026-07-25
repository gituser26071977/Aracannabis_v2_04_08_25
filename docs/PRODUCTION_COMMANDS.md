# PRODUCTION_COMMANDS — AraOS SIAP RC1

**Versão:** 2.0 (2026-06-28)
**Origem:** M36 — Operator Handoff Package
**Hardening:** M37 — Operator Package Hardening (pre-deploy)
**Audiência:** Operador executor
**Conteúdo:** Comandos exatos em ordem, sem texto adicional

---

## Como usar este documento

1. Abra em um terminal separado
2. **Cole o bloco de Variáveis Operacionais PRIMEIRO**
3. Copie e cole cada bloco NA ORDEM
4. Não modifique comandos (são exatos)
5. Em caso de dúvida: pare e consulte `OPERATOR_RUNBOOK.md`

---

## Variáveis Operacionais (colar ANTES de tudo)

```bash
export VPS_HOST="147.93.33.253"
export VPS_USER="root"
export SSH_KEY="$HOME/.ssh/id_ed25519"
export SSH_TARGET="${VPS_USER}@${VPS_HOST}"
export SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:?defina a URL do webhook Slack}"
export PROJECT_DIR="/root/projetos/araos"
export BACKUP_DIR="/var/backups/siap"
export LOG_DIR="/var/log/siap"
export COMPOSE_FILE="docker-compose.prod.yml"
export COMPOSE_BASE="docker compose -f ${PROJECT_DIR}/${COMPOSE_FILE}"
export BACKEND_CONTAINER="siap-backend"
export FRONTEND_CONTAINER="siap-frontend"
export DB_CONTAINER="siap-db"
export REDIS_CONTAINER="siap-redis"
export DB_NAME="aracannabis"
export DB_USER="siap_user"
export HEALTH_URL="https://api.visualsmartflow.com.br/api/health"
export SCHEMA_URL="https://api.visualsmartflow.com.br/api/schema-version"
export TAG_NAME="v1.0.0-rc.1"
export RC1_HEAD="REDACTED"
export RC1_BRANCH="fix/p0-stabilization-2026-06"
export GITHUB_REPO="gituser26071977/Aracannabis_v2_04_08_25"
ssh_vps() { ssh -i "$SSH_KEY" "$SSH_TARGET" "$@"; }
```

---

## BLOCO 0 — Pre-flight (OBRIGATÓRIO)

```bash
ssh -V && psql --version && docker --version && docker compose version && curl --version | head -1 && git --version
```

```bash
command -v ssh && command -v git && command -v docker && command -v curl && command -v psql
```

```bash
free -g | awk '/^Mem:/ { if ($4+0 < 1) print "FAIL mem"; else print "OK mem" }'
```

```bash
df -BG "${PROJECT_DIR}" "${BACKUP_DIR}" "${LOG_DIR}" 2>/dev/null | awk 'NR>1 { gsub("G",""); if ($4+0 < 5) print "FAIL disk:", $6; }'
```

```bash
ssh_vps "docker ps --filter 'name=siap' --format '{{.Names}}' | wc -l"
```

```bash
ssh_vps "docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c 'SELECT 1 AS ok;'"
```

```bash
ssh_vps "test -d ${BACKUP_DIR} && test -w ${BACKUP_DIR} && echo OK || (sudo mkdir -p ${BACKUP_DIR} && sudo chown ${VPS_USER}:${VPS_USER} ${BACKUP_DIR} && echo OK)"
```

```bash
ssh_vps "sudo -n true && echo 'OK passwordless sudo' || echo 'FAIL sudo'"
```

```bash
curl -s -o /dev/null -w "Slack: %{http_code}\n" -X POST "$SLACK_WEBHOOK_URL" -H "Content-Type: application/json" -d '{"text":"[pre-flight] OK"}'
```

---

## BLOCO 1 — Setup terminal

```bash
clear
date '+%Y-%m-%d %H:%M:%S %Z'
```

```bash
ssh -V && psql --version && docker --version && docker compose version && curl --version | head -1 && git --version
```

```bash
ssh_vps "hostname && uptime && whoami"
```

```bash
ssh_vps "docker ps --filter 'name=siap' --format 'table {{.Names}}\t{{.Status}}'"
```

---

## BLOCO 2 — Backup pré-deploy

```bash
ssh_vps "ls -ld ${BACKUP_DIR}"
```

```bash
ssh_vps "cd ${PROJECT_DIR} && ./scripts/backup.sh --env=production 2>&1 | tee ${LOG_DIR}/backup_pre_deploy.log"
```

```bash
ssh_vps "ls -lah ${BACKUP_DIR}/ | tail -5 && du -sh ${BACKUP_DIR}/aracannabis_*.sql.gz | tail -1"
```

```bash
ssh_vps "ls -t ${BACKUP_DIR}/aracannabis_*.sql.gz | head -1 | xargs basename"
```

---

## BLOCO 3 — Migration B-001

```bash
ssh_vps "docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c '\\dt' | head -20"
```

```bash
ssh_vps "docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c \"SELECT column_name FROM information_schema.columns WHERE table_name='pacientes' AND column_name='data_revogacao';\""
```

```bash
ssh_vps "docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c 'ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;'"
```

```bash
ssh_vps "docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c \"\\d pacientes\" | grep data_revogacao"
```

---

## BLOCO 4 — Tag e push

```bash
git status
```

```bash
git tag -a "${TAG_NAME}" "${RC1_HEAD}" -m "${TAG_NAME}: AraOS SIAP first release candidate"
```

```bash
git tag -l "${TAG_NAME}"
```

```bash
git push origin "${TAG_NAME}"
```

---

## BLOCO 5 — Build (CI/CD)

```bash
curl -X POST "https://api.github.com/repos/${GITHUB_REPO}/dispatches" -H "Authorization: token ${GITHUB_TOKEN}" -H "Accept: application/vnd.github.everest-preview+json" -d "{\"event_type\": \"deploy-rc1\", \"client_payload\": {\"tag\": \"${TAG_NAME}\"}}"
```

```bash
sleep 300 && curl -s "https://ghcr.io/v2/${GITHUB_REPO}/siap-backend/tags/list" | python3 -c "import json,sys; d=json.load(sys.stdin); print([t for t in d.get('tags',[]) if 'rc.1' in t])"
```

---

## BLOCO 6 — Pull e restart

```bash
ssh_vps "cd ${PROJECT_DIR} && ${COMPOSE_BASE} pull backend frontend 2>&1 | tail -10"
```

```bash
ssh_vps "cd ${PROJECT_DIR} && ${COMPOSE_BASE} up -d backend frontend 2>&1 | tail -10"
```

```bash
sleep 30 && ssh_vps "docker ps --filter 'name=siap' --format 'table {{.Names}}\t{{.Status}}'"
```

---

## BLOCO 7 — Healthchecks

```bash
curl -s -o /dev/null -w "%{http_code}\n" "${HEALTH_URL}"
```

```bash
curl -s "${SCHEMA_URL}" | python3 -m json.tool
```

```bash
ssh_vps "docker logs ${BACKEND_CONTAINER} --since 1m 2>&1 | grep -E '(deploy_guard|schema|migration)' | head -20"
```

---

## BLOCO 8 — Smoke

```bash
ssh_vps "cd ${PROJECT_DIR} && ./scripts/smoke.sh --env=production 2>&1 | tee ${LOG_DIR}/smoke_rc1.log"
```

```bash
grep -E "(PASS|FAIL|ERROR)" ${LOG_DIR}/smoke_rc1.log | tail -20
```

```bash
grep -E "p95|latency" ${LOG_DIR}/smoke_rc1.log | tail -5
```

---

## BLOCO 9 — Carga

```bash
ssh_vps "cd ${PROJECT_DIR} && locust -f tests/load/locustfile.py --headless --host=https://api.visualsmartflow.com.br -u 5 -r 1 -t 90s --html ${LOG_DIR}/load_rc1.html 2>&1 | tail -20"
```

```bash
ssh_vps "grep -E '(Error|Median|95%|99%|RPS)' ${LOG_DIR}/load_rc1.log"
```

---

## BLOCO 10 — Decisão e notificação

```bash
curl -X POST "${SLACK_WEBHOOK_URL}" -H "Content-Type: application/json" -d "{\"text\": \"✅ AraOS SIAP ${TAG_NAME} deployed. Smoke OK. p95: <X>ms.\"}"
```

```bash
ssh_vps "tar czf ${LOG_DIR}/deploy_${TAG_NAME}_$(date +%Y%m%d_%H%M).tar.gz ${LOG_DIR}/backup_pre_deploy.log ${LOG_DIR}/smoke_rc1.log ${LOG_DIR}/load_rc1.log"
```

```bash
date '+%Y-%m-%d %H:%M:%S %Z'
```

---

## BLOCO EMERGÊNCIA — Rollback

```bash
ssh_vps "cd ${PROJECT_DIR} && ./scripts/rollback.sh --env=production 2>&1 | tee ${LOG_DIR}/rollback_${TAG_NAME}.log"
```

```bash
ssh_vps "docker ps --filter 'name=siap' --format 'table {{.Names}}\t{{.Status}}'"
```

```bash
curl -s -o /dev/null -w "%{http_code}\n" "${HEALTH_URL}"
```

```bash
curl -X POST "${SLACK_WEBHOOK_URL}" -H "Content-Type: application/json" -d "{\"text\": \"🚨 ROLLBACK AraOS SIAP ${TAG_NAME} executado. Investigação em andamento.\"}"
```

---

**Fim do PRODUCTION_COMMANDS.** Para detalhes de cada passo, abrir `SSH_DEPLOY_CHECKLIST.md`.