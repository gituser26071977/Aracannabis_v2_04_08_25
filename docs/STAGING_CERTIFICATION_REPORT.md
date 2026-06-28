# STAGING CERTIFICATION REPORT — MISSÃO 19

**Data:** 2026-06-25
**Modo:** EXECUTE (somente validação; nenhuma correção, nenhuma funcionalidade nova, nenhum commit)
**Objetivo:** certificar AraOS para beta fechado (5 médicos reais)
**Resultado:** **NÃO CERTIFICADO** — staging server não existe neste ambiente; certificação não pode ser executada conforme protocolo

---

## 1. Resumo executivo

A MISSÃO 19 solicitava a implantação da versão atual em **ambiente de staging** e a execução de **30 fluxos críticos** (Login, Cadastro, Cannabis, Exames, Billing, MercadoPago, Webhook, Backup, Restore, Rate Limit, JWT, CSRF, CSP, Tenant Isolation, LGPD, RQ, Redis, PostgreSQL, etc.) com registro de **tempo, screenshots, logs, stack traces, HTTP, CPU, RAM, Redis, workers, banco**.

**A missão NÃO PÔDE ser executada integralmente neste ambiente** pelos motivos documentados na Seção 2. Foi feita **validação read-only complementar** (Seção 3) e **mapeamento do que falta** para tornar a certificação executável (Seção 4).

> **Veredito:** AraOS **NÃO está certificado** para beta fechado enquanto não houver (a) ambiente de staging provisionado, (b) ferramenta de E2E com screenshots, (c) janela de manutenção autorizada e (d) suite de smoke automatizada. Os 31 testes P0 da MISSÃO 18 continuam passando, mas **isso não substitui uma certificação**.

---

## 2. Por que a missão não foi executada integralmente

### 2.1 Sem ambiente de staging

```
$ grep -E "(STAGING|staging)" .env.example docker-compose*.yml
(nenhum match)
```

| Ambiente | Status | URL |
|----------|--------|-----|
| **dev local** | existe | `localhost:5002` |
| **prod** | existe (ativo) | `api.visualsmartflow.com.br` |
| **staging** | **NÃO existe** | — |

Não há manifesto `docker-compose.staging.yml`, não há `STAGING_*` env vars, não há DNS `staging.visualsmartflow.com.br`. Implantar em prod para "certificar" seria equivalente a testar em prod — fora do escopo da missão e arriscado.

### 2.2 Sem ferramenta de E2E com screenshots

A missão exige **screenshots** dos 30 fluxos. Python Playwright **não está instalado** no venv de testes:

```
.venv-test/bin/python -c "import playwright"
ModuleNotFoundError: No module named 'playwright'
```

Chrome (`/usr/bin/google-chrome`) está disponível, mas sem Python wrapper; instalar Playwright + browser headless viola o princípio "não criar código novo / não instalar" e ainda assim não há staging para apontar.

### 2.3 Sem instrumentação de CPU/RAM/Redis/Workers já em produção

A missão exige monitoramento contínuo durante os 30 fluxos. Não há agente de métricas (Prometheus/Grafana/Datadog) acessível daqui; capturar CPU/RAM/Redis/Workers exigiria acesso SSH ao VPS `147.93.33.253`, que **não foi fornecido nesta sessão**.

### 2.4 Sem janela de manutenção autorizada

Mesmo se houvesse staging, **derrubar Redis/PostgreSQL para teste de chaos**, **executar restore de backup** e **rodar carga pesada** exigem janela autorizada pelo operador do VPS. Nenhuma autorização foi concedida nesta sessão.

### 2.5 Política auto-mode

O classificador de modo bloqueia automaticamente:
- Operações que possam afetar produção compartilhada
- Deploy em ambientes sem janela autorizada
- Instalação de binários pesados

A MISSÃO 19, como descrita, requer **todas essas operações**.

---

## 3. Validação read-only executada (substituta limitada)

Em conformidade com "não corrigir nada / não criar código / não commitar", fiz **apenas leituras** que produzem evidência objetiva:

### 3.1 Suíte de testes P0 (MISSÃO 18)

```
.venv-test/bin/python -m pytest tests/security/test_p0_remediation_m18.py -q
…
============================== 31 passed, 1 warning in 3.01s ==============================
```

**Cobertura:** 12 P0 de segurança (P0-01 a P0-12) + 1 sanity de compilação.

### 3.2 Sanity estático de sintaxe

```
Files checked: 543 Python files
Syntax errors: 0
```

(Iteração completa do projeto, excluindo `.venv*`, `node_modules`, `.git`, `Backup`.)

### 3.3 HTTP probe de prod (read-only)

```
GET https://api.visualsmartflow.com.br/api/status → 200 (1.90s)
GET https://api.visualsmartflow.com.br/             → 302 (0.27s)
```

Serviço responde, latência normal para endpoint público.

### 3.4 Capacidade real (herdada de MISSÃO 17)

Fonte: `RELATORIO_TESTE_CARGA_2026_06.md` (56.323 requests em prod):

| Cenário | Usuários | Falhas | p95 |
|---------|----------|--------|-----|
| baseline | 50 | 63% | 170ms |
| peak | 200 | 84% | 230ms |
| soak | 100 | 74% | 180ms |

**Conclusão herdada:** sustenta **< 50 usuários ativos**; gargalo em rate limiter per-IP + bug `data_revogacao`.

---

## 4. Status individual dos 30 fluxos solicitados

| # | Fluxo | Status de certificação | Bloqueio |
|---|-------|------------------------|----------|
| 1 | Login | ⚠️ Validado em teste unitário (`test_login_route_source_compiles`) | Sem UI; sem staging |
| 2 | Logout | ❌ Não testado | Sem UI; sem staging |
| 3 | Cadastro | ❌ Não testado | Sem staging + sem E2E |
| 4 | Reset de senha | ❌ Não testado | Requer e-mail real / MailHog |
| 5 | Troca de senha | ❌ Não testado | Requer staging |
| 6 | Cadastro de paciente | ❌ Não testado | Requer staging |
| 7 | Editar paciente | ❌ Não testado | Requer staging |
| 8 | Excluir paciente | ❌ Não testado | Requer staging + LGPD |
| 9 | Consulta | ❌ Não testado | Requer staging |
| 10 | Evolução | ❌ Não testado | Requer staging |
| 11 | Prescrição | ❌ Não testado | Requer staging |
| 12 | Cannabis | ❌ Não testado | Requer staging |
| 13 | Exames | ⚠️ Path traversal validado (P0-01/P0-02 tests); UI não | Sem staging |
| 14 | Upload | ⚠️ Path traversal validado (P0-01/P0-02 tests); UI não | Sem staging |
| 15 | Download | ⚠️ Path traversal validado (P0-01/P0-02 tests); UI não | Sem staging |
| 16 | IA Chat | ⚠️ Skip-tenant validated (P0-09 test); integração não | Requer staging + LLM |
| 17 | Billing | ❌ Não testado | Requer staging + MP sandbox |
| 18 | MercadoPago | ⚠️ Webhook hardening validado (P0-11 test); integração não | Requer staging + sandbox |
| 19 | Webhook | ⚠️ compare_digest + hmac validated (P0-11 tests); sem teste E2E | Requer staging + sandbox |
| 20 | Backup | ❌ Não testado | Requer acesso SSH ao VPS |
| 21 | Restore | ❌ Não testado | Requer janela de manutenção |
| 22 | Rate Limit | ✅ Validado em `RELATORIO_TESTE_CARGA_2026_06.md` (60 req/min/IP) | Gargalo documentado |
| 23 | JWT | ⚠️ Validação estática (path / decode); sem integração E2E | Requer staging |
| 24 | CSRF | ✅ P0-06 test passing (`csrf_protect_uses_compare_digest`, `REDACTED`) | Cobertura parcial |
| 25 | CSP | ✅ P0-05 test passing (`add_security_headers_no_unsafe`, `csp_has_object_src_none`) | Cobertura parcial |
| 26 | Tenant Isolation | ✅ P0-08 + P0-12 tests passing (`before_flush`, `tenant_from_jwt_only`) | Cobertura parcial |
| 27 | LGPD | ❌ Não testado | LGPD-04 (art. 18 VI) **não implementado** — fluxo INEXISTENTE |
| 28 | Fila RQ | ❌ Não testado | Requer staging + Redis |
| 29 | Redis | ❌ Não testado | Requer acesso a redis-cli no VPS |
| 30 | PostgreSQL | ❌ Não testado | Requer psql no VPS |

**Resumo:** **0 fluxos totalmente certificados**, **10 com cobertura parcial estática**, **20 sem cobertura**.

---

## 5. Respondendo as 6 perguntas obrigatórias

### Pergunta 1: Existe algum bug bloqueador?

**SIM — bloqueadores remanescentes da auditoria:**

1. 🔴 **LGPD-04** (direito ao esquecimento, art. 18, VI): endpoint não existe. Bloqueador legal para produção comercial.
2. 🔴 **Capacidade < 50u**: rate limiter global quebra o serviço com mais de 50 usuários simultâneos.
3. 🔴 **Staging inexistente**: impede QUALQUER validação pré-prod.
4. 🟠 **Webhook DLQ ausente**: pagamentos podem ser perdidos.
5. 🟠 **Backup sem restore testado**: RPO/RTO indefinidos.

### Pergunta 2: Existe alguma regressão?

**DESCONHECIDO** — sem suite de regressão E2E. Os 31 testes P0 cobrem apenas hardening de segurança, não fluxos funcionais. **Não há evidência para afirmar nem refutar regressões funcionais.**

### Pergunta 3: Existe perda de dados?

**DESCONHECIDO** — fluxo "Restore" (item 21 dos 30) **não foi testado** porque exige ambiente de staging + backup + janela. Em prod:
- Backup automatizado existe? **Status desconhecido** (não auditado nesta missão).
- Restore testado? **NÃO** — evidência herdada da MISSÃO 17 indica "Backup auditado e restore testado" como P1 não corrigido.

### Pergunta 4: Existe vazamento entre tenants?

**PARCIALMENTE COBERTO** — P0-08 (before_flush listener) e P0-12 (tenant do JWT only) passaram nos testes unitários. Isso **bloqueia** vazamento via INSERT/UPDATE e via spoof de header. Mas:

- ❌ **Vazamento via SELECT cross-tenant** (queries que usam `skip_tenant=True`) **não foi testado dinamicamente** em staging.
- ❌ **Vazamento via cache Redis** entre tenants **não foi testado**.
- ❌ **Vazamento via logs estruturados** (PII de tenant A em log de tenant B) **não foi testado**.

**Recomendação:** criar suite Playwright com 2 tenants concorrentes validando isolamento de leitura antes de beta.

### Pergunta 5: Existe falha de UX crítica?

**DESCONHECIDO** — não há screenshots, não há walk-through manual, não há teste de usabilidade.

**Riscos prováveis não testados:**
- CSP sem `unsafe-inline` pode bloquear scripts inline não detectados (P0-05). Requer smoke em prod com browser real.
- Login lento (CSP nonce por request adiciona ~5ms — não medido).
- Erros 500 do bug `data_revogacao` (já identificado em MISSÃO 17) podem quebrar UI de pacientes com dados revogados.

### Pergunta 6: O sistema pode receber 5 médicos reais?

**NÃO CERTIFICADO — recomendação condicional alinhada com MISSÃO 18:**

| Condição | Estado | Origem |
|----------|--------|--------|
| ✅ P0 blockers de segurança eliminados | OK | MISSÃO 18 |
| ⚠️ Smoke em prod (CSP, login, dashboard) | NÃO executado | MISSÃO 19 sem staging |
| ⚠️ `JWT_SECRET_KEY` ≥32 chars em prod | Não verificado nesta missão | — |
| ⚠️ `CSRF_TOKEN` setado em prod | Não verificado nesta missão | — |
| ⚠️ Backup PG ativo + restore testado | NÃO verificado | MISSÃO 19 sem staging |
| ⚠️ 5 médicos sem dependência de `X-Association-ID` | Não confirmado com equipe | — |
| ❌ Staging certificado com 30 fluxos | **FALTA** | MISSÃO 19 |

**Resposta direta:** **NÃO** — sem staging certificado, abrir beta com 5 médicos é **apostar**. A recomendação de MISSÃO 18 ("beta fechado condicional") **se mantém**, mas **sem a execução de MISSÃO 19, nenhuma das 7 condições foi verificada**.

---

## 6. Bloqueios para executar MISSÃO 19 corretamente

Para que a MISSÃO 19 possa ser executada **de fato** (não apenas reportada como "não executada"), é necessário:

### 6.1 Provisionar staging

1. Criar `docker-compose.staging.yml` (cópia de `docker-compose.prod.yml` com portas/dir diferentes)
2. Provisionar VPS ou subdomínio `staging.visualsmartflow.com.br`
3. Criar banco PG de staging (separado do prod)
4. Criar Redis de staging (separado do prod)
5. Configurar DNS / Traefik
6. Variáveis `STAGING_*` em `.env.staging`
7. Secrets **diferentes** do prod (não reutilizar)

### 6.2 Instalar Playwright + escrever E2E

```bash
.venv-test/bin/pip install playwright pytest-playwright
.venv-test/bin/playwright install chromium
```

Criar `tests/e2e/test_30_flows.py` com:
- 1 test por fluxo da lista
- Screenshots a cada passo (já é built-in no Playwright)
- Logs estruturados
- Asserts em HTTP status + conteúdo

### 6.3 Instrumentação

- Prometheus + Grafana (CPU/RAM/Redis/Workers)
- Acesso `ssh deploy@staging-vps` para sysadmin
- Sentry ou similar para stack traces
- Logger estruturado (JSON) em todos endpoints

### 6.4 Janela autorizada

- Bloquear deploys em prod por 4h durante execução
- Permitir derrubada de Redis/PG para chaos
- Permitir carga pesada (200u+)

### 6.5 Equipe

- 1 SRE/DevOps para staging + monitoramento
- 1 QA para walk-through manual
- 1 médico-piloto disponível para validação de UX

**Estimativa:** 1 sprint de 2 semanas para deixar a certificação executável.

---

## 7. Estado pós-MISSÃO 19

> **Sistema:** ainda não certificado para beta.
>
> **Pronto para:**
> - ✅ MISSÃO 20 (provisionamento de staging) — pré-requisito para certificação
> - ✅ MISSÃO 19.1 (instalar Playwright + escrever E2E skeleton)
> - ✅ Manter 31/31 testes P0 passando
>
> **NÃO pronto para:**
> - ❌ Beta com 5 médicos (condições não verificadas)
> - ❌ Abertura comercial
> - ❌ Considerar Release Candidate
>
> **Bloqueios remanescentes (do backlog MISSÃO 17 + esta missão):**
> 1. **Staging server** inexistente
> 2. **E2E framework** não instalado
> 3. **Instrumentação** (Prometheus/Grafana) ausente
> 4. **LGPD-04** (art. 18 VI) ainda não implementado
> 5. **Backup/restore** audit
> 6. **Capacity < 50u**
>
> **Recomendação operacional:**
> 1. MISSÃO 20 — Provisionar staging
> 2. MISSÃO 21 — Instalar Playwright + esqueleto E2E
> 3. MISSÃO 22 — LGPD-04 (direito ao esquecimento)
> 4. MISSÃO 23 — Re-executar MISSÃO 19 com staging pronto

---

## 8. Itens NÃO executados nesta missão (e por quê)

Em conformidade com o modo EXECUTE + auto-mode:

| Item | Razão |
|------|-------|
| Deploy em staging | Staging não existe |
| 30 fluxos E2E | Sem staging + sem Playwright |
| Screenshots | Sem Playwright |
| Captura CPU/RAM | Sem agente de métricas + sem SSH ao VPS |
| Restore de backup | Sem staging + sem janela |
| Chaos test | Mesma razão |
| Load test pesado | Mesma razão |

---

## 9. Inventário de artefatos produzidos nesta missão

| Arquivo | Tipo | Status |
|---------|------|--------|
| `docs/STAGING_CERTIFICATION_REPORT.md` | Relatório MISSÃO 19 | ✅ este arquivo (NÃO CERTIFICADO) |
| `tests/security/test_p0_remediation_m18.py` | Suite P0 | ✅ 31/31 passando (re-confirmado) |
| `docs/RELEASE_CANDIDATE_REPORT.md` | Relatório MISSÃO 18.5 | ✅ (herdado) |

---

**MISSÃO 19 CONCLUÍDA — Aguardando aprovação humana.**

**Recomendação final:** autorizar **MISSÃO 20 (Provisionar Staging)** como pré-requisito absoluto antes de qualquer nova tentativa de certificação. Sem staging, MISSÃO 19 não pode ser executada; sem certificação, beta com 5 médicos é aposta, não engenharia.
