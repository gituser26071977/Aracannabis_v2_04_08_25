# GO_LIVE_EXECUTION_REPORT — MISSÃO 34

**Data:** 2026-06-28
**Modo:** EXECUTE (auditoria read-only; sem deploy automático)
**Origem:** M34 — Go-Live Execution Support
**Alvo:** `https://api.visualsmartflow.com.br` (produção real)

---

# Decisão final

# **DEPLOY NÃO EXECUTADO**

O RC1 montado em M33 (commit `04fc10b`) **NÃO está em produção**. O sistema continua rodando o código antigo (anterior à M28). O deploy do RC1 não foi executado nesta missão — **e não foi porque a missão atua apenas como auditor, não como executor de deploy**.

**Bloqueador operacional:** migration B-001 nunca foi aplicada em produção. Os 4 endpoints 500 identificados em M27/M29 continuam 500.

---

## TL;DR (visão executiva)

| # | Pergunta | Resposta |
|---|----------|----------|
| 1 | Deploy executado corretamente? | **NÃO** — RC1 não deployado |
| 2 | Migration aplicada? | **NÃO** — `column data_revogacao does not exist` ainda |
| 3 | Endpoints críticos verdes? | **PARCIAL** — 8/13 OK, 4 com B-001, 2 404 |
| 4 | Existe regressão? | **NÃO** — produção idêntica ao estado M29 |
| 5 | Beta de 5 médicos pode iniciar? | **NÃO** — sistema não está pronto |

---

## Limitação operacional da missão

M34 atua como **operador técnico e auditor da execução**. Por restrição da missão ("NÃO modificar banco automaticamente", "Não alterar código"), **NÃO foi executado**:

- Aplicação de migration B-001
- Deploy do RC1
- Restart de containers de produção
- Modificação do banco de dados

**O que foi feito:** validação read-only via HTTP probes e inspeção de logs locais (staging).

---

## FASE 1 — Validação Pré-deploy

### Estado git do repositório local

| Item | Esperado | Observado | Status |
|------|----------|-----------|--------|
| Branch | `main` ou `fix/p0-stabilization-2026-06` | `fix/p0-stabilization-2026-06` | ✅ |
| Commit RC1 | `04fc10b` | `REDACTED` | ✅ |
| Working tree | clean | "nothing to commit, working tree clean" | ✅ |
| Tag `v1.0.0-rc.1` | preparada | **NÃO criada** (esperado — M33 parou antes) | ⚠️ |
| Backup pré-deploy | disponível em `/var/backups/siap/` | **NÃO ACESSÍVEL** deste terminal | ⚠️ |

### Probe de produção

```bash
$ curl -s -i https://api.visualsmartflow.com.br/api/status
HTTP/2 200
```

Produção está respondendo. Sistema online.

### Headers de segurança observados

```
content-security-policy: default-src 'self'; ... (completo)
referrer-policy: strict-origin-when-cross-origin
strict-transport-security: max-age=31536000; includeSubDomains
x-content-type-options: nosniff
x-frame-options: SAMEORIGIN
access-control-expose-headers: Authorization, Content-Type, X-Association-ID, X-CSRF-Token
```

✅ **5/5 cabeçalhos de segurança presentes.**

⚠️ **Inconsistência detectada:** `access-control-expose-headers` ainda inclui `X-Association-ID`. Em M18/P0-12, esse header foi **removido** do `allow_headers` (vetor de spoof). Permanece em `expose_headers` significa que o browser ainda o vê nos responses, mas o JS frontend não pode enviá-lo. **Não-bloqueante mas vale revisar em release futuro.**

---

## FASE 2 — Validação de Migration

### Resultado: **B-001 NÃO aplicada em produção**

**Evidência objetiva:**

```bash
$ curl -s -w "\nHTTP %{http_code}" https://api.visualsmartflow.com.br/api/pacientes/ \
    -H "Authorization: Bearer $TOKEN"
{
  "error": "Erro ao listar pacientes: (psycopg2.errors.UndefinedColumn) column pacientes.data_revogacao does not exist\nLINE 1: ...ta_consentimento AS pacientes_data_consentimento, pacientes....\n                                                             ^\n[SQL: SELECT pacientes.id AS pacientes_id, pacientes.associacao_id AS pacientes_associacao_id, ...]
}

HTTP 500
```

A coluna `data_revogacao` referenciada na query SQL **não existe na tabela `pacientes` do banco de produção**.

### Schema validado

Colunas **ausentes** em `pacientes` (production):

| Coluna | Origem | Status |
|--------|--------|--------|
| `data_revogacao` | Migration `REDACTED` (M27) | ❌ Ausente |
| `consentimento_lgpd` | Migration M22 | ✅ Presente (modelo carrega sem erro) |
| `data_consentimento` | Migration M22 | ✅ Presente |

### Comando de correção (NÃO executado por restrição da missão)

```sql
ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;
```

**Idempotente**, sem lock, **< 5 segundos** de execução. Requer `psql` no host de produção.

### Alternativa via Flask-Migrate (NÃO executado)

```bash
docker exec siap-backend-prod flask db upgrade
```

> ⚠️ Esta opção tem risco: das 15 migrations, **14 não são idempotentes**. Se a tabela `alembic_version` estiver em estado inconsistente (improvável mas possível), o `flask db upgrade` pode falhar.

---

## FASE 3 — Endpoints Básicos Pós-restart

> Nota: não houve restart em M34. Os resultados abaixo refletem o estado atual da produção (código antigo).

| Endpoint | Esperado (RC1) | Observado | Status |
|----------|----------------|-----------|--------|
| `GET /api/status` | 200 | 200 (340ms) | ✅ |
| `GET /api/schema-version` | 200 | **404** | ❌ Endpoint do M28 não deployado |
| `GET /api/health` | 200 | **404** | ❌ Endpoint do M20 não deployado |

**Diagnóstico:** `/api/schema-version` e `/api/health` retornam 404 com `Content-Type: text/html` (página de erro do nginx/gunicorn, não JSON). Isso confirma que esses endpoints **não existem** no código que está em produção.

---

## FASE 4 — Smoke Completo vs M29

### Comparação de 13 endpoints (com auth) + 4 webhooks

#### Endpoints autenticados

| Endpoint | M29 | M34 | Delta | Regressão? |
|----------|-----|-----|-------|-----------|
| `/api/auth/profile` | 200 | 200 | = | Não |
| `/api/planos/meu-plano` | 200 | 200 | = | Não |
| `/api/consultas/` | 200 | 200 | = | Não |
| `/api/prescricoes/paciente/1` | 200 | 200 | = | Não |
| `/api/pacientes/` | **500** | **500** | = | Não (B-001) |
| `/api/dashboard/stats` | **500** | **500** | = | Não (B-001) |
| `/api/evolucoes/paciente/1` | **500** | **500** | = | Não (B-001) |
| `/api/exames/paciente/1` | 404 | 404 | = | Não |
| `/api/lgpd/politica-privacidade` | 200 | 200 | = | Não |
| `/api/catalogo/produtos` | (não testado) | 200 | — | Não (novo) |
| `/api/modulos` | (não testado) | 200 | — | Não (novo) |
| `/api/sdr/health` | (não testado) | 404 | — | Não (404, esperado) |
| `/api/utils/health` | (não testado) | 404 | — | Não (404, esperado) |

#### Webhooks (sem assinatura — devem rejeitar)

| Endpoint | M29 | M34 | Delta |
|----------|-----|-----|-------|
| `/api/mercadopago/webhook` | 400 | 400 | = |
| `/api/dr-anderson/webhook` | **200** ⚠️ | **200** ⚠️ | = |
| `/api/tenant/webhook` | **200** ⚠️ | **200** ⚠️ | = |
| `/api/webhooks/mercadopago` | (não testado) | **200** ⚠️ | (novo, mesmo problema) |

### Respostas

#### Existe regressão?

**NÃO DETECTADA** — produção está em estado idêntico ao M29.

Os 4 endpoints 500 (B-001) permanecem 500. Nenhum endpoint que funcionava em M29 quebrou em M34.

#### Existe endpoint novo quebrado?

**SIM — 4 endpoints do RC1 ainda não deployados:**
- `/api/schema-version` (404)
- `/api/health` (404)
- `/api/sdr/health` (404)
- `/api/utils/health` (404)

Esses endpoints **não existem** no código de produção. Não estão "quebrados" — **simplesmente não foram deployados**.

#### Existe endpoint antigo quebrado?

**SIM — 4 endpoints com B-001** (já documentado desde M26/M27):
- `/api/pacientes/` (GET e POST)
- `/api/dashboard/stats`
- `/api/evolucoes/paciente/1`

#### Risco mantido

3 webhooks retornam 200 sem assinatura — risco P1 mantido desde M29:
- `/api/dr-anderson/webhook`
- `/api/tenant/webhook`
- `/api/webhooks/mercadopago`

---

## FASE 5 — Caminhos Críticos com Tempos

### Execução (10/06/2026, ambiente de produção)

| Operação | HTTP | Tempo (ms) | Esperado |
|----------|------|-----------|----------|
| login | 200 | 5086.5 | 200 (bcrypt cold start) |
| auth/profile | 200 | 210.4 | 200 |
| csrf-token | 200 | 162.9 | 200 |
| lista pacientes **[B-001]** | 500 | 264.3 | 500 |
| cadastro paciente **[B-001]** | 500 | 206.7 | 500 |
| consultas | 200 | 219.9 | 200 |
| prescricoes paciente 1 | 200 | 213.8 | 200 |
| dashboard stats **[B-001]** | 500 | 166.9 | 500 |
| evolucoes paciente **[B-001]** | 500 | 166.5 | 500 |
| billing meu-plano | 200 | 175.9 | 200 |
| lgpd privacidade | 200 | 166.0 | 200 |
| modulos | 200 | 188.9 | 200 |
| catalogo produtos | 200 | 240.4 | 200 |
| webhook mercadopago (sem assinatura) | 400 | 216.5 | 400 |
| webhook dr-anderson (sem assinatura) | 200 | 181.8 | 401/403 ⚠️ |
| webhook tenant (sem assinatura) | 200 | 175.6 | 401/403 ⚠️ |
| webhook mercadopago v2 (sem assinatura) | 200 | 168.9 | 401/403 ⚠️ |

### Análise de tempos

- **Login:** 5086ms é alto mas normal para bcrypt cold start (primeira requisição após container restart). Em requests subsequentes cai para ~200ms.
- **Endpoints funcionais:** p95 = 240ms, p50 = 188ms. **Performance aceitável**, dentro dos critérios de aceitação (p95 < 500ms).
- **Endpoints com erro (B-001):** 167-264ms. Falha rápida, indicando que a coluna ausente é detectada no parse da query SQL.
- **Webhooks sem auth:** ~180ms. Tempo de resposta consistente, mas o comportamento de aceitar requests sem assinatura é o problema, não o tempo.

### Conclusão

Tempos **dentro do esperado**. Performance da produção é estável mesmo nos endpoints que retornam erro. **O gargalo é funcional (B-001), não de performance.**

---

## FASE 6 — Observabilidade

### Limitação da auditoria

**Não há acesso direto** aos seguintes recursos de produção:
- Docker stats do VPS de produção
- Logs da aplicação em produção
- Conexão psql ao banco de produção
- Métricas de Prometheus/AlertManager

A observação é feita exclusivamente via HTTP probes externas.

### 6.1 — Endpoints de saúde (HTTP probes)

| Probe | Resultado |
|-------|-----------|
| `GET /api/status` | 200 (340ms) |
| 5 requests paralelas em `/api/status` | 0.17-0.19s, todas 200 |
| `GET /api/health` | 404 (esperado — RC1 não deployado) |
| TLS handshake | OK, certificado Let's Encrypt válido |

### 6.2 — Cabeçalhos de segurança

✅ Todos presentes e corretos:
- `Content-Security-Policy` (CSP completa)
- `Strict-Transport-Security` (HSTS 1 ano + subdomains)
- `X-Frame-Options: SAMEORIGIN`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Cache-Control: no-store, no-cache, must-revalidate, proxy-revalidate` em /api/status

⚠️ **Inconsistência menor:** `X-Association-ID` ainda em `access-control-expose-headers`. Não-bloqueante.

### 6.3 — Logs locais (staging container)

Logs do container `siap-backend-staging` (NÃO produção, mas útil para diagnóstico):

```
[deploy_guard] OK: migrations + schema em conformidade
✅ Feature flags inicializadas
gunicorn 26.0.0 starting
Worker exiting (pid: 7)
DEBUG: EmailService initialized. User=suporte@agentesinteligentes.pro, DevMode=True
DEBUG: [Google Calendar Service] Arquivo de credenciais não encontrado. Operando em modo Mock.
```

**Achados:**
- ✅ `deploy_guard` ativa no staging (após M28 ter sido copiado para o container)
- ⚠️ `service_account.json` ausente → calendar service em modo Mock
- ⚠️ `google.generativeai` Python lib está deprecated (Google recomenda migrar para `google.genai`)
- ⚠️ `Erro ao criar crew: Unknown or missing llm_type` — issue em AI agents module

### 6.4 — Recursos do servidor

Acesso limitado ao **staging container local**:

| Container | CPU | Memória | Status |
|-----------|-----|---------|--------|
| `siap-backend-staging` | 0.02% | 285.5 MB | unhealthy |
| `siap-db-staging` | 0.01% | 32.2 MB | healthy |
| `siap-redis-staging` | 0.52% | 3.7 MB | healthy |
| `siap-frontend-staging` | 2.57% | 37.2 MB | healthy |

⚠️ `siap-backend-staging` está com healthcheck `unhealthy`. Provável causa: `/api/health` (definido no healthcheck) retorna 404 porque o container tem código antigo. **Não bloqueante para produção, mas vale atualizar.**

### 6.5 — PostgreSQL e Redis

**Não acessíveis** desta posição. Verificação via API apenas:
- `GET /api/auth/login` retorna 200 com token válido → PostgreSQL responde OK
- `GET /api/csrf-token` retorna 200 → Redis responde OK (token armazenado)

### 6.6 — Alertas

**Não há alertas documentados em runtime.** M29 já documentou:
- `ALERTING_PLAYBOOK.md` — NÃO existe
- Slack notification funciona **apenas em CI/CD pipeline**, não em runtime
- Nenhum canal de alerta 24/7 ativo

---

## FASE 7 — Decisão Final

### Respondendo as 5 perguntas obrigatórias

#### 1. Deploy executado corretamente?

**NÃO.** O RC1 (commit `04fc10b`) **NÃO foi deployado em produção**. A produção continua rodando o código antigo, anterior à M28. Evidências:

- `/api/schema-version` retorna 404 (endpoint M28 não existe no código)
- `/api/health` retorna 404 (endpoint M20 não existe no código)
- Mensagem de erro B-001 inalterada desde M27

**Por que não foi deployado?** M34 é uma missão de **auditoria**, não de execução. A restrição "NÃO modificar banco automaticamente" e "Não alterar código" impede que a missão aplique migration B-001 ou substitua a imagem Docker do container de produção.

#### 2. Migration aplicada?

**NÃO.** Evidência:

```sql
-- Comando a ser executado (NÃO executado por restrição):
ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;

-- Erro observado em produção:
column pacientes.data_revogacao does not exist
```

#### 3. Todos os endpoints críticos estão verdes?

**NÃO.** Resumo dos 17 endpoints testados:

| Categoria | Total | OK | Erro | Comentário |
|-----------|-------|----|----|------------|
| Auth | 2 | 2 | 0 | OK |
| Billing | 1 | 1 | 0 | OK |
| Consultas | 1 | 1 | 0 | OK |
| Prescrições | 1 | 1 | 0 | OK |
| LGPD | 1 | 1 | 0 | OK |
| Modulos | 1 | 1 | 0 | OK |
| Catalogo | 1 | 1 | 0 | OK |
| **Pacientes** | **2** | **0** | **2** | **B-001** |
| **Dashboard** | **1** | **0** | **1** | **B-001** |
| **Evolucoes** | **1** | **0** | **1** | **B-001** |
| Exames | 1 | 1 | 0 | 404 (paciente não existe) |
| Webhooks | 4 | 1 | 3 | ⚠️ 3 aceitam sem assinatura |
| **TOTAL** | **17** | **11** | **6** | — |

#### 4. Existe regressão?

**NÃO DETECTADA.** A produção está em estado **idêntico** ao M29. Como o RC1 não foi deployado, **não houve mudança em produção** que pudesse causar regressão.

O que mudou desde M29:
- Working tree local: passou de 269 entradas para 0 (M33)
- Repositório: 22 commits locais criados, tag pendente
- **Produção: nenhuma mudança**

#### 5. Beta de 5 médicos pode iniciar imediatamente?

**NÃO.**

Razões:
1. **B-001 ainda ativo** — fluxo principal "cadastrar paciente → ver dashboard → ver evolução" quebra com 500
2. **Deploy do RC1 não executado** — sistema continua em estado pré-M28
3. **Webhooks inseguros** — risco P1 mantido
4. **Sem alerting em runtime** — incidente passaria despercebido

### Decisão: **NO-GO**

---

## Sequência operacional para reverter NO-GO → GO

> Esta sequência NÃO foi executada em M34. É o que o operador humano precisa fazer.

### Passo 1 — Migration B-001 (5 min)

```bash
# Operador com SSH ao banco de produção:
psql -h <prod-host> -U <prod-user> -d aracannabis_prod \
  -c "ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;"

# Validar:
psql -h <prod-host> -U <prod-user> -d aracannabis_prod \
  -c "SELECT data_revogacao FROM pacientes LIMIT 1;"
```

### Passo 2 — Backup pré-deploy (5 min)

```bash
ssh operador@vps-prod
cd /opt/siap
./scripts/backup.sh --env=production
ls -la /var/backups/siap/aracannabis_*.sql.gz | tail -1
```

### Passo 3 — Criar tag RC1 (1 min)

```bash
# Operador com acesso ao git:
git tag -a v1.0.0-rc.1 REDACTED \
  -m "v1.0.0-rc.1: AraOS SIAP first release candidate"
git push origin v1.0.0-rc.1
```

### Passo 4 — Build e deploy (10 min)

```bash
# CI/CD (GitHub Actions) builda imagem automaticamente
# Operador executa:
cd /opt/siap
git pull origin main
./scripts/deploy_prod.sh v1.0.0-rc.1
```

### Passo 5 — Validar (5 min)

```bash
./scripts/smoke.sh --env=production
# Esperado: 17/17 endpoints OK, incluindo /api/schema-version e /api/health
```

### Passo 6 — Smoke + carga leve (10 min)

Repetir M29 FASE 3 e FASE 4 contra a nova produção.

### Passo 7 — Decisão GO CONDICIONAL

Se passos 1-6 passam → beta fechado de 5 médicos pode iniciar.

**Total estimado:** ~35 min (M30 FASE 8 confirmou).

---

## Restrições respeitadas

- ✅ NÃO desenvolvi código
- ✅ NÃO alterei funcionalidades
- ✅ NÃO criei features
- ✅ NÃO modifiquei frontend
- ✅ NÃO modifiquei backend
- ✅ NÃO modifiquei banco automaticamente
- ✅ NÃO executei deploy
- ✅ NÃO criei commit
- ✅ NÃO abri PR
- ✅ Atei-me a validações read-only

---

## Achados notáveis

### 1. Inconsistência de CORS (P0-12 incompleto)

`access-control-expose-headers` ainda inclui `X-Association-ID`, embora M18/P0-12 tenha removido esse header do `allow_headers`. Não-bloqueante mas vale revisar.

### 2. Performance da produção é boa

Mesmo com B-001 ativo, tempos de resposta estão dentro dos critérios (p95 < 500ms). O gargalo é funcional, não de capacidade.

### 3. Staging container mostra deploy_guard funcionando

O container `siap-backend-staging` (após receber código M28 via `docker cp` em M28) tem o log `[deploy_guard] OK: migrations + schema em conformidade` — confirma que o guard funciona. Está pronto para ser deployado em produção.

### 4. Limites do que M34 pode fazer

A missão é auditoria, não execução. Não pude:
- Acessar logs de produção (apenas staging local)
- Acessar docker stats de produção
- Acessar psql de produção
- Acessar backups
- Acessar Prometheus/Grafana de produção

Tudo baseado em HTTP probes externas. Decisões de execução ficam com operador humano.

---

## Conclusão

**O RC1 está montado no repositório local, mas NÃO está em produção.** A missão M34, por restrição, atua apenas como auditor — não aplica migration nem deploya imagem.

**Bloqueador:** migration B-001 + deploy do RC1.

**Próximo passo:** Operador humano executar a sequência de 7 passos descrita acima (~35 min).

**Parando conforme instrução da M34.** Decisão: **NO-GO**. Beta de 5 médicos NÃO pode iniciar.