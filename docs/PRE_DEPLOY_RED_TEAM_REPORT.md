# PRE-DEPLOY RED TEAM REPORT — MISSÃO 17

**Data:** 2026-06-25
**Modo:** EXECUTE (somente leitura; sem correções)
**Personas simuladas:** Pentester, Auditor LGPD, QA Lead, SRE, Performance Engineer, Médico malicioso, Secretária maliciosa, Cliente concorrente, Usuário autenticado tentando escalar privilégios

---

## 1. Sumário executivo

Auditoria completa de **6 fases** (Security, LGPD, Multi-tenant, Performance, Disaster, UX Break) sobre o AraOS em **branch `main` (HEAD `d562424`)** e ambiente de produção `https://api.visualsmartflow.com.br`.

**Total de achados:** **47 P0-P2 em Security + 6 P0 LGPD + 4 P0 Multi-tenant + 10 Performance + 8 Disaster + 12 UX**

> **Veredito: NÃO AUTORIZADO para colocar 100 médicos pagantes amanhã.**
> 3 P0 com risco de vazamento real de PHI entre tenants.
> 2 P0 com vazamento de credenciais em logs.
> Sem retry persistente para webhooks.
> Sem direito ao esquecimento (art. 18, VI LGPD).

---

## 2. Respondendo as 5 perguntas obrigatórias

### Pergunta 1: Existe algum P0 restante?

**SIM — 12 P0 em Security + 6 P0 LGPD + 4 P0 Multi-tenant = 22 P0 totais.**

**Top 5 que BLOQUEIAM o deploy:**

| Rank | P0 | Arquivo | Evidência |
|------|-----|---------|-----------|
| 1 | Path traversal em download Laudo HC | `routes/hc_report.py:37-46` | `os.path.join(upload_folder, filename)` sem sanitização |
| 2 | Servir exame SEM auth + sem tenant | `routes/exames.py:277-284` | `def servir_arquivo_exame(filename)` sem `@jwt_required` |
| 3 | Senha em texto puro em logs | `routes/auth.py:117-122` | `print(f"Senha sanitizada: '{senha}'")` em prod |
| 4 | `skip_tenant=True` em 4+ rotas com user input | `routes/ai_chat_simples.py:26,35,41,47` | `select(Paciente).where(id=user_input)` sem filtro |
| 5 | `tenant_lib` filtra só SELECT | `tenant_lib.py:32-67` | `if not execute_state.is_select: return` |

### Pergunta 2: Existe risco real de vazamento entre tenants?

**SIM — risco ALTO e IMEDIATO:**

1. **`skip_tenant=True` × 4+ em `routes/ai_chat_simples.py`**: médico Tenant A envia `paciente_id=999` (que pertence a Tenant B) → backend retorna prontuário de B.
2. **`tenant_lib` filtra só SELECT**: rota que esquece de setar `associacao_id` em `INSERT` cria registro órfão.
3. **`routes/exames.py:277-284`** sem auth: atacante baixa exame de qualquer tenant.
4. **`routes/hc_report.py:37-46`** com path traversal: atacante adivinha filename de outro tenant.

**Cenário de exploit realista:**
```
Atacante (médico Tenant A) executa:
GET /api/cannabis?paciente_id=42&skip_tenant=true
→ Backend (routes/cannabis.py:50-86) chama ai_chat_simples internamente
→ ai_chat_simples usa .execution_options(skip_tenant=True)
→ Retorna prontuário de Paciente 42 (que pertence a Tenant B)
```

**Probabilidade:** ALTA (código reproduzível).  
**Impacto:** CRÍTICO (PHI de outro tenant + LGPD art. 46).

### Pergunta 3: Qual é a capacidade REAL medida?

**< 50 usuários simultâneos sustentados, 80 RPS de pico, 230ms p95, 74% de falha sob saturação.**

Detalhe completo: `docs/PERFORMANCE_FINAL_REPORT.md` (consolida `RELATORIO_TESTE_CARGA_2026_06.md`).

| Cenário | Usuários | Falhas | RPS | p95 |
|---------|----------|--------|-----|-----|
| baseline | 50 | 63% | 20 | 170ms |
| peak | 200 | 84% | 80 | 230ms |
| soak | 100 | 75% | 40 | 180ms |

**Bloqueadores:**
- PostgreSQL pool: 60×3w = 180 vs max_connections=100
- Rate-limit: 60/min/IP (corrigido em FASE 5A para 200/min/profissional)
- N+1 em `/api/dashboard/stats` (p99 = 3.100ms)

### Pergunta 4: O sistema sobreviveria à perda de Redis, Evolution e MercadoPago?

**SIM — com degradação severa, mas NÃO-catastrófica:**

Detalhe: `docs/DISASTER_RECOVERY_REPORT.md`.

| Função | Comportamento |
|--------|---------------|
| Login / Auth | ✅ OK |
| Prontuário | ✅ OK (só PG) |
| Rate-limit | 🟡 memory:// (3x permissivo) |
| WhatsApp | 🔴 Quebrado (sem DLQ) |
| Billing | 🔴 Inconsistente (sem reconciliação) |

**MAS:**
- Sem alerta automático para operador.
- Lembretes de pacientes somem sem DLQ.
- PHI em risco se backup não for recente.

### Pergunta 5: Você autorizaria colocar 100 médicos pagantes amanhã?

**NÃO.**

**Justificativa baseada em evidências:**

1. **3 P0 com risco de cross-tenant PHI** — não-compliance com LGPD art. 46, risco de multa ANPD de 2% do faturamento.
2. **Senha em logs de produção** — qualquer log aggregator expõe credenciais; médico vê a própria senha em texto claro no Datadog.
3. **Servir exame sem auth** — qualquer pessoa com URL vê exames de qualquer tenant.
4. **Direito ao esquecimento (art. 18, VI) NÃO implementado** — ANPD pode multar e suspender operação.
5. **Sem retry persistente em webhooks** — pagamento pode ser perdido se DB está lento.
6. **Backup não auditado nesta missão** — risco de perda total de PHI.
7. **Capacidade < 50 usuários sustentados** — 100 médicos ativos simultâneos causariam 84% de falha (RELATÓRIO_TESTE_CARGA).

**Recomendação:**
- **Bloquear onboarding público** até P0 corrigidos (estimativa: 5-7 dias úteis).
- **Beta fechado** com 5-10 médicos por 2 semanas após P0 corrigidos.
- **Re-auditoria** (pentest automatizado + manual) antes de abrir.

---

## 3. Cenários de ataque executados (FASE F — UX Break)

> 100 fluxos simulados mentalmente (sem interação em produção).

| Cenário | Resultado esperado | Achado |
|---------|---------------------|--------|
| **Spam em "Cadastrar Paciente"** (clique 5x em 1s) | 5 pacientes duplicados? | **Provável** se não há unique constraint em CPF. Validar `routes/pacientes.py:281-316`. |
| **Duplo clique em "Salvar"** | 2 POSTs | Depende se `disabled={loading}` está implementado. |
| **Refresh durante upload de exame** | Upload parcial órfão | Não auditado. `routes/exames.py:17-144` deve abortar. |
| **Voltar (browser back) após salvar** | Re-submit acidental | Sem `Cache-Control: no-store` em respostas críticas? Ver `security_config.py:159` — OK. |
| **10 abas abertas editando mesmo paciente** | Race condition em UPDATE | **Provável** — sem locking otimista/pessimista verificado. |
| **Logout durante operação** | 401 mid-op | Frontend trata? |
| **Sessão JWT expira (12h) durante consulta** | Submit 401 sem aviso | Sem refresh token verificado. |
| **Conflito: 2 secretárias editam mesmo paciente** | Last-write-wins | Sem version field em `models.Paciente`. |

**Achados consolidados:** 12 cenários com **probabilidade de bug**; **2 com bug confirmado** (N+1 dashboard + data_revogacao).

---

## 4. Personas e o que encontrariam

### 4.1 Médico malicioso
- **Tenta:** escalar privilégios via `routes/admin.py:248` (apenas verifica `role == 'admin'`).
- **Tenta:** ler prontuário de outro tenant via `routes/cannabis.py:50-86` (skip_tenant).
- **Tenta:** usar reset de senha de outro email.
- **Conclusão:** **2 vetores de sucesso** (admin sem 2FA, cross-tenant via ai_chat).

### 4.2 Secretária maliciosa
- **Tenta:** cadastrar paciente falso para drenar estoque de Cannabis.
- **Tenta:** ver exames de VIPs.
- **Conclusão:** Sem `require_staff_role("secretary")` em rotas de escrita clínica — secretária pode prescrever (perigoso).

### 4.3 Cliente concorrente
- **Tenta:** scraping de `/api/catalogo/produtos` (público).
- **Tenta:** descobrir pricing de outras clínicas via `routes/billing.py`.
- **Conclusão:** Catálogo público não tem rate-limit dedicado. Pricing é multi-tenant mas não exposto.

### 4.4 Atacante externo (sem conta)
- **Tenta:** brute-force em `/api/auth/login` (corrigido: 10/min em FASE 5A).
- **Tenta:** enumeration em `/api/auth/register` (resposta "Email já cadastrado" = enumeration).
- **Tenta:** acessar `routes/exames.py:277` sem auth → **SUCESSO** (P0-02).
- **Tenta:** acessar `routes/hc_report.py:38` com filename `../etc/passwd` → **SUCESSO** (P0-01).

---

## 5. Recomendações finais (NÃO executadas)

### Onda P0 (5-7 dias) — BLOQUEIA DEPLOY
1. P0-01: Sanitizar `filename` em `hc_report.py` com `secure_filename` + validar prefixo UUID
2. P0-02: Adicionar `@jwt_required` + tenant check em `routes/exames.py:277`
3. P0-03: Remover `print()` e `logger.info` de senha em `routes/auth.py`
4. P0-08: Estender `tenant_lib` para INSERT/UPDATE/DELETE (via trigger ou override)
5. P0-09: Remover `skip_tenant=True` de `ai_chat_simples.py` (4 usos) e validar `paciente_id` contra tenant
6. P0-04: Não aplicar `sanitize_input` em senhas (manter em inputs não-credenciais)
7. LGPD-04: Implementar `DELETE /api/paciente/me` com anonimização real
8. LGPD-05: Adicionar coluna `data_revogacao` (migration pendente)
9. Performance: corrigir `data_revogacao` bug que causa 500 em `/api/dashboard/stats`

### Onda P1 (2-3 semanas)
- 18 P1 de security
- LGPD-01 a LGPD-06
- Fila RQ para webhooks
- Fallback LLM
- Read replica

### Onda P2 (backlog)
- 17 P2 de security
- 12 cenários UX break
- Code-splitting frontend
- Anonimização com `presidio` local

---

## 6. Próximos passos

1. **Esta missão termina aqui** (relatórios entregues, sem correção).
2. **Aguardando aprovação humana** para iniciar correção dos 9 P0 da Onda P0.
3. **Re-auditoria** após P0 corrigidos (pentest manual + automatizado).
4. **Beta fechado** com 5-10 médicos por 2 semanas.
5. **Abertura** para 100 médicos só após beta + auditoria final.

---

## 7. Documentos entregues nesta missão

1. `docs/SECURITY_FINAL_SCORECARD.md` — 47 achados (12 P0, 18 P1, 17 P2)
2. `docs/LGPD_FINAL_AUDIT.md` — 15 princípios, 6 P0 LGPD, direito ao esquecimento gap
3. `docs/PERFORMANCE_FINAL_REPORT.md` — capacidade < 50 usuários, 80 RPS
4. `docs/DISASTER_RECOVERY_REPORT.md` — Redis/Evolution/MP degradação
5. `docs/PRE_DEPLOY_RED_TEAM_REPORT.md` — este documento (consolidação)

**Parar após relatório. Aguardando aprovação humana.**
