# DEPLOY BLOCKERS — MISSÃO 21.5

**Data:** 2026-06-25
**Modo:** EXECUTE
**Objetivo:** separar BLOQUEADORES REAIS (comprovados) de HIPÓTESES (sem evidência) e BACKLOG (conhecidos mas não-críticos)

---

## 1. Definições

| Categoria | Definição | Critério de promoção |
|-----------|-----------|----------------------|
| **🔴 BLOQUEADOR REAL** | Comprovado por curl real contra prod OU por leitura de código + impacto direto em segurança/LGPD/pagamento | Evidência objetiva (HTTP, código, config) |
| **🟠 HIPÓTESE** | Não testado em prod; análise estática ou extrapolação | Precisa teste real ou auditoria adicional |
| **🟡 BACKLOG** | Item conhecido, fora do escopo de "deploy imediato", pode esperar | Documentado em MISSÃO 17 ou similar |

---

## 2. 🔴 BLOQUEADORES REAIS (comprovados)

### BLOQUEADOR #1: P0-05 (CSP) não está em produção

- **Evidência:** `curl -D - https://api.visualsmartflow.com.br/api/csrf-token` retorna CSP com `'unsafe-inline' 'unsafe-eval'`
- **Impacto:** XSS + RCE no navegador se houver endpoint que renderize user input
- **Código correto:** `security_config.py:262-274` (add_security_headers remove unsafe-inline/eval)
- **Causa provável:** deploy parcial / branch errado / servidor de prod em SHA anterior
- **Ação:** deploy do branch atual `feat/clinica-management` ou commit específico que contém o fix

### BLOQUEADOR #2: P0-12 (X-Association-ID) não está em produção

- **Evidência:** `curl -D - https://api.visualsmartflow.com.br/api/csrf-token` retorna `access-control-expose-headers: ... X-Association-ID ...`
- **Impacto:** tenant spoof cross-tenant (atacante envia header e escolhe tenant)
- **Código correto:** `app_cors_livre.py:98` remove X-Association-ID de allow/expose
- **Causa provável:** mesmo deploy parcial do BLOQUEADOR #1

### BLOQUEADOR #3: LGPD art. 18 VI (direito ao esquecimento) NÃO implementado

- **Evidência (código):** `routes/lgpd.py:94-160` `solicitar_direitos_titular()` aceita `tipo_solicitacao='exclusao'` mas **só registra LogAtividade**. Comentário literal: `"Aqui seria implementada a lógica para processar a solicitação..."`
- **Impacto:** paciente pede exclusão, sistema não executa. **Bloqueador legal para produção comercial** (multa LGPD até 2% do faturamento).
- **Ação:** implementar DELETE/anonimização do paciente + tombstone table para impedir restore indevido

### BLOQUEADOR #4: /api/health (M20) não deployado

- **Evidência:** `curl https://api.visualsmartflow.com.br/api/health` → 404
- **Impacto:** sem healthcheck, monitoring/load-balancer não sabem quando parar de mandar tráfego
- **Código correto:** `app_cors_livre.py:168-205`
- **Causa:** deploy parcial

### BLOQUEADOR #5: Pool PG real em prod é DESCONHECIDO

- **Evidência:** código tem default `pool_size=20, max_overflow=40`, mas `DB_POOL_SIZE`/`DB_MAX_OVERFLOW` no `.env.production` do VPS é **NÃO COMPROVADO**
- **Impacto:** se prod tem pool pequeno (5+10 mencionado em M17), sistema trava com >15 requests simultâneas
- **Ação:** acessar `.env.production` no VPS e confirmar valores reais

---

## 3. 🟠 HIPÓTESES (precisam teste/auditoria adicional)

### H1: Isolamento multi-tenant funciona em runtime

- **Código:** ✅ provado (do_orm_execute + before_flush)
- **Runtime:** ⚫ **NÃO TESTADO** em prod com 2 tenants simultâneos
- **Para confirmar:** staging com 2 tenants + queries cross-tenant + asserção de bloqueio

### H2: Performance em 75/100/150/200 usuários

- **Medido em M17:** <50u (Locust 56k requests)
- **Extrapolado em M21:** 75-200u degrada progressivamente
- **Para confirmar:** Locust pesado contra staging

### H3: Webhook MP "fora de ordem" quebra estado

- **Dedup:** ✅ provado (UNIQUE constraint atômico)
- **Ordem:** ⚫ register_webhook_event **não tem sequence_number check**
- **Para confirmar:** teste real com 2 webhooks em ordem trocada

### H4: backup automatizado em prod

- **Cron:** `scripts/setup_cron.sh` foi escrito em M20 mas **NÃO FOI VERIFICADO** se foi instalado no VPS
- **Para confirmar:** `crontab -l` no VPS

### H5: redis storage em prod

- **Código:** ✅ MemoryStorage é fallback explícito (linha 168)
- **Runtime:** ⚫ `RATELIMIT_STORAGE_URL` no VPS é DESCONHECIDO
- **Para confirmar:** env no VPS

### H6: capacidade pós-correção (data_revogacao + pool)

- **Estimativa M21:** 150-200u
- **Para confirmar:** Locust pesado após aplicar correções

---

## 4. 🟡 BACKLOG (conhecidos, não-críticos para hoje)

| Item | Origem | Severidade | Esforço |
|------|--------|------------|---------|
| Webhook DLQ | M17 | P1 | 1 sprint |
| WAL archiving para RPO<5min | M20 | P1 | 1 sprint |
| Healthchecks redundantes (PG/Redis) | M20 | P2 | 2 dias |
| Multi-associação JWT | M18 | P2 | 3 dias |
| 17 P2 de security | M17 | P2 | variável |
| 18 P1 de security | M17 | P1 | variável |
| Tracing OpenTelemetry | M21 | P2 | 1 sprint |
| 6 P0 LGPD | M17 | 🔴 mas herdados | variável |

---

## 5. Respondendo as 5 perguntas

### 1. Existe alguma afirmação das MISSÕES anteriores que estava incorreta?

**SIM — 4 refutadas por evidência objetiva:**

| Afirmação | Missão | Refutada por |
|-----------|--------|--------------|
| "P0-05 CSP deployado" (implícito) | M18 | curl 2026-06-25 mostra unsafe-inline em prod |
| "P0-12 X-Association-ID removido em prod" (implícito) | M18 | curl mostra X-Association-ID em expose-headers |
| "/api/health operacional em prod" | M20 | curl → 404 |
| "Pool PG = 5+10" | M17, M21, FAILOVER | código atual = 20+40 (defaults) |

### 2. Existe alguma conclusão baseada apenas em inferência?

**SIM — várias em M21:**

| Conclusão | Tipo | Problema |
|-----------|------|----------|
| "75-200u degradam progressivamente" | EXTRAPOLAÇÃO | Não medido em nenhum nível acima de 200u com correções |
| "150-200u após correções" | EXTRAPOLAÇÃO | Sem evidência |
| "PG trava em falha" | ANÁLISE ESTÁTICA | Não testado em failover real |
| "Mensagens WhatsApp perdem sem DLQ" | ANÁLISE ESTÁTICA | Não testado |
| "Webhooks duplicam sem dedup MP" | INCORRETA | Dedup EXISTE (UNIQUE constraint) |
| "MTTR ~30min sem Prometheus" | ANÁLISE ESTÁTICA | Não medido |

### 3. Quantos riscos continuam sem evidência objetiva?

**9 riscos** marcados como ⚫ NÃO COMPROVADOS (ver `EVIDENCE_MATRIX.md` Seção 9).

### 4. Quais blockers realmente impedem deploy hoje?

**5 BLOQUEADORES REAIS** (todos com evidência objetiva):

1. **P0-05 (CSP) não deployado em prod** — curl prova
2. **P0-12 (X-Association-ID) não deployado em prod** — curl prova
3. **LGPD art. 18 VI não implementado** — código prova (apenas LogAtividade)
4. **`/api/health` não deployado** — curl prova
5. **Pool PG real em prod desconhecido** — sem `.env.production` acessível

### 5. Depois desta auditoria, qual seria o **único motivo** para NÃO colocar em produção?

> **Os 5 BLOQUEADORES REAIS poderiam ser resolvidos em ≤ 1 sprint** (deploy de M18 + M20 + implementar LGPD-04). Se todos forem resolvidos:
>
> O **único motivo** restante para NÃO colocar em produção é:
>
> **Não há evidência objetiva de que o sistema aguente >5 médicos simultâneos em runtime real.**
>
> - Capacidade medida em M17: <50u sintético
> - Capacidade com médicos reais: **NÃO MEDIDA**
> - Staging inexistente para teste controlado
>
> **Risco real:** se 5 médicos reais usarem o sistema e gerarem padrões de uso diferentes do Locust (ex: GraphQL pesado, queries complexas, uploads simultâneos), o sistema pode degradar de formas não previstas.
>
> **Mitigação recomendada antes de produção:**
> 1. Deploy dos 5 BLOQUEADORES REAIS
> 2. Provisionar staging
> 3. Re-executar M17 contra staging com usuários sintéticos
> 4. Beta de 5 médicos por 2 semanas com telemetria
> 5. Re-auditoria após beta
>
> **Resumo:** sem staging + sem deploy dos P0 + sem LGPD-04, **NÃO HÁ GARANTIA OPERACIONAL**. **O sistema em produção atual está vulnerável a CSP injection, tenant spoof, e não-conformidade LGPD — tudo comprovado por curl e leitura de código.**

---

## 6. Checklist antes de deploy (resumo executivo)

| Item | Como verificar | Status atual |
|------|----------------|--------------|
| CSP sem unsafe-inline/eval em prod | `curl -D - /api/csrf-token \| grep -i csp` | ❌ FAIL |
| X-Association-ID removido de CORS | `curl -D - /api/csrf-token \| grep -i association` | ❌ FAIL |
| `/api/health` retorna 200 | `curl /api/health` | ❌ FAIL |
| LGPD art. 18 VI implementado | `routes/lgpd.py` (DELETE paciente) | ❌ FAIL |
| Pool PG ≥20+40 | `cat .env.production \| grep DB_POOL` | ⚫ DESCONHECIDO |
| Redis storage em prod | `echo $RATELIMIT_STORAGE_URL` no VPS | ⚫ DESCONHECIDO |
| Backup diário rodando | `crontab -l` no VPS | ⚫ DESCONHECIDO |
| Staging provisionado | `docker ps \| grep staging` | ❌ FAIL |
| Multi-tenant testado em runtime | 2 tenants em staging | ⚫ NÃO TESTADO |
| DLQ webhooks | grep em `services/`, `routes/` | ❌ NÃO EXISTE |

**10 itens: 5 FAIL confirmados, 4 DESCONHECIDOS, 1 confirmado (P0 tests).**

---

**MISSÃO 21.5 CONCLUÍDA — Aguardando aprovação humana.**

**Parando conforme instrução. Nenhum commit criado.**
