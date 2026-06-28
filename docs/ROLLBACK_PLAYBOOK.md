# ROLLBACK_PLAYBOOK — MISSÃO 22

**Data:** 2026-06-25
**Modo:** EXECUTE
**Objetivo:** responder: quando abortar, quando continuar, qual perda máxima, tempo, validação

---

## 1. Quando abortar imediatamente?

Acionar `rollback.sh --env=production` **SEM HESITAÇÃO** se:

| # | Cenário | Detecção | Tempo de reação |
|---|---------|----------|------------------|
| 1 | **Erro 5xx massivo** (>50/min em /api/*) | Logs ou métrica | <2 min |
| 2 | **Falha de autenticação** (login retorna 500) | Smoke test H+15 | <5 min |
| 3 | **Vazamento de PHI cross-tenant** detectado | Logs de auditoria | IMEDIATO |
| 4 | **Perda de dados** confirmada | Query SQL mostra count menor | IMEDIATO |
| 5 | **LGPD-04 falha** (ex: dados excluídos voltam) | Auditoria pós-restore | IMEDIATO |
| 6 | **Webhook MP rejeitando pagamentos** | Taxa de erro MP > 10% | <10 min |
| 7 | **CSP quebrando frontend** (tela branca) | Browser reporta | <5 min |
| 8 | **/api/health retornando 503 sustentado** | Probe | <5 min |
| 9 | **Pool PG esgotado** (todas conexões em uso) | Métricas `pg_stat_activity` | <5 min |
| 10 | **Comando manual do gerente/PO** | Slack/telefone | IMEDIATO |

## 2. Quando continuar (NÃO abortar)?

| # | Cenário | Por que continuar |
|---|---------|---------------------|
| 1 | Lentidão isolada (<5s) | Pode ser cache miss |
| 2 | 1-2 erros 5xx em 15min | Ruído normal |
| 3 | Um webhook MP duplicado | Dedup funciona |
| 4 | Latência alta em horário de pico | Esperado |
| 5 | Container reiniciou 1 vez | Auto-recovery |
| 6 | Alerta amarelo em métrica | Investigar, não abortar |

## 3. Qual perda máxima aceitável (RPO)?

| Cenário | RPO aceitável | Observação |
|---------|---------------|------------|
| Webhook MP | **1 minuto** | Reenvio de MP cobre |
| Cadastro de paciente | **0** (perda inaceitável) | LGPD exige retenção |
| Consulta/evolução | **0** | PHI crítico |
| Log de auditoria | **0** | Compliance |
| Métricas | **5 minutos** | Prometheus retém 15d |
| Backup | **24 horas** | Diário 03:00 UTC |

## 4. Tempo máximo de rollback

| Cenário | Tempo alvo | Tempo máximo aceitável |
|---------|------------|-------------------------|
| Rollback de aplicação (sem restore de DB) | **2 minutos** | 5 minutos |
| Rollback com restore de DB 100MB | **5 minutos** | 10 minutos |
| Rollback com restore de DB 1GB | **15 minutos** | 30 minutos |
| Rollback com restore de DB 10GB+ | **1 hora** | 2 horas |

**Mitigação para DBs grandes:** WAL archiving + replicação contínua (MISSÃO 24+).

## 5. Como validar rollback?

Após executar `rollback.sh --env=production`:

```bash
# 1. Health endpoint
curl -sk https://api.visualsmartflow.com.br/api/health
# Esperado: 200 (ou 404 se ainda não deployado)

# 2. Smoke
./scripts/smoke.sh --env=production
# Esperado: 6 endpoints OK

# 3. Logs do rollback
docker logs siap-backend --since 5m | grep -i "rollback\|restore"

# 4. Métricas
./scripts/healthcheck.sh --env=production

# 5. Verificar SHA da imagem
docker inspect --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' siap-backend 2>/dev/null || \
  docker exec siap-backend cat /app/REVISION 2>/dev/null || \
  git rev-parse HEAD
# Esperado: SHA anterior ao deploy com problema
```

> **Correção M22.2:** comando original `cat /opt/araos/REVISION` referenciava arquivo inexistente.
> Substituído por 3 alternativas, em ordem de preferência:
> 1. OCI label `org.opencontainers.image.revision` (se CI/CD setar)
> 2. Arquivo `/app/REVISION` no container (convenção comum)
> 3. `git rev-parse HEAD` no host (sempre funciona)

## 6. Procedimento passo a passo

### 6.1 Identificar problema (SRE)

```bash
# Logs recentes
docker logs siap-backend --since 5m 2>&1 | tail -100

# Métricas
docker exec siap-backend ps aux | head -20

# Banco
docker exec siap-db psql -U siap_user -d aracannabis -c "SELECT count(*) FROM pacientes;"
```

### 6.2 Decidir (SRE + Gerente)

Consultar matriz da Seção 1. Se `ABORTAR`:

```bash
# Comunicação
echo ":rotating_light: ABORTANDO deploy $(git describe --tags)" | \
  curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"$(cat -)\"}" \
  $SLACK_WEBHOOK_URL
```

### 6.3 Executar rollback

```bash
./scripts/rollback.sh --env=production
```

O script:
1. Identifica backup mais recente
2. Para backend
3. Restaura banco
4. Reinicia backend
5. Roda smoke

### 6.4 Validar

```bash
./scripts/smoke.sh --env=production
./scripts/healthcheck.sh --env=production
```

### 6.5 Comunicar

```bash
echo ":white_check_mark: Rollback concluído. Sistema em $(git describe --tags) (anterior)." | \
  curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"$(cat -)\"}" \
  $SLACK_WEBHOOK_URL
```

### 6.6 Post-mortem (D+1)

- [ ] Qual era o problema?
- [ ] Por que smoke não pegou?
- [ ] Quanto tempo de indisponibilidade?
- [ ] Quantos usuários afetados?
- [ ] Ação corretiva?

## 7. Comunicação durante rollback

| Tempo | Mensagem | Canal |
|-------|----------|-------|
| Decisão | "ABORTANDO deploy $TAG — investigando" | Slack `#araos-incidents` |
| Rollback executando | "Rollback em andamento — RPO estimado: X min" | Slack |
| Rollback OK | "Sistema restaurado em $TAG anterior. Investigando causa raiz." | Slack |
| Post-mortem | "Causa raiz: $X. Fix em $Y" | Email + Slack |

## 8. Situações especiais

### 8.1 Rollback parcial (só backend, mantém DB)

Quando o problema é **apenas** código:

```bash
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d --no-deps siap-backend
```

Sem `restore.sh`. Apenas reverte imagem.

### 8.2 Rollback total (com restore)

Quando há corrupção de DB ou migration problemática:

```bash
./scripts/rollback.sh --env=production --to-backup=/var/backups/siap/db_prod_20260625_120000.sql.gz
```

### 8.3 Forward-fix (corrigir sem rollback)

Se o problema é **conhecido e trivial**:

```bash
git checkout main
# patch
git commit -m "fix: ..."
git tag v1.2.4   # incrementar patch manualmente (caractere '+' não é válido em tag git)
./scripts/deploy_prod.sh v1.2.4
```

> **Correção M22.2:** `git tag v*.*.*+1` substituído por **incremento manual de versão SemVer** (`v1.2.3` → `v1.2.4`). Caractere `+` não é permitido em nomes de tag do git.

## 9. Auditoria pós-rollback

| Item | Responsável | Tempo |
|------|-------------|-------|
| Registrar incidente | SRE | 5min |
| Contar usuários afetados | SRE | 30min |
| Post-mortem | Equipe | 1h |
| Atualizar runbook | SRE | 1h |
| Commit fix | Dev | varia |
