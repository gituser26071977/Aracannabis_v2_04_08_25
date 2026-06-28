# BETA READINESS REPORT — MISSÃO 21 (FASE 8)

**Data:** 2026-06-25
**Modo:** EXECUTE
**Objetivo:** GO/NO-GO técnico para beta por escala (5, 10, 25, 50, 100, 500 médicos)

---

## 1. Sumário executivo

Avaliação por escala baseada em:
- Capacidade real medida em MISSÃO 17 (`RELATORIO_TESTE_CARGA_2026_06.md`)
- P0 de segurança corrigidos em MISSÃO 18 (mas **NÃO deployados em prod** — ver OAT_REPORT.md)
- Capacidade pós-MISSÃO 18 estimada (rate-limit mitigado, mas não há medição nova)
- Bloqueios LGPD remanescentes
- Infraestrutura de release MISSÃO 20 (não provisionada)

---

## 2. Veredicto por escala

| Escala | Veredicto | Justificativa |
|--------|-----------|---------------|
| **5 médicos** | ⚠️ **CONDICIONAL** | Possível APÓS deploy das correções MISSÃO 18 + smoke em prod |
| **10 médicos** | ⚠️ **CONDICIONAL** | Idem; rate-limit 60 req/min/IP ainda quebra com >5 médicos ativos simultâneos |
| **25 médicos** | 🟠 **NÃO** | Sem staging para validar; LGPD-04 ainda não implementado; backup não auditado |
| **50 médicos** | 🔴 **NÃO** | Capacidade real <50u; falhas em série (429 + bug data_revogacao) |
| **100 médicos** | 🔴 **NÃO** | Múltiplos bloqueios críticos |
| **500 médicos** | 🔴 **DEFINITIVAMENTE NÃO** | Exige scaling horizontal (múltiplas réplicas gunicorn, PG cluster, Redis cluster), ainda no backlog |

---

## 3. Justificativa técnica por escala

### 5 médicos — CONDICIONAL

**O que dá:**
- Capacidade real sustenta 5 médicos ativos (medido em M17: <50u).
- 31 testes P0 passando (read-only).
- TLS válido até 2026-09-07.

**O que falta:**
- **Deploy das correções MISSÃO 18** em prod (P0-05, P0-12 estão no código mas NÃO em prod — ver OAT_REPORT.md).
- **Deploy de `/api/health`** (M20) para observabilidade.
- **Smoke em prod** confirmando que frontend carrega com nova CSP.
- **5 médicos aceitarem** nova CSP + ausência de X-Association-ID.
- **Backup PG testado** (RPO atual 24h).

**Se 5 condições forem atendidas:** GO.

### 10 médicos — CONDICIONAL

Tudo de 5 médicos + análise de carga real (Locust 10u simulando médicos + assistentes).

**Risco:** rate-limit 60 req/min/IP quebra quando 10 médicos fazem requisições em rajada. MISSÃO 18 mitigou parcialmente (configurações mais brandas), mas **não foi medido**.

**Recomendação:** rodar mini-load test (10u, 10min) antes de autorizar.

### 25 médicos — NÃO

**Bloqueios:**
- LGPD-04 (art. 18 VI — direito ao esquecimento): paciente não pode solicitar eliminação. Risco legal.
- Bug `data_revogacao` identificado em M17 — quebra 26% das requests em 100u.
- Sem staging para validar.
- Sem DLQ em webhooks.

### 50 médicos — NÃO

**Bloqueios:**
- Capacidade medida: <50u sustentados. Em 50u médicos simultâneos, sistema satura.
- Performance <50u P0 (MISSÃO 17) ainda não corrigido.
- Faltam índices em FKs (identificado em M17, não mitigado).
- Pool PG `pool_size=5 + max_overflow=10` é gargalo (15 conexões max).

### 100 médicos — NÃO

Tudo de 50 + :
- Multi-associação (médicos que atendem em 2+ clínicas): JWT não carrega lista de associations.
- Sem monitoramento Prometheus/Grafana.
- Sem alerting em tempo real.

### 500 médicos — DEFINITIVAMENTE NÃO

Exige:
- Múltiplas réplicas Flask + load balancer (atualmente 1 VPS).
- PostgreSQL com replicação + read replicas.
- Redis cluster.
- CDN para frontend.
- Sentry/observability.
- Time de plantão.
- Tudo isso **não está em MISSÃO 20 nem no backlog próximo**.

**Estimativa:** 3-6 meses de trabalho de SRE + backend.

---

## 4. Bloqueios em comum a todas as escalas

1. **Deploy de M18 não executado em prod** — P0-05/P0-12 estão no código mas prod ainda tem CSP inseguro.
2. **LGPD-04** — sem direito ao esquecimento.
3. **RPO 24h** — backup diário, sem WAL archiving.
4. **Sem staging** — qualquer validação pré-prod é impossível.
5. **Capacity <50u** — sem scaling horizontal.

---

## 5. Recomendação final

### Para MISSÃO 21 autorizar beta de 5 médicos:

**Pré-condições obrigatórias:**
1. ✅ Deploy M18 em prod (corrige P0-05, P0-12, e outros 10 P0)
2. ✅ Deploy de `/api/health` (M20)
3. ✅ Smoke em prod confirmando
4. ✅ Backup PG ativo (cron `backup.sh` instalado)
5. ✅ 5 médicos-piloto avisados das mudanças (CSP, multi-associação)

**Após:** beta de 5 médicos com duração de 2 semanas + re-auditoria.

### Para escalar:

- 5 → 10: requer medição pós-deploy M18
- 10 → 25: requer LGPD-04 + DLQ webhooks
- 25 → 50: requer scaling PG + rate-limit Redis
- 50 → 100: requer WAL archiving + observabilidade
- 100 → 500: requer infra de produção real (múltiplas réplicas, cluster)

---

## 6. Tabela-resumo para decisão

| Escala | Veredicto | Bloqueio #1 | Risco de queda |
|--------|-----------|-------------|----------------|
| 5 | ⚠️ CONDICIONAL | Deploy M18 | Baixo (se smoke OK) |
| 10 | ⚠️ CONDICIONAL | Idem + load test | Médio |
| 25 | 🟠 NÃO | LGPD-04 | Alto |
| 50 | 🔴 NÃO | Capacity + LGPD-04 | Crítico |
| 100 | 🔴 NÃO | Tudo + monitoramento | Crítico |
| 500 | 🔴 NÃO | Infraestrutura inteira | Inviável |
