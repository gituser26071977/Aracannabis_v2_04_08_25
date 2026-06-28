# OBSERVABILITY REPORT — MISSÃO 21 (FASE 7)

**Data:** 2026-06-25
**Modo:** EXECUTE
**Objetivo:** responder: "às 03:00 da manhã, um operador consegue descobrir rapidamente onde, quando, impacto e causa?"

---

## 1. Sumário executivo

| Capacidade | Estado atual | Onde está |
|------------|--------------|-----------|
| **Grafana** | ❌ não provisionado | config M20 existe, sem deploy |
| **Prometheus** | ❌ não provisionado | config M20 existe, sem deploy |
| **Alertmanager** | ❌ não provisionado | config M20 existe, sem deploy |
| **Healthcheck endpoint** | ⚠️ existe no código (M20) | **NÃO deployado em prod** (404 confirmado em OAT_REPORT) |
| **Logs centralizados** | ⚠️ locais (volume Docker) | sem agregação |
| **Tracing distribuído** | ❌ não implementado | sem OpenTelemetry |
| **Correlation IDs** | ⚠️ parcial | request_id existe em algumas rotas |
| **Métricas de negócio** | ❌ não expostas | sem `/metrics` Prometheus |
| **Alertas em tempo real** | ❌ sem canal | Slack não configurado |

---

## 2. Respondendo as perguntas da FASE 7

### "às 03:00 da manhã, onde ocorreu?"

**Estado atual:** operador precisa SSH no VPS + `docker logs siap-backend | grep ERROR`. **MTTR para encontrar: 5-30min.**

**Com Prometheus/Grafana (M20 provisionado):** <1min via dashboard filtrado por job/instance.

### "às 03:00, quando ocorreu?"

**Estado atual:** `docker logs --since 10m` dá janela de tempo. **MTTR: 1-5min.**

**Com Prometheus:** query `time() - alert_start_time` retorna em segundos.

### "às 03:00, qual o impacto?"

**Estado atual:** sem métricas, operador precisa estimar manualmente. **MTTR: 5-15min.**

**Com métricas:** `rate(http_requests_total{status=~"5.."}[5m])` retorna em segundos.

### "às 03:00, qual a causa provável?"

**Estado atual:** sem tracing, sem correlation_id, causa fica em "achismo" via logs. **MTTR: 30-120min.**

**Com OpenTelemetry + tracing distribuído:** trace ID permite seguir request por todos os serviços. **MTTR: 5-10min.**

---

## 3. Estado do que está escrito vs deployado

| Item | Escrito em M20 | Deployado em prod |
|------|----------------|-------------------|
| `/api/health` | ✅ | ❌ (404 confirmado) |
| `prometheus.yml` | ✅ | ❌ |
| `alert.rules.yml` | ✅ (14 regras) | ❌ |
| `alertmanager.yml` | ✅ | ❌ |
| `docker-compose.monitoring.yml` | ✅ | ❌ |
| `healthcheck.sh` (cron) | ✅ | ❌ (cron não instalado) |
| Slack webhook | ✅ (URL placeholder) | ❌ |
| PagerDuty | ✅ (key placeholder) | ❌ |

**Resumo:** 100% da infra de observabilidade foi **escrita** em M20. **0% está em execução em prod.**

---

## 4. MTTR por cenário

### Cenário 1: API retornando 500

| Etapa | Sem obs | Com Prometheus | Com OTEL + Tracing |
|-------|---------|----------------|--------------------|
| Detectar | 5-30min (usuário reclama) | <1min (alerta) | <30s (alerta + log) |
| Localizar | 5-10min (SSH + logs) | <1min (dashboard) | <1min |
| Diagnosticar | 30-60min (achismo) | 5-10min (métricas + logs) | <5min (trace) |
| **Total** | **40-100min** | **6-12min** | **6-7min** |

### Cenário 2: Banco lento

| Etapa | Sem obs | Com Prometheus |
|-------|---------|----------------|
| Detectar | 10-30min | <1min (alerta `pg_stat_activity`) |
| Localizar | 10-15min | <1min |
| Diagnosticar | 30-60min | 5-10min (queries lentas) |
| **Total** | **50-105min** | **7-12min** |

### Cenário 3: Webhook perdido

| Etapa | Sem obs | Com alerta dedicado |
|-------|---------|---------------------|
| Detectar | horas (cliente reclama) | <5min (alerta `mercadopago_webhook_failures`) |
| Localizar | 20-40min | <5min |
| Diagnosticar | 30-60min | 10-20min |
| **Total** | **horas** | **15-30min** |

---

## 5. Plano para observabilidade operacional real

### Curto prazo (esta sprint)

1. Deploy de `/api/health` em prod (5 min)
2. Instalar `scripts/setup_cron.sh` para healthcheck */5min (5 min)
3. Configurar Slack webhook para alertas (15 min)

### Médio prazo (próxima sprint)

4. Provisionar Prometheus + Grafana em VPS secundário (4h)
5. Configurar 5 exporters (PG, Redis, Node, RQ, webhook) (2h)
6. Importar dashboards Grafana prontos (1h)

### Longo prazo

7. Implementar OpenTelemetry tracing (1 sprint)
8. Adicionar correlation_id em todos os requests (3 dias)
9. Logs centralizados (Loki ou ELK) (1 sprint)

---

## 6. Estado pós-FASE 7

> **Observabilidade: NÃO OPERACIONAL.**
>
> **Stack escrita (M20) está completa mas 0% em execução.**
>
> **MTTR médio estimado para incidentes 03:00 da manhã:**
> - Hoje: **40-100min** (sem Prometheus, sem alerta, sem tracing)
> - Pós-curto prazo: **15-30min** (com healthcheck + cron + Slack)
> - Pós-médio prazo: **6-12min** (com Prometheus + Grafana + exporters)
> - Pós-longo prazo: **<5min** (com OTEL + tracing + logs centralizados)
>
> **Recomendação:** MISSÃO 22.8 = provisionar Prometheus + Grafana em ≤ 1 dia.
