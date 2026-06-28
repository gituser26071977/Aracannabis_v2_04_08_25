# GO_LIVE_CHECKLIST — MISSÃO 22

**Data:** 2026-06-25
**Modo:** EXECUTE (somente documentação; nenhuma alteração de código/banco/infra)
**Objetivo:** checklist operacional executável para deploy de produção

---

## Janela D-7 (uma semana antes)

### 1. Comunicação prévia

| # | Ação | Responsável | Tempo | Comando | Critério OK | Critério ABORTAR | Rollback |
|---|------|-------------|-------|---------|-------------|-------------------|----------|
| 1.1 | Notificar equipe médica | Gerente | 1h | email + Slack `#araos-deploy` | Confirmação de leitura de 100% | <80% ciente | Re-agendar |
| 1.2 | Bloquear agenda de mudanças | Gerente | 30min | congelar merge em `main` | Branch `main` protegida | Falha ao congelar | Cancelar deploy |
| 1.3 | Confirmar janela de manutenção | SRE | 15min | `cal invite` 18h–22h sexta | Janela confirmada por todos | Qualquer indisponibilidade | Re-agendar |

### 2. Validação de pré-requisitos

| # | Ação | Responsável | Tempo | Comando | Critério OK | Critério ABORTAR | Rollback |
|---|------|-------------|-------|---------|-------------|-------------------|----------|
| 2.1 | `git fetch` + status limpo | Dev | 5min | `git fetch && git status` | Working tree clean | Mudanças não commitadas | `git stash` |
| 2.2 | Branch correto | Dev | 1min | `git branch --show-current` | `main` ou tag `v*.*.*` | Branch errado | `git checkout main` |
| 2.3 | Tag existe | Dev | 1min | `git tag -l "v*.*.*" \| tail -3` | Tag desejada presente | Tag ausente | `git tag v*.*.*` (cuidado) |
| 2.4 | P0 tests passando | Dev | 30s | `.venv-test/bin/python -m pytest tests/security/test_p0_remediation_m18.py -q` | todos passam | Qualquer falha | NÃO prosseguir |

---

## Janela D-3 (três dias antes)

### 3. Provisionamento

| # | Ação | Responsável | Tempo | Comando | Critério OK | Critério ABORTAR | Rollback |
|---|------|-------------|-------|---------|-------------|-------------------|----------|
| 3.1 | VPS staging provisionado | SRE | 2h | `docker-compose -f docker-compose.staging.yml up -d` | Containers healthy em 5min | Containers não iniciam | `docker-compose down` |
| 3.2 | DNS staging configurado | SRE | 1h | configurar Traefik + Let's Encrypt | `curl https://api.staging...` → 200 | TLS não emite | Aguardar 5min e tentar |
| 3.3 | `.env.staging` populado | DevOps | 15min | copiar `.env.staging.example`, gerar secrets via `python -c "import secrets; print(secrets.token_urlsafe(32))"` | Todos os ≥32 chars | Secret fraco | NÃO deploy |

### 4. Validação de capacidade

| # | Ação | Responsável | Tempo | Comando | Critério OK | Critério ABORTAR | Rollback |
|---|------|-------------|-------|---------|-------------|-------------------|----------|
| 4.1 | Load test 50u contra staging | SRE | 30min | `locust -f tests/load/locustfile.py --host=https://api.staging... -u 50 -t 5m` | Falhas <30%, p95 <500ms | Falhas >50% | NÃO promover para prod |

---

## Janela D-1 (um dia antes)

### 5. Backup completo

| # | Ação | Responsável | Tempo | Comando | Critério OK | Critério ABORTAR | Rollback |
|---|------|-------------|-------|---------|-------------|-------------------|----------|
| 5.1 | Backup manual de prod | SRE | 10min | `./scripts/backup.sh --env=production` | Backup em `/var/backups/siap/` | Falha no `pg_dump` | NÃO prosseguir |
| 5.2 | Verificar tamanho | SRE | 1min | `ls -lh /var/backups/siap/db_*.sql.gz \| tail -1` | Tamanho > versão anterior | Backup vazio | NÃO prosseguir |
| 5.3 | Anotar SHA-256 | SRE | 30s | `sha256sum backup.sql.gz` | Hash anotado em log | — | — |

### 6. Validação de secrets

| # | Ação | Responsável | Tempo | Comando | Critério OK | Critério ABORTAR | Rollback |
|---|------|-------------|-------|---------|-------------|-------------------|----------|
| 6.1 | Rodar `validate_env.py` | Dev | 30s | `python3 scripts/validate_env.py` | "OK: 0 erros" | Qualquer erro | Corrigir .env |
| 6.2 | `grep JWT_SECRET_KEY .env.production \| wc -c` | Dev | 30s | contar chars | ≥64 chars (após token) | <64 chars | Regenerar |

---

## Janela H-2 (duas horas antes)

### 7. Pré-flight

| # | Ação | Responsável | Tempo | Comando | Critério OK | Critério ABORTAR | Rollback |
|---|------|-------------|-------|---------|-------------|-------------------|----------|
| 7.1 | Status prod atual | SRE | 5min | `./scripts/healthcheck.sh --env=production` | Todos os checks OK | Qualquer FAIL | Diagnosticar antes |
| 7.2 | Comunicação "deploy em 2h" | SRE | 5min | Slack `#araos-status` | Mensagem visível | — | — |
| 7.3 | Alerta para plantão | SRE | 5min | PagerDuty ack | 1 pessoa em alerta | Ninguém disponível | Re-agendar |

---

## Janela H-1 (uma hora antes)

### 8. Congelamento

| # | Ação | Responsável | Tempo | Comando | Critério OK | Critério ABORTAR | Rollback |
|---|------|-------------|-------|---------|-------------|-------------------|----------|
| 8.1 | Modo manutenção | SRE | 5min | configurar `MAINTENANCE_MODE=true` no `.env.production` e recarregar backend, OU bloquear via Traefik | Flag ativa | — | reverter |
| 8.2 | Comunicação "deploy em 1h" | SRE | 2min | Slack | OK | — | — |
| 8.3 | Último backup incremental | SRE | 5min | `./scripts/backup.sh --env=production` | Backup OK | Falha | NÃO prosseguir |

> **Correção M22.2:** passo 8.1 reescrito. O mecanismo `touch /tmp/MAINTENANCE` **não existe** documentado no app. Operador deve usar variável de ambiente ou bloqueio de ingress.

---

## Janela Deploy (H-0)

### 9. Deploy propriamente dito

| # | Ação | Responsável | Tempo | Comando | Critério OK | Critério ABORTAR | Rollback |
|---|------|-------------|-------|---------|-------------|-------------------|----------|
| 9.1 | Checkout tag | Dev | 1min | `git fetch --tags && git checkout v*.*.*` | Tag ativa | Tag inválida | `git checkout main` |
| 9.2 | Build imagens | Dev | 3-5min | `docker-compose -f docker-compose.prod.yml build --pull` | Build OK | Build error | Corrigir Dockerfile |
| 9.3 | Backup pré-deploy | SRE | 5min | `./scripts/backup.sh --env=production` | Backup OK | Falha | NÃO prosseguir |
| 9.4 | Rolling restart backend | SRE | 2min | `docker-compose up -d --no-deps siap-backend` | Container novo healthy | Container não sobe | `docker-compose up -d --no-deps siap-backend` (anterior) |
| 9.5 | Smoke backend | SRE | 30s | `./scripts/smoke.sh --env=production` | 6 endpoints OK | Qualquer FAIL | `rollback.sh` |
| 9.6 | Rolling restart frontend | SRE | 2min | `docker-compose up -d --no-deps siap-frontend` | Frontend OK | Falha | `rollback.sh` |
| 9.7 | Smoke frontend | SRE | 30s | `curl -I https://visualsmartflow.com.br/` | 200 | !=200 | `rollback.sh` |

---

## Pós-deploy imediato

### 10. Validação H+15min

| # | Ação | Responsável | Tempo | Comando | Critério OK | Critério ABORTAR |
|---|------|-------------|-------|---------|-------------|-------------------|
| 10.1 | Logs de erro | SRE | 2min | `docker logs siap-backend --since 15m 2>&1 \| grep -i "error\|exception" \| head -20` | <5 erros | ≥5 erros incomuns |
| 10.2 | Taxa 5xx | SRE | 1min | `docker logs siap-backend --since 15m 2>&1 \| grep -c " 500 "` | <10 | ≥50 |
| 10.3 | Healthcheck | SRE | 30s | `curl https://api.visualsmartflow.com.br/api/health` | 404 (estado conhecido) | 503 | Não considerar 404 como falha — ver BLOQUEADOR #4 |
| 10.4 | Comunicação "deploy OK" | SRE | 1min | Slack | OK | — |

### 11. Validação H+30min

| # | Ação | Responsável | Tempo | Comando | Critério OK | Critério ABORTAR |
|---|------|-------------|-------|---------|-------------|-------------------|
| 11.1 | Métricas básicas | SRE | 5min | revisar logs / grafana | CPU<70%, RAM<80%, p95<500ms | CPU>90% sustentado |
| 11.2 | Webhooks processados | SRE | 5min | `grep "webhook" /var/log/siap/*.log \| wc -l` | >0 eventos | Zero webhooks em 30min (suspeito) |
| 11.3 | Billing check | SRE | 5min | acessar `/api/billing/history` no painel admin | Carrega OK | 500 |

### 12. Validação H+60min

| # | Ação | Responsável | Tempo | Comando | Critério OK | Critério ABORTAR |
|---|------|-------------|-------|---------|-------------|-------------------|
| 12.1 | Playwright contra prod | QA | 15min | `pytest tests/e2e/ --env=prod` | ≥12/13 flows passam | <10/13 |
| 12.2 | Lighthouse contra prod | QA | 5min | `lhci autorun` | Perf≥80, A11y≥90 | < thresholds |
| 12.3 | Load test leve | SRE | 10min | `locust -u 10 -t 2m --host=https://api...` | <1% falhas | >5% |

---

## Pós-deploy D+1 (24h depois)

### 13. Validação 24h

| # | Ação | Responsável | Tempo | Comando | Critério OK |
|---|------|-------------|-------|---------|-------------|
| 13.1 | Métricas noturnas | SRE | 30min | revisar Prometheus | Sem alertas triggered |
| 13.2 | Logs de incidentes | SRE | 30min | `grep ERROR /var/log/siap/*.log` | <50 erros esperados |
| 13.3 | Fila RQ | SRE | 5min | revisar tamanho da fila | <100 jobs pendentes |
| 13.4 | Backup noturno executou | SRE | 5min | `ls -lt /var/backups/siap/` | 1 backup novo |

---

## Pós-deploy D+7 (uma semana)

### 14. Auditoria pós-deploy

| # | Ação | Responsável | Tempo | Comando | Critério OK |
|---|------|-------------|-------|---------|-------------|
| 14.1 | Métricas da semana | SRE | 1h | Grafana | Sem degradação |
| 14.2 | Satisfação dos médicos | Gerente | 1h | survey | ≥80% satisfeitos |
| 14.3 | Billing reconciliação | Financeiro | 2h | comparar MP × banco | 0 discrepâncias |
| 14.4 | Retrospectiva | Equipe | 1h | meeting | Lições aprendidas registradas |

---

## Matriz de rollback

| Cenário | Quando abortar? | Comando rollback |
|---------|------------------|------------------|
| **Erro 5xx massivo (>50/min)** | H+15min | `rollback.sh --env=production` |
| **Falha de autenticação** | Imediato | `rollback.sh --env=production` |
| **Perda de dados detectada** | Imediato | `rollback.sh --env=production` + análise |
| **Billing quebrou** | H+30min | `rollback.sh --env=production` |
| **LGPD falha** | Imediato | `rollback.sh --env=production` + comunicação legal |

---

**Validade deste checklist:** até que MISSÃO 23+ o atualize com base em lições aprendidas.
