# EMERGENCY_ROLLBACK — AraOS SIAP RC1

**Versão:** 2.0 (2026-06-28)
**Origem:** M36 — Operator Handoff Package
**Hardening:** M37 — Operator Package Hardening (pre-deploy)
**SLA:** Rollback executado em **< 15 minutos** do início ao fim
**Trigger:** Falha em qualquer critério de abort do `OPERATOR_RUNBOOK.md` §6

---

## Variáveis Operacionais

> **Cole este bloco NO INÍCIO do rollback** (substitui o bloco completo de `OPERATOR_RUNBOOK.md` §1.5):

```bash
export VPS_HOST="147.93.33.253"
export VPS_USER="root"
export SSH_KEY="$HOME/.ssh/id_ed25519"
export SSH_TARGET="${VPS_USER}@${VPS_HOST}"
export PROJECT_DIR="/root/projetos/araos"
export BACKUP_DIR="/var/backups/siap"
export LOG_DIR="/var/log/siap"
export COMPOSE_FILE="docker-compose.prod.yml"
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
ssh_vps() { ssh -i "$SSH_KEY" "$SSH_TARGET" "$@"; }
```

---

## TL;DR (modo pânico)

Se você precisa reverter AGORA e não tem tempo de ler tudo:

```bash
ssh_vps "cd ${PROJECT_DIR} && ./scripts/rollback.sh --env=production"
```

**Pronto.** O script cuida de tudo em ~10 min. Volte aqui depois para documentar.

---

## Quando executar rollback

| # | Trigger | Origem |
|---|---------|--------|
| 1 | Backup falhou OU tamanho = 0 | SSH §1.3 |
| 2 | `ALTER TABLE` falhou | SSH §2.3 |
| 3 | Build da imagem falhou | SSH §4.2 |
| 4 | Deploy guard abortou startup | SSH §6.3 |
| 5 | `${HEALTH_URL}` retornou 5xx após restart | SSH §6.1 |
| 6 | Smoke: falhas em endpoints críticos | SSH §7.1 |
| 7 | Latência p95 acima do SLA | SSH §7.3 |
| 8 | Taxa de erro acima do SLA na carga | SSH §8.2 |
| 9 | Médicos beta reportam erro grave em produção | Slack #suporte |
| 10 | Violação de segurança descoberta após deploy | Slack #security |

---

## O que o rollback FAZ e o que NÃO FAZ

### FAZ

| # | Ação | Efeito |
|---|------|--------|
| 1 | Para containers do RC1 (`docker compose down`) | Backend/frontend do RC1 saem do ar |
| 2 | Sobe containers com imagem anterior (`prod-<sha-anterior>`) | Backend/frontend voltam ao estado pré-RC1 |
| 3 | NÃO executa migration de downgrade | Migration B-001 permanece em prod (é aditiva, não quebra nada) |
| 4 | Roda smoke pós-rollback | Confirma que endpoints básicos voltaram |
| 5 | Notifica Slack `#deploys` | Time sabe do rollback |

### NÃO FAZ

| # | Não-ação | Por quê |
|---|----------|---------|
| 1 | **Não remove a coluna `data_revogacao`** | A migration é aditiva (`ADD COLUMN IF NOT EXISTS`); remover poderia quebrar dados de LGPD que começaram a ser preenchidos |
| 2 | **Não restaura o banco de dados** | Schema do banco não foi modificado de forma destrutiva; restaurar seria exagero |
| 3 | **Não desfaz a tag `v1.0.0-rc.1`** | Tag no Git é apenas um marcador; pode ser refeita |
| 4 | **Não apaga logs** | Precisamos deles para post-mortem |

---

## Sequência operacional (10-15 min)

### T+00:00 — Decisão (30s)

1. Operador confirma trigger de rollback
2. Operador anuncia no Slack `#deploys`: "🚨 iniciando rollback AraOS RC1"
3. Operador abre este documento

---

### T+00:00:30 — Identificar imagem anterior (1 min)

```bash
ssh_vps "docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}' | grep ${BACKEND_CONTAINER%:*} | head -10"
```

**Esperado:**
```
siap-backend  prod-<sha-anterior>  2026-06-15 ...
siap-backend  prod-<sha-rc1>       2026-06-28 ... (atual, problemático)
```

**Ação:** anotar o sha-anterior (`SHA_ANTERIOR`).

---

### T+00:01:30 — Parar containers do RC1 (2 min)

```bash
ssh_vps "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} down ${BACKEND_CONTAINER} ${FRONTEND_CONTAINER} 2>&1 | tail -10"
```

**Esperado:**
```
Stopping ${BACKEND_CONTAINER}   ... done
Stopping ${FRONTEND_CONTAINER}  ... done
```

**Falha:** se não parar em 1 min → `ssh_vps "docker kill ${BACKEND_CONTAINER} ${FRONTEND_CONTAINER}"`.

---

### T+00:03:30 — Atualizar tag da imagem (2 min)

```bash
SHA_ANTERIOR="<preencher-sha-anterior>"
ssh_vps "cd ${PROJECT_DIR} && sed -i 's|${BACKEND_CONTAINER}:prod-.*|${BACKEND_CONTAINER}:prod-${SHA_ANTERIOR}|' ${COMPOSE_FILE} && sed -i 's|${FRONTEND_CONTAINER}:prod-.*|${FRONTEND_CONTAINER}:prod-${SHA_ANTERIOR}|' ${COMPOSE_FILE}"
```

**Verificar:**
```bash
ssh_vps "grep -E '(${BACKEND_CONTAINER}|${FRONTEND_CONTAINER}):' ${PROJECT_DIR}/${COMPOSE_FILE}"
```

**Esperado:** ambas linhas apontam para `${SHA_ANTERIOR}`.

---

### T+00:05:30 — Subir containers com imagem anterior (3 min)

```bash
ssh_vps "cd ${PROJECT_DIR} && docker compose -f ${COMPOSE_FILE} up -d ${BACKEND_CONTAINER} ${FRONTEND_CONTAINER} 2>&1 | tail -10"
```

**Esperado:**
```
Container ${REDIS_CONTAINER}    Running
Container ${DB_CONTAINER}       Running
Container ${BACKEND_CONTAINER}  Recreated
Container ${FRONTEND_CONTAINER} Recreated
```

---

### T+00:08:30 — Aguardar estabilização (1 min)

```bash
sleep 30 && ssh_vps "docker ps --filter 'name=siap' --format 'table {{.Names}}\t{{.Status}}'"
```

**Esperado:** todos `Up` e `(healthy)`.

---

### T+00:09:30 — Healthcheck (1 min)

```bash
curl -s -o /dev/null -w "%{http_code}\n" "${HEALTH_URL%/health}/csrf-token"
```

**Esperado:** `200` (endpoint do estado pré-RC1 está no ar).

**Falha:** 5xx → investigar logs (rollback falhou).

```bash
ssh_vps "docker logs ${BACKEND_CONTAINER} --since 1m 2>&1 | tail -30"
```

---

### T+00:10:30 — Smoke pós-rollback (3 min)

```bash
ssh_vps "cd ${PROJECT_DIR} && ./scripts/smoke.sh --env=production 2>&1 | tee ${LOG_DIR}/rollback_smoke.log"
```

**Esperado:** smoke **sem falhas críticas** (baseline conhecida do estado pré-RC1).

**Falha:** falhas críticas → rollback não restaurou estado conhecido; investigar manualmente.

---

### T+00:13:30 — Notificar Slack (30s)

```bash
curl -X POST "${SLACK_WEBHOOK_URL}" -H "Content-Type: application/json" -d "{\"text\": \"✅ Rollback AraOS ${TAG_NAME} concluído em ~13 min. Sistema no estado pré-RC1. Post-mortem agendado.\"}"
```

---

### T+00:14:00 — Arquivar logs (1 min)

```bash
ssh_vps "tar czf ${LOG_DIR}/rollback_${TAG_NAME}_$(date +%Y%m%d_%H%M).tar.gz ${LOG_DIR}/rollback*.log ${LOG_DIR}/smoke_rc1.log ${LOG_DIR}/load_rc1.log 2>/dev/null"
```

---

### T+00:15:00 — Encerrar ciclo

**Total: 15 min** (dentro do SLA).

---

## Pós-rollback (próximas horas)

### Imediatamente (próximos 30 min)

1. **Anunciar:** Slack `#deploys` e `#engenharia` que sistema está no estado pré-RC1
2. **Bloquear médicos beta:** avisar que NÃO entrem no sistema até novo aviso
3. **Coletar evidências:** logs, métricas, screenshots do que estava errado
4. **Marcar incidente:** abrir ticket P1 no board

### Nas próximas 4h

1. **Post-mortem:** reunião rápida (30 min) — o que deu errado, por que passou pelos testes anteriores
2. **Identificar causa raiz:** bug de código? configuração? capacidade? segurança?
3. **Decidir fix:** hotfix no RC1 ou voltar para dev e re-RC1?
4. **Atualizar docs:** este runbook pode ter ganhado uma nova armadilha conhecida

### Nas próximas 24h

1. **Re-deploy** (quando fix estiver pronto): executar FASE 1-9 do `SSH_DEPLOY_CHECKLIST.md` novamente
2. **Validar:** smoke + carga devem passar com fix aplicado
3. **Decidir GO:** somente após 24h de monitoring estável

---

## Critérios de "rollback concluído com sucesso"

| # | Critério | Verificação |
|---|----------|-------------|
| 1 | Containers pré-RC1 rodando | `docker ps` mostra imagens antigas |
| 2 | Healthcheck 200 | `${HEALTH_URL}` retorna 200 |
| 3 | Smoke sem falhas críticas | `./scripts/smoke.sh` retorna baseline conhecida |
| 4 | Slack notificado | Mensagem visível em `#deploys` |
| 5 | Logs arquivados | `.tar.gz` em `${LOG_DIR}/` |
| 6 | Sem dados perdidos | DB intacto (rollback é só de código, não de dados) |

---

## Anti-patterns (o que NÃO fazer durante rollback)

| # | NÃO faça | Por quê |
|---|----------|---------|
| 1 | Tentar corrigir o bug durante o rollback | Primeiro restaure o serviço, depois corrija |
| 2 | Reiniciar o container repetidamente esperando "dar certo" | Vai mascarar a causa raiz |
| 3 | Tentar aplicar migration de downgrade | Migration B-001 é aditiva, não precisa |
| 4 | Deletar a coluna `data_revogacao` | Pode quebrar dados de LGPD que foram preenchidos |
| 5 | Pular o smoke pós-rollback | Pode deixar sistema em estado inconsistente |
| 6 | Não documentar | Post-mortem fica impossível sem logs |
| 7 | Esperar mais de 15 min para rollback começar | SLA é 15 min — se passou, escalar |
| 8 | Reiniciar o DB durante rollback | Vai gerar mais caos |

---

## Contatos de escalação

| Nível | Quem | Quando | Canal |
|-------|------|--------|-------|
| L1 | Operador executor | 0-5 min | Slack `#deploys` |
| L2 | Dev sênior on-call | 5-10 min | Telefone (ver PagerDuty) |
| L3 | Engenheiro líder | 10-15 min | Telefone direto |
| L4 | CTO | > 15 min | Telefone direto |

---

**Fim do EMERGENCY_ROLLBACK.** Em caso de rollback completo bem-sucedido, abrir post-mortem em `docs/POST_MORTEM_<data>.md`.