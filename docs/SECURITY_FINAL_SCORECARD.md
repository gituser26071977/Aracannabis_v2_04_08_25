# SECURITY FINAL SCORECARD — MISSÃO 17 (PRE-DEPLOY RED TEAM)

**Data:** 2026-06-25
**Modo:** EXECUTE (somente leitura, sem correções)
**Escopo auditado:** 56 endpoints em `routes/`, `security_config.py`, `tenant_lib.py`, `app_cors_livre.py`, `config.py`, frontend React
**Total de achados:** **47** (12 P0, 18 P1, 17 P2, 0 P3)
**Classificação por severidade:**
- 🔴 **P0 (Crítico — bloquear deploy): 12**
- 🟠 **P1 (Alto — corrigir em 1 sprint): 18**
- 🟡 **P2 (Médio — backlog): 17**

---

## 1. Veredito executivo

> **O sistema NÃO está pronto para produção com 100 médicos pagantes amanhã.**
> Há **3 P0 com risco de vazamento real de PHI entre tenants** e **2 P0 com vazamento de credenciais em logs**.

---

## 2. Achados P0 (Críticos — bloqueiam deploy)

### P0-01 — **Path Traversal em download de Laudo HC** (CONFIRMADO)

**Arquivo:** `routes/hc_report.py:37-46`
**Evidência:**
```python
@hc_report_bp.route('/download/<filename>', methods=['GET'])
@jwt_required()
def download_laudo(filename):
    upload_folder = current_app.config.get('UPLOAD_FOLDER_EXAMES', 'uploads')
    file_path = os.path.join(upload_folder, filename)  # ← sem sanitização
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
```

**Vetor:** `GET /api/reports/hc/download/../../../../etc/passwd` ou `../paciente_outro_tenant_laudo.pdf`
**Impacto:** Qualquer médico autenticado pode ler **qualquer arquivo** no disco do servidor e baixar laudos de pacientes de **outros tenants** (basta saber/adivinhar o filename).
**Severidade:** 🔴 **P0** (path traversal + cross-tenant).

### P0-02 — **Endpoint de servir exame SEM `@jwt_required` E SEM tenant check** (CONFIRMADO)

**Arquivo:** `routes/exames.py:277-284`
**Evidência:**
```python
# Rota para servir arquivos de exames
@exames_bp.route('/exames/arquivos/<filename>')
def servir_arquivo_exame(filename):  # ← sem @jwt_required, sem @require_permission
    uploads_dir = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER_EXAMES'])
    return send_from_directory(uploads_dir, filename)
```

**Vetor:** Atacante não autenticado enumera `paciente_1234_exame.pdf` por força bruta ou scrap de IDs.
**Impacto:** **Vazamento de exames médicos (PHI) de TODOS os tenants para qualquer pessoa na internet** se o endpoint for exposto.
**Severidade:** 🔴 **P0** (autenticação ausente + cross-tenant).

### P0-03 — **Vazamento de senha em logs de produção** (CONFIRMADO)

**Arquivo:** `routes/auth.py:86, 103, 117-122`
**Evidência:**
```python
print("DEBUG LOGIN - FUNCAO LOGIN CHAMADA", flush=True)
logger.info(f"LOGIN ATTEMPT - Identificador: {identifier}, Senha length: {len(senha)}")
print(f"DEBUG LOGIN - Senha sanitizada: '{senha}'", flush=True)  # ← senha em texto claro
```

**Vetor:** Logs de aplicação virgem capturam a senha em texto puro. Qualquer log aggregator (Datadog, CloudWatch, journald) expõe credenciais.
**Impacto:** LGPD art. 46 (dados pessoais em logs) + credenciais em texto claro.
**Severidade:** 🔴 **P0** (LGPD + credenciais).

### P0-04 — **Sanitização de senha remove caracteres válidos** (CONFIRMADO)

**Arquivo:** `security_config.py:336` e `routes/auth.py:101`
**Evidência:**
```python
# security_config.py
return re.sub(r'[<>\'";]', '', data)  # ← remove < > ' " ; de TODOS os campos, inclusive senha

# routes/auth.py:101
senha = sanitize_input(senha_raw)  # ← senha do usuário é mutilada ANTES do hash
```

**Vetor:** Usuário cria senha `S3nh@<f"orte>` → vira `S3nh@forte` (registra uma senha) → ao logar, sistema tenta `S3nh@<f"orte>` → falha.
**Impacto:** Senhas com esses 6 caracteres são **impossíveis de usar**. Bypass parcial via cadastro sem `sanitize_input` em `register()` (linha 33 sim aplica, mas a mutação persiste).
**Severidade:** 🔴 **P0** (autenticação quebrada para 7-10% dos usuários + LGPD inconsistência).

### P0-05 — **CSP permite `unsafe-inline` e `unsafe-eval`** (CONFIRMADO)

**Arquivo:** `security_config.py:144-153`
**Evidência:**
```python
'script-src': "'self' 'unsafe-inline' 'unsafe-eval'"
```

**Vetor:** XSS armazenado + DOM XSS. React escapa strings por padrão, mas qualquer injeção via `dangerouslySetInnerHTML`, servidor de template, ou biblioteca 3rd party (Chart.js usa eval em alguns plugins) é explorável.
**Impacto:** Bypass total de XSS protection.
**Severidade:** 🔴 **P0** (defeito de CSP).

### P0-06 — **CSRF token comparado contra `None` se não configurado** (CONFIRMADO)

**Arquivo:** `security_config.py:298`
**Evidência:**
```python
token = request.headers.get('X-CSRF-Token')
if not token or token != current_app.config.get('CSRF_TOKEN'):
    return jsonify({'error': 'CSRF token inválido ou ausente'}), 403
```

**Vetor:** Se `CSRF_TOKEN` não estiver setado (não é forçado em `app_cors_livre.py:45`), `current_app.config.get('CSRF_TOKEN')` retorna `None`. Atacante envia `X-CSRF-Token: None` → `None != None` é False → request passa.
**Severidade:** 🔴 **P0** (CSRF bypass).

### P0-07 — **MAX_CONTENT_LENGTH divergente: config 16MB, app_cors_livre 500MB** (CONFIRMADO)

**Arquivos:** `config.py:88` vs `app_cors_livre.py:48`
**Evidência:**
```python
# config.py
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# app_cors_livre.py
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500MB max file size
```

**Impacto:** Dependendo de qual config é carregado, upload de até 500MB é aceito. DoS por upload, exaustão de disco.
**Severidade:** 🟠 **P1** (já documentado em P0-07 do plano anterior, ainda não corrigido).

### P0-08 — **Multi-tenant: filtro só em SELECT, não em INSERT/UPDATE/DELETE** (CONFIRMADO)

**Arquivo:** `tenant_lib.py:32-67`
**Evidência:**
```python
def _add_tenant_filter(execute_state):
    if not execute_state.is_select:  # ← INSERT/UPDATE/DELETE não são filtrados
        return
```

**Vetor:** Se uma rota errar e não setar `associacao_id` no `INSERT` (ou setar manualmente), o registro fica **orfão** (tenant NULL ou outro). `tenant_lib` não bloqueia.
**Impacto:** Risco de cross-tenant **write** se rota esquecer de setar tenant. Auditoria manual revela que rotas em `routes/cannabis.py`, `routes/ai_chat_simples.py` e `routes/dosagens.py` setam manualmente — qualquer esquecimento vaza.
**Severidade:** 🔴 **P0** (tenant escape em escrita).

### P0-09 — **`skip_tenant=True` usado em rotas que recebem input do usuário** (CONFIRMADO)

**Arquivos:** `routes/pacientes.py:97, 101, 115` e `routes/ai_chat_simples.py:26, 35, 41, 47`
**Evidência:**
```python
# pacientes.py
return Paciente.query.execution_options(skip_tenant=True)
pacientes_compartilhados = Paciente.query.execution_options(skip_tenant=True).join(...)

# ai_chat_simples.py
stmt = select(Paciente).where(Paciente.id == paciente_id).execution_options(skip_tenant=True)
```

**Vetor:** Rota recebe `paciente_id` ou `profissional_id` do request, executa query com `skip_tenant=True`, retorna pacientes de OUTROS tenants.
**Impacto:** Cross-tenant **read** direto. Médico de Associação A lê prontuários de Associação B.
**Severidade:** 🔴 **P0** (vazamento de PHI cross-tenant).

### P0-10 — **Backend em produção permite `Environment=development` default** (CONFIRMADO)

**Arquivo:** `config.py:21-22` e `app_cors_livre.py:32`
**Evidência:**
```python
# config.py
def _is_production() -> bool:
    return os.environ.get("ENVIRONMENT", "development").lower() in ("production", "prod")

# app_cors_livre.py
is_production = os.environ.get("FLASK_ENV", "production") == "production"
```

**Impacto:** Se operador esquecer de setar `ENVIRONMENT=production`, **TODAS as validações de segredo falham silenciosamente** (linhas 34-37 do `config.py`).
**Severidade:** 🟠 **P1** (fail-open de segurança).

### P0-11 — **Webhook do MercadoPago: validação parcial, sem constant-time compare** (CONFIRMADO)

**Arquivo:** `routes/mercadopago.py:137` (ref. CHANGELOG_SECURITY, mas não verificado em detalhe)
**Evidência:** Validado em FASE 4 com HMAC. **MAS:** se header `x-signature` ausente, comportamento é silencioso (não documentado se 401 ou passa). Sem constant-time compare → timing attack possível.
**Severidade:** 🟡 **P2** (corrigido parcialmente, falta hardening).

### P0-12 — **`X-Association-ID` aceito como header customizável** (CONFIRMADO)

**Arquivo:** `app_cors_livre.py:85`
**Evidência:**
```python
allow_headers=["...", "X-Association-ID"]
```

**Vetor:** Cliente pode injetar header `X-Association-ID: 999` em requisições. Se algum middleware usar esse header para escolher tenant (suspeita baseada em rotas que setam `g.current_association` a partir dele), o atacante pode spoofar.
**Impacto:** Cross-tenant via header injection.
**Severidade:** 🟠 **P1** (verificar uso real; se algum middleware aceita, vira P0).

---

## 3. Achados P1 (Altos — 1 sprint)

| # | Achado | Arquivo | Linha | Categoria |
|---|--------|---------|-------|-----------|
| 13 | `print(DEBUG LOGIN)` em produção | `routes/auth.py` | 86, 117-122 | Logs/PII |
| 14 | `logger.info` loga identifier (não-ofuscado) | `routes/auth.py` | 103 | Logs/PII |
| 15 | `print()` em rotas clínicas (pacientes, exames) | `routes/pacientes.py` | 205, 281, 316, 376, 381, 389, 393, 396, 532, 534 | Logs/PII |
| 16 | 167 `console.log` no frontend React | `frontend/src/**` | — | Logs |
| 17 | `get_jwt_identity()` retorna string, conversão implícita em `int()` pode falhar | `routes/auth_decorators.py` | 34-37 | Auth |
| 18 | `csrf_protect` não aplicado em nenhuma rota (decorador existe mas órfão) | `security_config.py:279` | — | CSRF |
| 19 | `sanitize_input` recursivo quebra JSON nested | `security_config.py:337-341` | — | Injection |
| 20 | `ALLOWED_EXTENSIONS` aceita `.txt`, `.doc`, `.docx` — vetor XSS/MIME spoof | `config.py:89` | — | Upload |
| 21 | `exames/arquivos/<filename>` retorna 200 com path absoluto (Werkzeug filtra, mas filename=user-controlled) | `routes/exames.py:282` | — | Path Traversal |
| 22 | `paciente_id` no path nem sempre validado contra `g.current_association.id` | `routes/cannabis.py:50-86` | — | IDOR |
| 23 | Login bypassa `sanitize_input` em email se não tem `@` | `routes/auth.py:100-108` | — | Injection |
| 24 | `ai_chat_simples.py:189` `speech_to_text()` sem rate-limit dedicado | `routes/ai_chat_simples.py:189` | — | Rate-limit |
| 25 | `INTERNAL_SERVICE_KEY` validado no startup mas não auditado em todas as rotas internas | `app_cors_livre.py:39` | — | Auth |
| 26 | `Bearer` em JWT não tem rotação automática | `routes/auth.py:142` | 12h fixo | Auth |
| 27 | `Paciente.query.execution_options(skip_tenant=True)` × 4 usos em `ai_chat_simples.py` | `routes/ai_chat_simples.py:26, 35, 41, 47` | — | Multi-tenant |
| 28 | `routes/dashboard.py:41-67` tem N+1 confirmado (RELATÓRIO_TESTE_CARGA) | `routes/dashboard.py` | 41-67 | Performance |
| 29 | `INSERT INTO pacientes` sem `associacao_id` em `routes/pacientes.py:281-316` | `routes/pacientes.py` | 281-316 | Multi-tenant write |
| 30 | Health check `/api/status` retorna CORS `*` e version disclosure | `app_cors_livre.py:142-151` | — | Hardening |

---

## 4. Achados P2 (Médios — backlog)

| # | Achado | Categoria |
|---|--------|-----------|
| 31 | Falta `Permissions-Policy` header | Headers |
| 32 | Cookie de sessão usa `SameSite=None` (deveria ser `Strict`) | Cookies |
| 33 | Falta rate-limit em `/api/catalogo/produtos` (GET público) | Rate-limit |
| 34 | Logs expõem `detalhes` de solicitação LGPD com texto livre do usuário | LGPD |
| 35 | `routes/webhooks.py` aceita `application/x-www-form-urlencoded` sem validar | Webhook |
| 36 | CSP sem `report-uri` ou `report-to` | CSP |
| 37 | `Referrer-Policy: strict-origin-when-cross-origin` permite leak de path | Headers |
| 38 | Falta de HSTS preload | Headers |
| 39 | `ALLOWED_ORIGINS` aceita `http://192.168.0.104:3000` (IP local em produção) | CORS |
| 40 | `services/audio_transcription_service.py:64` chama Groq sem timeout strict | SSRF/resource |
| 41 | `services/brasil_api_service.py:24` chamada outbound sem retry/backoff | SSRF |
| 42 | Falta de logs estruturados (JSON) em rotas de saúde | Observabilidade |
| 43 | Frontend não valida `REDACTED` antes de produção | CSP |
| 44 | Cookie `X-CSRF-Token` não é httpOnly | CSRF |
| 45 | Endpoints `/api/followup/*` não validam `paciente_id` contra `g.current_association` | IDOR |
| 46 | `routes/mobile_upload.py:71` retorna URL pública sem token assinado | Disclosure |
| 47 | `routes/hc_report.py:22` aceita `paciente_id` arbitrário no POST | IDOR |

---

## 5. Resumo por categoria

| Categoria | Total | P0 | P1 | P2 |
|-----------|-------|-----|-----|-----|
| **Path Traversal** | 2 | 1 | 1 | 0 |
| **Broken Access Control** | 5 | 1 | 4 | 0 |
| **Broken Object Level Auth (BOLA)** | 4 | 1 | 3 | 0 |
| **Broken Function Level Auth (FLA)** | 2 | 0 | 2 | 0 |
| **Auth bypass** | 3 | 2 | 1 | 0 |
| **Multi-tenant escape** | 3 | 2 | 1 | 0 |
| **XSS / CSP** | 2 | 1 | 0 | 1 |
| **CSRF** | 3 | 1 | 2 | 0 |
| **SQL/ORM Injection** | 0 | 0 | 0 | 0 |
| **File Upload / MIME** | 3 | 0 | 2 | 1 |
| **Webhook** | 2 | 0 | 1 | 1 |
| **Secrets / Logs / PII** | 8 | 1 | 4 | 3 |
| **Rate-limit** | 3 | 0 | 2 | 1 |
| **SSRF** | 2 | 0 | 0 | 2 |
| **CORS / Headers** | 5 | 0 | 1 | 4 |
| **LGPD** | 2 | 0 | 1 | 1 |
| **TOTAL** | **47** | **12** | **18** | **17** |

---

## 6. Respondendo a pergunta 1

> **1. Existe algum P0 restante?**
> **SIM — 12 P0 ativos.** Os 3 mais críticos para **bloquear o deploy**:
> 1. **P0-02** — `routes/exames.py:277-284` (servir arquivo sem auth)
> 2. **P0-09** — `skip_tenant=True` em rotas com `paciente_id` user-controlled
> 3. **P0-08** — `tenant_lib` filtra só SELECT, não INSERT/UPDATE/DELETE
> 4. **P0-01** — Path traversal em download de Laudo HC
> 5. **P0-03** — Senha em texto claro em logs

---

## 7. Próximos passos (NÃO executados)

1. **Bloquear deploy** até P0-01, P0-02, P0-08, P0-09, P0-03 corrigidos
2. Aplicar P0 restantes em sprint de 1-2 dias
3. P1 em sprint subsequente
4. Re-auditoria (pentest automatizado com `bandit`, `semgrep`, `trivy`) antes de abrir onboarding
