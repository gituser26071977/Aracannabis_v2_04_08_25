# GO_LIVE_CARD — AraOS SIAP v1.0.0-rc.1

**Versão:** 2.0 (2026-06-28)
**Origem:** M36 — Operator Handoff Package
**Hardening:** M37 — Operator Package Hardening (pre-deploy)
**Formato:** Cartão de referência rápida (1 página, imprimível)
**Audiência:** Operador, sombra técnica, product owner

---

## Variáveis Operacionais (essenciais, resumidas)

```bash
export VPS_HOST="147.93.33.253"; export VPS_USER="root"
export SSH_KEY="$HOME/.ssh/id_ed25519"
export PROJECT_DIR="/root/projetos/araos"; export BACKUP_DIR="/var/backups/siap"
export LOG_DIR="/var/log/siap"; export COMPOSE_FILE="docker-compose.prod.yml"
export BACKEND_CONTAINER="siap-backend"; export DB_CONTAINER="siap-db"
export DB_NAME="aracannabis"; export DB_USER="siap_user"
export HEALTH_URL="https://api.visualsmartflow.com.br/api/health"
export SCHEMA_URL="https://api.visualsmartflow.com.br/api/schema-version"
export TAG_NAME="v1.0.0-rc.1"
export RC1_HEAD="REDACTED"
export SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:?definir}"
ssh_vps() { ssh -i "$SSH_KEY" "${VPS_USER}@${VPS_HOST}" "$@"; }
```

Bloco completo: `OPERATOR_RUNBOOK.md` §1.5.

---

## QUANDO

| Item | Valor |
|------|-------|
| Dia recomendado | Terça ou quarta-feira |
| Horário | 14h-15h (horário de baixo uso) |
| Duração | ~35 min de execução + 25 min de margem |
| Janela total reservada | **60 minutos** |
| Evitar | Segunda 8-10h, sexta 16h+, véspera de feriado |

---

## QUEM

| Papel | Pessoa | Disponível em |
|-------|--------|---------------|
| **Operador executor** | Você | Todo o deploy |
| **Sombra técnica** | 1 dev sênior | Slack `#deploys` (pode abortar) |
| **Product owner** | 1 pessoa | Fim do smoke (decisão GO/NO-GO) |
| **Médicos beta** | 5 médicos | **NÃO entram** durante deploy; entram dia seguinte 8h |

---

## ABORT (parar imediatamente se)

| # | Trigger | Ação |
|---|---------|------|
| 1 | Backup falha ou 0 bytes | PARE — investigar |
| 2 | `ALTER TABLE` falha | PARE — investigar permissão |
| 3 | Build da imagem falha | PARE — investigar CI/CD |
| 4 | Deploy guard aborta startup | PARE — investigar schema |
| 5 | `${HEALTH_URL}` retorna 5xx | **ROLLBACK** |
| 6 | Smoke: falhas em endpoints críticos | **ROLLBACK** |
| 7 | p95 acima do SLA | **ROLLBACK** |
| 8 | Taxa erro acima do SLA | **ROLLBACK** |

**Comando de rollback:**
```bash
ssh_vps "cd ${PROJECT_DIR} && ./scripts/rollback.sh --env=production"
```

---

## FLUXOGRAMA

```
  START
    ↓
[Pre-flight]──FAIL──→ ABORT
    ↓ PASS
  SSH
    ↓
[Backup]──FAIL──→ ABORT
    ↓
[Migration]──FAIL──→ ABORT
    ↓
[Deploy]──FAIL──→ ROLLBACK
    ↓
[Healthcheck]──FAIL──→ ROLLBACK
    ↓
[Smoke]──FAIL──→ ROLLBACK
    ↓
[Carga]──FAIL──→ ROLLBACK
    ↓
   GO
    ↓
[Monitor 24h]
    ↓
[Beta 5 médicos]
```

---

## SEQUÊNCIA (resumo)

```
1. Setup terminal (5 min)
   └─ ssh_vps "hostname && uptime && whoami"
2. Pre-flight (2 min)
   └─ 12 verificações (SSH, Git, Docker, memória, disco, DB, backup dir, sudo, slack)
3. Backup (5 min)
   └─ ssh_vps "cd ${PROJECT_DIR} && ./scripts/backup.sh --env=production"
4. Migration B-001 (1 min)
   └─ ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP
5. Tag + push (1 min)
   └─ git tag -a ${TAG_NAME} ${RC1_HEAD} -m "..."
6. Build CI (5-10 min)
   └─ GitHub Actions builda imagem
7. Pull + restart (5 min)
   └─ ssh_vps "docker compose -f ${COMPOSE_FILE} pull && up -d"
8. Healthchecks (1 min)
   └─ curl ${HEALTH_URL} && curl ${SCHEMA_URL}
9. Smoke (5 min)
   └─ ssh_vps "./scripts/smoke.sh --env=production"
10. Carga (2 min)
    └─ locust -u 5 -t 90s
11. Decisão GO/NO-GO (5 min)
    └─ Slack #deploys
```

**TOTAL: ~35 min**

---

## DECISÃO GO/NO-GO (critérios funcionais, 30s)

| # | Critério funcional | OK? |
|---|--------------------|-----|
| 1 | Backup válido (arquivo > 0 bytes, consistente) | [ ] |
| 2 | Migration B-001 aplicada (coluna existe) | [ ] |
| 3 | Tag `${TAG_NAME}` pushed | [ ] |
| 4 | Containers todos `Up (healthy)` | [ ] |
| 5 | `${HEALTH_URL}` retorna 200 | [ ] |
| 6 | `${SCHEMA_URL}` retorna `columns_ok: true` | [ ] |
| 7 | Smoke sem falhas em endpoints críticos | [ ] |
| 8 | Latência p95 dentro do SLA | [ ] |
| 9 | Carga com taxa de erro dentro do SLA | [ ] |

- **Todos OK** → **GO**
- **1-2 falham** → **GO CONDICIONAL** (documentar)
- **3+ falham** → **NO-GO** (rollback)

---

## APÓS GO

| Quando | O que |
|--------|-------|
| Imediatamente | Slack `#deploys`: "✅ deploy concluído" |
| Próximas 2h | Monitoring passivo (logs, métricas) |
| Próximas 12h | NÃO deixar médicos beta entrarem |
| **Dia seguinte 8h** | Liberar acesso aos 5 médicos beta |
| Dia seguinte 18h | Retrospectiva rápida (30 min) |

---

## EMERGÊNCIA

| Situação | Comando |
|----------|---------|
| Rollback | `ssh_vps "cd ${PROJECT_DIR} && ./scripts/rollback.sh --env=production"` |
| Logs backend | `ssh_vps "docker logs ${BACKEND_CONTAINER} --since 5m"` |
| Status DB | `ssh_vps "docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c '\\dt'"` |
| Slack | `curl -X POST ${SLACK_WEBHOOK_URL} -H "Content-Type: application/json" -d '{"text":"..."}'` |

---

## CONTATOS

| Canal | Onde |
|-------|------|
| Slack `#deploys` | Dia-a-dia |
| Slack `#security` | Se LGPD/segurança |
| Telefone sênior | PagerDuty / ver lista on-call |
| Telefone CTO | Escalar L4 (> 15 min de rollback) |

---

## DOCS RELACIONADOS (não reimprima)

| Documento | Conteúdo |
|-----------|----------|
| `docs/OPERATOR_RUNBOOK.md` | Pré-requisitos, duração, janelas, sequência, abort triggers |
| `docs/SSH_DEPLOY_CHECKLIST.md` | Checklist passo-a-passo com comandos |
| `docs/PRODUCTION_COMMANDS.md` | Comandos exatos copy-paste |
| `docs/EMERGENCY_ROLLBACK.md` | Plano de rollback < 15 min |
| `docs/GO_LIVE_EXECUTION_REPORT.md` | Estado pré-deploy (M34) |
| `docs/FINAL_DEPLOY_REPORT.md` | Por que M35 abortou |
| `RELEASE_MANIFEST.md` | O que o RC1 contém |

---

## HEAD DO RC1

```
${RC1_HEAD}
```

Branch: `${RC1_BRANCH}`

---

**Fim do GO_LIVE_CARD.** Imprima este cartão e deixe com a sombra técnica durante o deploy.