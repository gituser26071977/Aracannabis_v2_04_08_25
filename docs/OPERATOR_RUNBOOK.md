# OPERATOR_RUNBOOK — AraOS SIAP RC1 Deploy

**Versão:** 2.0 (2026-06-28)
**Origem:** M36 — Operator Handoff Package
**Hardening:** M37 — Operator Package Hardening (pre-deploy)
**Audiência:** Operador humano com acesso SSH ao VPS de produção
**Pré-requisito:** M33 (RC1 montado) + M35 (tentativa abortada por falta de acesso) concluídos

---

## 1. Pré-requisitos

### 1.1 Software no terminal do operador

| Ferramenta | Versão mínima | Comando de verificação |
|------------|---------------|------------------------|
| `ssh` | OpenSSH 7.0+ | `ssh -V` |
| `psql` (cliente PostgreSQL) | 14+ | `psql --version` |
| `docker` | 20.10+ | `docker --version` |
| `docker compose` | v2 | `docker compose version` |
| `curl` | 7.0+ | `curl --version` |
| `git` | 2.30+ | `git --version` |

### 1.2 Conectividade obrigatória

- [ ] Acesso SSH ao VPS `147.93.33.253` (porta 22)
- [ ] Usuário com privilégios `sudo` no VPS
- [ ] Acesso ao Docker daemon (usuário no grupo `docker`)
- [ ] Acesso de leitura à tabela `pacientes` no PostgreSQL de produção
- [ ] Capacidade de executar `ALTER TABLE` (DBA ou owner da tabela)

### 1.3 Credenciais necessárias

| Credencial | Onde obter | Formato esperado |
|------------|-----------|------------------|
| SSH user + chave privada | Operações/DevOps | `~/.ssh/id_rsa_vps` |
| PostgreSQL prod | Vault / `.env.prod` em `/opt/siap/.env` | `postgresql://USER:PASS@HOST:5432/DB` |
| Docker registry (se aplicável) | GitHub Packages | `ghcr.io/gituser26071977/...` |
| Slack webhook `#deploys` | DevOps | `https://hooks.slack.com/...` |

### 1.4 Estado esperado do repositório

- Branch: `fix/p0-stabilization-2026-06`
- HEAD: `REDACTED`
- Working tree: limpo (exceto `docs/GO_LIVE_EXECUTION_REPORT.md` que é doc)
- Tag `v1.0.0-rc.1`: **NÃO criada** (este runbook cria a tag)

---

### 1.5 Variáveis Operacionais

> **Defina estas variáveis UMA VEZ no shell antes de começar.** Os documentos `SSH_DEPLOY_CHECKLIST.md`, `PRODUCTION_COMMANDS.md` e `EMERGENCY_ROLLBACK.md` usam estas mesmas variáveis.

```bash
export VPS_HOST="147.93.33.253"
export VPS_USER="root"
export SSH_KEY="$HOME/.ssh/id_ed25519"
export SSH_TARGET="${VPS_USER}@${VPS_HOST}"
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

**Helper para descoberta dinâmica de container** (caso nome tenha divergido):

```bash
DB_CONTAINER=$(ssh_vps "docker ps --filter 'name=siap-db' --format '{{.Names}}' | head -1")
```

---

### 1.6 Pre-flight check (OBRIGATÓRIO)

> Execute **antes** de começar qualquer FASE. Se QUALQUER item falhar: **ABORTAR imediatamente**.

| # | Verificação | Comando (resumo) |
|---|-------------|-----------------|
| 1 | SSH funcional | `ssh -V` |
| 2 | Git funcional | `git --version` |
| 3 | Docker funcional | `docker --version` |
| 4 | Docker Compose v2 | `docker compose version` |
| 5 | curl funcional | `curl --version` |
| 6 | psql funcional | `psql --version` |
| 7 | Memória >= 1 GB | `free -g` |
| 8 | Disco >= 5 GB livres | `df -h` |
| 9 | Containers ativos | `ssh_vps "docker ps --filter 'name=siap'"` |
| 10 | Acesso ao banco | `ssh_vps "docker exec ${DB_CONTAINER} psql -U ${DB_USER} -d ${DB_NAME} -c 'SELECT 1;'"` |
| 11 | Backup dir existe+gravável | `ssh_vps "test -d ${BACKUP_DIR} && test -w ${BACKUP_DIR}"` |
| 12 | Permissões (sudo sem senha) | `ssh_vps "sudo -n true"` |

Detalhamento completo: `SSH_DEPLOY_CHECKLIST.md` §FASE 0.5.

---

## 2. Acessos necessários

### 2.1 Sequência de hosts

```
[Seu terminal]
    ↓ ssh
[VPS Produção: 147.93.33.253]
    ↓ docker compose
[Containers: siap-backend, siap-frontend, siap-db, siap-redis]
    ↓ psql
[PostgreSQL Produção: 147.93.33.253:5432, db=aracannabis]
```

### 2.2 Portas envolvidas

| Porta | Serviço | Acesso externo? |
|-------|---------|-----------------|
| 22 | SSH | SIM (chave privada) |
| 5432 | PostgreSQL | NÃO (somente local ao VPS) |
| 6379 | Redis | NÃO |
| 5002 | Backend (gunicorn) | Via nginx |
| 443 | HTTPS público | Público |
| 80 | HTTP → redirect | Público |

### 2.3 Quem deve estar online durante o deploy

| Papel | Pessoa | Quando |
|-------|--------|--------|
| Operador executor | Você | Todo o deploy (~35 min) |
| Sombra técnica | 1 dev sênior | Disponível no Slack para abortar |
| Product owner | 1 pessoa | Disponível no fim do smoke para GO/NO-GO |
| Médico beta #1 | (opcional) | Avisado para abrir às 8h do dia seguinte |

---

## 3. Duração estimada

| Etapa | Tempo | Origem do número |
|-------|-------|------------------|
| Setup terminal + SSH | 5 min | M22 + manual |
| Backup pré-deploy | 5 min | M22 + M30 |
| Migration B-001 (SQL idempotente) | < 1 min | M27 |
| Criar tag `v1.0.0-rc.1` | 1 min | M33 |
| Build imagem Docker (CI/CD) | 5-10 min | M22 pipeline |
| Pull imagem + restart containers | 5 min | M30 |
| Validar healthchecks | 1 min | M28 |
| Smoke completo (17 endpoints) | 5 min | M29 |
| Carga leve 5 users 90s | 2 min | M29 |
| Decisão GO/NO-GO | 5 min | — |
| **TOTAL** | **~35 min** | M30 FASE 8 |

**Janela recomendada:** reserve **60 minutos** totais (35 min execução + 25 min margem).

---

## 4. Janela recomendada

### 4.1 Quando executar

| Dia | Horário | Razão |
|-----|---------|-------|
| Dia de semana (ter-qui) | 14h-17h | Pico de uso já passou; médicos beta ainda não chegaram |
| **Evitar** segunda 8h-10h | — | Pico de uso semanal |
| **Evitar** sexta 16h+ | — | Plantão de fim de semana sem suporte |
| **Evitar** véspera de feriado | — | Suporte reduzido no dia seguinte |

### 4.2 Janela sugerida

**Terça ou quarta-feira, 14h-15h.** Permite:
- Manhã para revisar e fazer dry-run
- Deploy em horário de baixa utilização
- Tempo de monitoring até o fim do expediente
- Quinta para ajustes se algo precisar ser revertido

---

## 5. Sequência cronológica

### Timeline operacional

```
T+00:00  — Setup terminal, validar SSH
T+00:05  — Backup pré-deploy (./scripts/backup.sh)
T+00:10  — Validar backup (tamanho > 0, timestamp atual)
T+00:12  — Aplicar migration B-001 (SQL idempotente)
T+00:13  — Validar SELECT data_revogacao
T+00:14  — Criar tag ${TAG_NAME} + push
T+00:15  — Aguardar CI/CD buildar imagem (5-10 min)
T+00:25  — Pull imagem no VPS
T+00:27  — Restart containers (docker compose up -d)
T+00:30  — Validar ${HEALTH_URL}, ${SCHEMA_URL}
T+00:32  — Rodar smoke.sh --env=production
T+00:37  — Rodar carga leve (locust ou equivalente)
T+00:39  — Coletar métricas
T+00:40  — Decisão GO / GO CONDICIONAL / NO-GO
T+00:45  — Notificar Slack #deploys
T+01:00  — Monitoring passivo (5 médicos NÃO entram ainda)
         — Primeiro médico entra apenas no dia seguinte às 8h
```

### 5.1 Fluxograma de decisão

```
                   ┌─────────┐
                   │  START  │
                   └────┬────┘
                        ↓
                 ┌──────────────┐
                 │ Pre-flight   │──FAIL──→ ABORT
                 │ check        │
                 └──────┬───────┘
                        ↓ PASS
                   ┌─────────┐
                   │   SSH   │──FAIL──→ ABORT
                   └────┬────┘
                        ↓ PASS
                  ┌──────────┐
                  │  Backup  │──FAIL──→ ABORT
                  └─────┬────┘
                        ↓ PASS
                 ┌─────────────┐
                 │  Migration  │──FAIL──→ ABORT
                 └──────┬──────┘
                        ↓ PASS
                  ┌──────────┐
                  │  Deploy  │──FAIL──→ ROLLBACK
                  └─────┬────┘
                        ↓ PASS
                ┌──────────────┐
                │ Healthcheck │──FAIL──→ ROLLBACK
                └──────┬───────┘
                       ↓ PASS
                  ┌─────────┐
                  │  Smoke  │──FAIL──→ ROLLBACK
                  └─────┬───┘
                        ↓ PASS
                  ┌─────────┐
                  │  Carga  │──FAIL──→ ROLLBACK
                  └─────┬───┘
                        ↓ PASS
                   ┌─────────┐
                   │   GO    │
                   └────┬────┘
                        ↓
                 ┌──────────────┐
                 │ Monitoring   │
                 │ passivo 24h  │
                 └──────┬───────┘
                        ↓
                  ┌──────────┐
                  │ Beta 5   │
                  │ médicos  │
                  └──────────┘
```

---

## 6. Critérios de parada (abort triggers)

### ABORTAR IMEDIATAMENTE se:

| # | Condição | Ação |
|---|----------|------|
| 1 | Backup falha ou tamanho = 0 | ABORTAR — investigar |
| 2 | `ALTER TABLE` falha | ABORTAR — investigar permissão |
| 3 | Build da imagem falha | ABORTAR — investigar CI/CD |
| 4 | Deploy guard aborta startup em produção | ABORTAR — investigar schema |
| 5 | `${HEALTH_URL}` retorna 5xx após restart | ABORTAR — rollback |
| 6 | Smoke retorna falhas em endpoints críticos | ABORTAR — rollback |
| 7 | Latência p95 acima do SLA definido em `RELEASE_MANIFEST.md` §7 | ABORTAR — investigar |
| 8 | Taxa de erro acima do SLA | ABORTAR — rollback |

### CONTINUAR COM CAUTELA se:

| # | Condição | Ação |
|---|----------|------|
| 1 | Webhook retorna 200 sem assinatura (esperado pré-M36) | Continuar; documentar |
| 2 | Rate limit parece desativado em /auth/login | Continuar; documentar |
| 3 | X-Association-ID em `expose_headers` | Continuar; documentar |

### Prosseguir normalmente:

- Backup válido (arquivo > 0 bytes, consistente com baseline)
- Todos os endpoints críticos verdes no smoke
- Schema validado pelo deploy_guard (`columns_ok: true`)
- Latência p95 dentro do SLA definido em `RELEASE_MANIFEST.md` §7
- Todos os healthchecks retornando 200
- Containers do compose `Up (healthy)`
- 5 médicos conseguem cadastrar pacientes

---

## 7. Documentos relacionados

| Documento | Uso |
|-----------|-----|
| `docs/SSH_DEPLOY_CHECKLIST.md` | Checklist passo-a-passo |
| `docs/PRODUCTION_COMMANDS.md` | Comandos exatos (copy-paste) |
| `docs/EMERGENCY_ROLLBACK.md` | Plano de rollback < 15 min |
| `docs/GO_LIVE_CARD.md` | Cartão de referência rápida |
| `docs/RELEASE_MANIFEST.md` | Manifest do release v1.0.0-rc.1 |
| `docs/RC1_ASSEMBLY_REPORT.md` | O que o RC1 contém |
| `docs/GO_LIVE_EXECUTION_REPORT.md` | Estado da auditoria M34 |

---

**Fim do OPERATOR_RUNBOOK.** Próximo documento: `SSH_DEPLOY_CHECKLIST.md`.