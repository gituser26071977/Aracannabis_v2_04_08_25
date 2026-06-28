# OAT REPORT — MISSÃO 21 (FASE 1)

**Data:** 2026-06-25
**Modo:** EXECUTE (somente validação; somente testes/scripts/documentação)
**Objetivo:** certificar se o AraOS suporta operação real de 5 médicos amanhã
**Veredito:** **NÃO CERTIFICÁVEL como "testes reais"** — staging não existe; evidência coletada por read-only probing em prod

---

## 1. Sumário executivo

A FASE 1 da MISSÃO 21 pedia **execução real** do fluxo completo (Login → Cadastro → Paciente → LGPD → Consulta → Evolução → Exames → Prescrição → Billing → MercadoPago → Webhook → WhatsApp → IA → Logout) com validação de HTTP, logs, erros, rollback, consistência de banco, multi-tenant e auditoria.

**Esta fase NÃO pôde ser executada como "testes reais"** porque:

1. **Staging não existe** (ainda pendente das MISSÕES 19 e 20).
2. **Credenciais de prod** não foram fornecidas.
3. **Sem janela** para testes que criem pacientes/consultas reais.
4. **Multi-tenant** exige 2 tenants configurados simultaneamente.

Foi feita **coleta read-only de evidência observacional** contra `api.visualsmartflow.com.br` para validar comportamento público do sistema, complementada pela suíte de 31 testes P0 da MISSÃO 18.

---

## 2. Evidência read-only coletada

### 2.1 Probes HTTP em prod (sem mutação)

| Endpoint | HTTP | Latência | Observação |
|----------|------|----------|------------|
| `GET /` | 302 | 270ms | redirect para `/api/status` |
| `GET /api` | 200 | — | raiz da API OK |
| `GET /api/status` | 200 | **175-300ms** | status público OK |
| `GET /api/csrf-token` | 200 | — | retorna token 64-char hex |
| `GET /api/health` | **404** | — | **endpoint novo da M20 não deployado** |
| `POST /api/auth/login` (sem body) | 405 | — | método não permitido (esperado) |

### 2.2 Latência observada (5 amostras em /api/status)

```
amostra 1: 297ms
amostra 2: 175ms
amostra 3: 178ms
amostra 4: 174ms
amostra 5: 172ms
```

**p50 ≈ 178ms, p95 ≈ 297ms** em horário comercial.

### 2.3 Headers de segurança observados em prod

```
access-control-expose-headers: Authorization, Content-Type, X-Association-ID, X-CSRF-Token
content-security-policy: default-src 'self';
  script-src 'self' 'unsafe-inline' 'unsafe-eval';   ← ⚠️ P0-05 NÃO ESTÁ EM PROD
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: blob: https:;
  ...
strict-transport-security: max-age=31536000; includeSubDomains
x-content-type-options: nosniff
x-frame-options: SAMEORIGIN
```

### 2.4 Achado crítico #1: P0-05 e P0-12 NÃO deployados em prod

> **A correção P0-05 (CSP sem unsafe-inline/eval) e P0-12 (remoção do X-Association-ID) estão no código mas NÃO estão em produção.**

Evidências:
- CSP inclui `'unsafe-inline'` e `'unsafe-eval'` → P0-05 não aplicado.
- `X-Association-ID` aparece em `access-control-expose-headers` → P0-12 não aplicado.

> **Significância:** os testes P0 da MISSÃO 18 validam o **código**, não o que está em produção. **O sistema em produção ainda é vulnerável a CSP injection e X-Association-ID spoof cross-tenant**.

### 2.5 TLS / DNS

| Item | Valor |
|------|-------|
| TLS válido | sim (Let's Encrypt, expira 2026-09-07) |
| Subject | `CN=api.visualsmartflow.com.br` |
| DNS prod | `147.93.33.253` |
| Frontend | `visualsmartflow.com.br` e `araos.visualsmartflow.com.br` → 200 |

### 2.6 Regressão P0 (read-only)

```
.venv-test/bin/python -m pytest tests/security/test_p0_remediation_m18.py
→ 31 passed, 1 warning in 3.23s
```

---

## 3. Status dos 14 fluxos

| # | Fluxo | Status de execução | Bloqueio |
|---|-------|--------------------|----------|
| 1 | Login | ⚠️ Validado só o endpoint público; login real requer credenciais | Credenciais não fornecidas |
| 2 | Cadastro médico | ❌ Não executado | Staging inexistente |
| 3 | Cadastro paciente | ❌ Não executado | Staging + consentimento LGPD |
| 4 | Consentimento LGPD | ❌ Não executado | LGPD-04 (art. 18 VI) ainda não implementado |
| 5 | Consulta | ❌ Não executado | Staging |
| 6 | Evolução | ❌ Não executado | Staging |
| 7 | Exames | ⚠️ Path traversal validado em testes; UI não | Staging |
| 8 | Prescrição | ❌ Não executado | Staging |
| 9 | Billing | ❌ Não executado | Staging + MP sandbox |
| 10 | MercadoPago | ⚠️ Webhook signature validada; checkout real não | Staging + MP sandbox |
| 11 | Webhook | ⚠️ hmac.compare_digest validada em código; integração não | Staging + sandbox |
| 12 | WhatsApp | ❌ Não testado | Staging + Evolution API |
| 13 | IA | ❌ Não testado | Staging + LLM (Gemini/Crew) |
| 14 | Logout | ❌ Não testado | Staging |

**0 fluxos totalmente certificados via teste real.**
**5 fluxos com cobertura parcial estática.**
**9 fluxos sem cobertura.**

---

## 4. Validações que **NÃO PUDERAM** ser feitas

| Validação pedida | Por quê não foi feita |
|------------------|------------------------|
| Status HTTP de mutações | Sem credenciais para criar recursos em prod |
| Logs de aplicação | Sem acesso ao log do container em prod |
| Erros 5xx | Sem carga para induzir erros |
| Rollback | Sem deploy recente para reverter |
| Consistência de banco | Sem credenciais de leitura direta |
| Multi-tenant (2 tenants simultâneos) | Staging inexistente |
| Auditoria (logs de ação) | Sem fluxo executado |

---

## 5. Respondendo as 6 perguntas da MISSÃO 21 (este relatório foca FASE 1)

> As respostas detalhadas estão em `docs/BETA_READINESS_REPORT.md` (FASE 8). Resumo:

1. **5 médicos amanhã?** NÃO sem deploy prévio de M18 + novo `/api/health`.
2. **Usuários suportados?** <50 (herdado de M17).
3. **Risco crítico restante?** SIM — P0-05/P0-12 não deployados em prod.
4. **Perda de dados?** SIM em falha de banco (RPO 24h).
5. **Maior risco?** Deploy não executado de M18 (P0 não estão em prod).
6. **Beta aprovado?** NÃO.

---

## 6. Estado pós-FASE 1

> **Sistema em produção:** NÃO tem as correções P0-05/P0-12 deployadas. Código está pronto; deploy está pendente.
>
> **Próximo passo:** deploy dos artefatos da MISSÃO 18 + MISSÃO 20 + Playwright/Lighthouse/DR da MISSÃO 21 em staging (que precisa ser provisionado).
>
> **Recomendação operacional:**
> 1. Provisionar staging (MISSÃO 22 — sub-missão)
> 2. Deploy de P0 + /api/health
> 3. Re-executar FASE 1 da MISSÃO 21 contra staging
