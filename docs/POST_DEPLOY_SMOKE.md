# POST_DEPLOY_SMOKE — MISSÃO 22.2 (corrigido)

**Data:** 2026-06-25
**Modo:** EXECUTE (somente documentação)
**Origem:** corrigido conforme `RUNBOOK_VALIDATION_REPORT.md` (M22.1)

---

## Como usar

Cada item lista: comando, resultado esperado, tempo máximo, ação se falhar.
Se QUALQUER item falhar, acionar `rollback.sh --env=production` (ver `ROLLBACK_PLAYBOOK.md`).

**REGRA DE OURO:** se o operador ver HTTP **404** num endpoint que deveria existir, **NÃO é bug** se o endpoint estiver marcado como `[NÃO DEPLOYADO]`. É bug se o endpoint estiver marcado como `[EXISTE]`.

---

## 1. Health básico

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| API status | `curl -sk -o /dev/null -w "%{http_code}" https://api.visualsmartflow.com.br/api/status` | 200 | 5s | [EXISTE] `app_cors_livre.py:153` | Diagnosticar backend |
| API redirect | `curl -sk -o /dev/null -w "%{http_code}" https://api.visualsmartflow.com.br/` | 302 → `/api/status` | 5s | [EXISTE] | OK se redirect |
| CSRF token | `curl -sk https://api.visualsmartflow.com.br/api/csrf-token \| jq -r .csrf_token \| wc -c` | ≥64 chars | 5s | [EXISTE] `app_cors_livre.py:122` | App abortou startup |
| Health endpoint | `curl -sk -o /dev/null -w "%{http_code}" https://api.visualsmartflow.com.br/api/health` | 404 | 5s | **[NÃO DEPLOYADO]** código existe em `app_cors_livre.py:168` mas M21 provou que retorna 404 | OK se 404 (ver DEPLOY_BLOCKERS #4) |
| Frontend | `curl -sk -o /dev/null -w "%{http_code}" https://visualsmartflow.com.br/` | 200 | 10s | [EXISTE] | Diagnosticar Traefik |

## 2. Segurança (Headers)

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| CSP sem unsafe-inline (script-src) | `curl -sk -D - https://api.visualsmartflow.com.br/api/csrf-token \| grep -i "content-security-policy" \| grep -v "unsafe-inline"` | 0 matches em `script-src` | 5s | **[NÃO DEPLOYADO]** código existe em `security_config.py:262-274` mas M18/M21 provou unsafe-inline em prod | **DEPLOY FALHOU — re-deploy com M18** |
| X-Association-ID ausente | `curl -sk -D - https://api.visualsmartflow.com.br/api/csrf-token \| grep "access-control-expose-headers" \| grep "X-Association-ID"` | **VAZIO** (0 matches) | 5s | **[NÃO DEPLOYADO]** header NÃO está exposto | **DEPLOY FALHOU — re-deploy com M18** |
| HSTS | `curl -sk -D - https://api.visualsmartflow.com.br/api/status \| grep -i "strict-transport-security"` | ≥1 linha | 5s | [EXISTE] | OK sem (staging) |
| X-Frame-Options | `curl -sk -D - https://api.visualsmartflow.com.br/api/status \| grep -i "x-frame-options"` | SAMEORIGIN ou DENY | 5s | [EXISTE] | Aceitar em prod |

## 3. Login + Cadastro

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| Login válido | `curl -sk -X POST https://api.visualsmartflow.com.br/api/auth/login -H "Content-Type: application/json" -d '{"identifier":"tester.modulos@araos.dev","password":"Tester@2025"}'` | 200 + access_token | 10s | [EXISTE] `routes/auth.py:83` | DB down ou credenciais erradas |
| Login inválido | mesmo com senha errada | 401 | 10s | [EXISTE] | OK se 401 |
| Perfil próprio | `curl -sk https://api.visualsmartflow.com.br/api/auth/profile -H "Authorization: Bearer $TOKEN"` | 200 + JSON | 10s | [EXISTE] `routes/auth.py:84` | Auth quebrada |

## 4. Paciente

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| Listar pacientes | `curl -sk https://api.visualsmartflow.com.br/api/pacientes -H "Authorization: Bearer $TOKEN"` | 200 + array | 10s | [EXISTE] `routes/pacientes.py` | DB query |
| Tenant isolation | 2 tokens de tenants diferentes | associacao_id único em cada | — | [EXISTE] | **CRÍTICO — vazamento** |
| Criar paciente | `curl -sk -X POST .../api/pacientes -d '{"nome":"...","cpf":"..."}'` | 201 | 10s | [EXISTE] | DB write quebrado |

## 5. Consulta

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| Listar consultas | `curl -sk .../api/consultas -H "Authorization: Bearer $TOKEN"` | 200 | 10s | [EXISTE] `routes/consultas.py` | — |
| Criar consulta | POST com payload válido | 201 | 10s | [EXISTE] | Schema mudou? |

## 6. Prescrição

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| Listar prescrições | `GET /api/prescricoes` | 200 | 10s | [EXISTE] `routes/prescricoes.py` | — |
| Criar prescrição | POST com dose + duração | 201 | 10s | [EXISTE] | — |

## 7. Cannabis

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| Listar perfis | `GET /api/cannabis/profiles` | 200 | 10s | [EXISTE] `routes/cannabis.py` | — |
| Tenant isolation | associacao_id consistente | OK | — | [EXISTE] | CRÍTICO |

## 8. Módulo Paciente (substitui /api/nutrologia — não existe)

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| Avaliações gerais | `GET /api/cannabis/profiles/<int:patient_id>` | 200 + perfil | 10s | [EXISTE] | — |
| Anamnese | `GET /api/anamnese` | 200 | 10s | [EXISTE] anamnese bp registrado sem prefix | — |

> **Nota:** `/api/nutrologia` **NÃO EXISTE** no código. Operador **não deve testar este endpoint**. Documentado em M22.1.

## 9. IA Chat

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| Chat simples | `curl -sk -X POST https://api.visualsmartflow.com.br/api/chat-simples -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"pergunta":"olá"}'` | 200 + resposta | 30s | [EXISTE] `routes/ai_chat_simples.py:109` | LLM provider down |
| Tenant check | resposta cita apenas pacientes do tenant | OK | — | [EXISTE] | **CRÍTICO — vazamento de PHI** |

> **Correção M22.1:** rota real é `/api/chat-simples` (não `/api/ai-chat-simples/perguntar`).

## 10. Billing

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| Listar planos | `GET /api/planos` | 200 | 10s | [EXISTE] `routes/planos.py` | — |
| Meu plano | `GET /api/planos/meu-plano` | 200 + plano atual | 10s | [EXISTE] `routes/planos.py` | — |
| Listar faturas | `GET /api/billing/invoices` | 200 + array | 10s | [EXISTE] `routes/billing.py:75` | — |

> **Correções M22.1:**
> - `/api/billing/meu-plano` → **`/api/planos/meu-plano`**
> - `/api/billing/history` → **`/api/billing/invoices`** (única rota de histórico existente)

## 11. Webhook Mercado Pago

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| POST sem assinatura | `curl -X POST .../api/mercadopago/webhook -d '{}'` | 401 ou 400 | 5s | [EXISTE] `routes/mercadopago.py:131` | OK se rejeitado |
| POST com assinatura válida | gerar HMAC e enviar | 200 ou 4xx (nunca 5xx) | 10s | [EXISTE] | **DLQ ausente — log manual** |
| Replay (mesma assinatura) | enviar 2x | 2ª chamada: 200 `idempotent: true` | 10s | [EXISTE] dedup via UNIQUE constraint | Dedup quebrado |

## 12. Webhook Evolution (WhatsApp)

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| POST sem assinatura | `curl -X POST https://api.visualsmartflow.com.br/api/dr-anderson/webhook -d '{}'` | 401/400 | 5s | [EXISTE] `routes/dr_anderson_webhook.py:117` | OK se rejeitado |
| POST assinado | HMAC correto | 200/4xx | 10s | [EXISTE] | — |

> **Correção M22.1:** webhook Evolution é **`/api/dr-anderson/webhook`**, não `/api/evolution/webhook`. O segredo é `DR_ANDERSON_WEBHOOK_SECRET`.

## 13. LGPD

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| Política privacidade | `GET /api/lgpd/politica-privacidade` | 200 + texto | 5s | [EXISTE] `routes/lgpd.py` | — |
| Consentimento | `GET /api/lgpd/consentimento/<paciente_id>` | 200 + flag | 10s | [EXISTE] | — |
| Direito titular | `POST /api/lgpd/direitos-titular/<id>` com `tipo_solicitacao=exclusao` | 201 + protocolo | 10s | [EXISTE rota, NÃO IMPLEMENTADO backend] | ⚠️ **registra log mas NÃO executa exclusão** (ver DEPLOY_BLOCKERS #3) |

## 14. Backup

| Item | Comando | Esperado | Tempo máx | Se falhar |
|------|---------|----------|-----------|-----------|
| Cron instalado | `crontab -l \| grep backup` | linha presente | 1s | Não instalado — executar `./scripts/setup_cron.sh` |
| Backup manual | `./scripts/backup.sh --env=production` | exit 0 + arquivo `/var/backups/siap/db_production_*.sql.gz` | 5min | DB unreachable |

## 15. Health (Monitoring)

| Item | Comando | Esperado | Tempo máx | Status deploy | Se falhar |
|------|---------|----------|-----------|----------------|-----------|
| Health endpoint (app) | `GET /api/health` | 404 (ver §1) | 5s | [NÃO DEPLOYADO] | OK se 404 |
| Backend `/metrics` | (não testar) | — | — | **[NÃO EXISTE]** backend NÃO expõe `/metrics` | Não provisionado |
| Logs estruturados | `docker logs siap-backend --since 5m` | JSON ou formato legível | 5s | [EXISTE] | — |

> **Correção M22.1:** removido teste de `curl /metrics` no backend. Endpoint não existe no código.

## 16. Observabilidade

| Item | Comando | Esperado | Status deploy | Se falhar |
|------|---------|----------|----------------|-----------|
| Prometheus | `curl http://localhost:9090/-/healthy` | **NÃO TESTAR** | **[NÃO DEPLOYADO]** compose existe em `monitoring/` mas não há evidência de execução em prod | Não provisionado (M20) |
| Grafana | `curl http://localhost:3001/api/health` | **NÃO TESTAR** | **[NÃO DEPLOYADO]** | Não provisionado (M20) |
| Healthcheck script | `./scripts/healthcheck.sh --env=production` | stdout com métricas (CPU, RAM, Disk, PG, Redis, Workers) | [EXISTE] `scripts/healthcheck.sh` | Healthcheck falhou |

> **Correção M22.1:** removido teste direto contra Prometheus/Grafana. Substituído por teste ao script `healthcheck.sh` que escreve em `/var/lib/node_exporter/textfile_collector/`.

## 17. Rate Limit

| Item | Comando | Esperado | Tempo máx | Se falhar |
|------|---------|----------|-----------|-----------|
| Limite funcional | 200 requests em 1 min | primeiras 200 OK, próximas 429 | 60s | Rate-limit quebrado |
| Headers X-RateLimit | `curl -D - ... \| grep X-RateLimit` | linhas presentes | 5s | OK |

---

## Resumo de aceite

Para considerar deploy OK, **TODOS** os itens acima devem:

- ✅ Passar (resultado esperado em endpoint [EXISTE])
- ⚠️ Falhar mas com causa conhecida (ex: `/api/health` 404, Prometheus não deployado, CSP unsafe-inline)

**Se QUALQUER item 🔴 falhar inesperadamente:** acionar rollback IMEDIATO.

---

## Mudanças aplicadas nesta versão (M22.2)

| # | Item | Antes (M22) | Depois (M22.2) | Origem |
|---|------|--------------|------------------|--------|
| 1 | §1 Health endpoint | 200 ou 404 | 404 (estado conhecido) | M22.1 |
| 2 | §2 CSP/X-Association-ID | "DEPLOY FALHOU" | "NÃO DEPLOYADO" (estado conhecido) | M22.1 |
| 3 | §3 Perfil próprio | `/api/profissionais/me` | `/api/auth/profile` | M22.1 |
| 4 | §8 Nutrologia | `/api/nutrologia` | `/api/cannabis/profiles/<id>` + `/api/anamnese` | M22.1 |
| 5 | §9 IA Chat | `/api/ai-chat-simples/perguntar` | `/api/chat-simples` | M22.1 |
| 6 | §10 Meu plano | `/api/billing/meu-plano` | `/api/planos/meu-plano` | M22.1 |
| 7 | §10 Histórico | `/api/billing/history` | `/api/billing/invoices` | M22.1 |
| 8 | §12 Webhook Evolution | `/api/evolution/webhook` | `/api/dr-anderson/webhook` | M22.1 |
| 9 | §15 /metrics | curl `/metrics` | removido (não existe) | M22.1 |
| 10 | §16 Prometheus/Grafana | curl localhost | removido (não deployado) | M22.1 |
| 11 | §16 Observabilidade | — | adicionado teste `healthcheck.sh` | M22.1 |