# Auditoria de Segurança — AraOS SIAP

**Data:** 2026-06-22
**Escopo:** Backend Flask (`routes/`, `services/`, `security_config.py`, `app_cors_livre.py`, `docker-compose.prod.yml`, `requirements.txt`)
**Método:** Análise estática de código + leitura de configurações + leitura de logs de produção
**Branch:** `main` @ `ce141c5`
**Produção:** VPS `147.93.33.253` (domínios `visualsmartflow.com.br` / `araos.visualsmartflow.com.br`)

---

## Sumário Executivo

| Severidade | Qtd |
|-----------|-----|
| 🔴 **CRÍTICO** | **5** |
| 🟠 **ALTO** | **23** |
| 🟡 **MÉDIO** | **18** |
| 🟢 **BAIXO** | **9** |
| **TOTAL** | **55** |

**Veredito:** O sistema **NÃO está pronto para produção real** com dados sensíveis de pacientes. Há 5 falhas exploráveis hoje (qualquer pentester identificaria), CSRF totalmente desativado, autenticação fraca em vários blueprints críticos e gestão de segredos instável (chave de criptografia regenerada a cada restart se env var ausente).

---

## Top 10 ações (ordenadas por ROI)

| # | Ação | Esforço | Impacto |
|---|------|---------|---------|
| 1 | Implementar e aplicar `validate_required_secrets()` cobrindo `JWT_SECRET_KEY`, `SECRET_KEY`, `ANONYMIZATION_KEY`, `INTERNAL_SERVICE_KEY`, `WEBHOOK_SECRET_KEY` (config.py:27-30 referencia função inexistente → `except ImportError` engole) | 2h | Elimina 4 vetores (fallbacks hardcoded + crypto instável) |
| 2 | Bloquear startup se `ANONYMIZATION_KEY` ausente em prod (`crypto.py:10-17` regenera chave silenciosamente) | 1h | Evita perda irrecuperável de dados criptografados |
| 3 | Adicionar `@jwt_required` em **TODAS** as rotas de `routes/exames.py`, `routes/voice.py`, `routes/anuncios.py` (múltiplas rotas hoje são públicas) | 3h | Fecha 3 vetores de vazamento cross-tenant |
| 4 | Remover `GET /api/auth/create-admin` sem `@jwt_required` (rotas 26-56) — ou exigir `@jwt_required` + role admin + senha aleatória | 1h | Fecha backdoor público de criação de admin |
| 5 | Adicionar `@limiter.limit("5/min; 20/hour")` em `/auth/login` + storage Redis (atualmente `memory://` em `security_config.py:142`) | 2h | Mitiga brute-force e DDoS no login |
| 6 | Validar assinatura HMAC SHA256 (`x-signature`) em todos webhooks: MercadoPago, Evolution API, Dr.Anderson, módulos (5 webhooks hoje sem validação) | 4h | Fecha 5 vetores de injeção de payload |
| 7 | Criptografar Fernet: persistir chave estável + remover `print()` da chave em `crypto.py:14-16` + implementar KMS/rotação | 3h | Evita perda de dados criptografados + vazamento de chave em logs |
| 8 | Adicionar `@csrf_protect` em rotas mutativas OU remover suporte CSRF e marcar app como SPA-only com mesma origem | 4h | Fecha CSRF |
| 9 | Padronizar `MAX_CONTENT_LENGTH` para 16MB (atualmente `app_cors_livre.py:34=500MB` diverge de `config.py:88=16MB`) | 30min | Mitiga DoS por upload |
| 10 | Remover `sanitize_input()` aplicado em senha (`routes/auth.py:127-128`) — caracteres especiais são válidos em senhas fortes e estão sendo alterados antes do hash | 1h | Quebra de login para usuários com senha contendo `<>'";` |

---

## Achados Detalhados

### 🔴 CRÍTICOS (5)

#### C1. Endpoint público para criar admin sem autenticação
- **Arquivo:** `routes/auth.py:26-56`
- **Rota:** `GET /api/auth/create-admin`
- **Risco:** Atacante pode criar um admin com senha hardcoded `AraOS@2025` (`auth.py:33`) sem nenhuma credencial.
- **Recomendação:** Remover rota. Se mantida para setup inicial, exigir `@jwt_required` + role admin e gerar senha aleatória retornada apenas uma vez.

#### C2. Crypto: chave de criptografia regenerada a cada boot
- **Arquivo:** `services/anonymization_service/app/crypto.py:10-17`
- **Comportamento:** Se `ANONYMIZATION_KEY` ausente em produção, gera chave temporária nova e loga em stdout (`print(f"...{new_key.decode()}")`).
- **Impacto:** Dados criptografados antes do restart ficam irrecuperáveis. Chave aparece em logs centralizados (vazamento).
- **Recomendação:** Em produção, abortar startup se chave ausente. Persistir chave em KMS/Vault. Nunca logar chave.

#### C3. CSRF totalmente desativado
- **Arquivo:** `security_config.py:201-224` (decorator `@csrf_protect` existe mas não é usado em lugar nenhum — `grep @csrf_protect` retorna 0 usos)
- **Risco:** Como o app envia JWT no header `Authorization` (não em cookie), o CSRF clássico via cookie não se aplica. MAS o CORS com `supports_credentials=True` + origens amplas (`ALLOWED_ORIGINS`) habilita cross-origin authenticated requests. Combinado com tokens em header, é vetor XSSI se um subdomínio for comprometido.
- **Recomendação:** Remover suporte CSRF (não usar) OU aplicar em rotas mutativas. Como o sistema é SPA + Bearer token, marcar como "SPA-only com same-origin obrigatória".

#### C4. Rate limit não aplicado no login
- **Arquivo:** `routes/auth.py:111` (constante `LOGIN_RATE_LIMIT` existe em `security_config.py:75-78` mas nenhum `@limiter.limit(...)` está aplicado).
- **Storage:** `memory://` (`security_config.py:142`) — por-worker, **NÃO distribuído**.
- **Risco:** Brute-force viável; em produção com 3 gunicorn workers, atacante consegue 3x o limite (cada worker conta separado).
- **Evidência no teste de carga:** Peak test (200u/3min) → login p95=10s, 46 requests com `429 Too Many Requests: 60 per 1 minute`. Com 200 usuários do mesmo IP, o limite de 60/min satura imediatamente.

#### C5. Webhooks sem validação de assinatura
- **Arquivos:**
  - `routes/mercadopago.py:119-159`
  - `routes/webhooks.py:16-41`
  - `routes/dynamic_tenant_webhook.py:13-93`
  - `routes/dr_anderson_webhook.py:108-181`
  - `routes/modulos.py:352-411` (aceita GET também!)
- **Risco:** Atacante que souber a URL do webhook pode forjar POSTs que ativam assinaturas, disparam LLM agents (custo de API!), ou mudam estado de pagamento.
- **Evidência em `services/mercadopago_service.py:19`:** `MERCADOPAGO_WEBHOOK_SECRET` lido mas **nunca usado** para HMAC verify.
- **Recomendação:** Validar `x-signature` HMAC SHA256 com o secret específico de cada provedor. Forçar método POST em todos webhooks.

---

### 🟠 ALTOS (23)

#### A1. JWT com 24h de validade sem refresh tokens
- **Arquivo:** `config.py:77` (`JWT_ACCESS_TOKEN_EXPIRES = 86400`)
- **Risco:** Token roubado fica válido por 24h. Sem mecanismo de revogação.
- **Recomendação:** Implementar access (15min) + refresh (7d) tokens. Adicionar `JWT_BLOCKLIST_ENABLED` para logout server-side.

#### A2. Algoritmo JWT não fixado explicitamente
- **Arquivo:** `config.py:68-75`
- **Risco:** Se `JWT_ALGORITHM` mudar no futuro, tokens antigos ficam inválidos ou exploráveis.
- **Recomendação:** Fixar `JWT_ALGORITHM = "HS256"` em config.

#### A3. `SECRET_KEY` sobrescrito em `create_app`
- **Arquivo:** `app_cors_livre.py:28`
- **Risco:** O factory sobrescreve `app.config["SECRET_KEY"]` com `os.environ.get("SECRET_KEY", secrets.token_hex(32))`, perdendo o controle validado em `config.py`. Se env ausente, gera chave aleatória em runtime → sessões/CSRF imprevisíveis.
- **Recomendação:** Não sobrescrever. Usar `Config.SECRET_KEY` validado.

#### A4. `CSRF_TOKEN` regenerado em cada `create_app`
- **Arquivo:** `app_cors_livre.py:31`
- **Risco:** Reinício do processo invalida token de todos os clientes.
- **Recomendação:** Armazenar token CSRF por sessão.

#### A5. Rotas de exames sem `@jwt_required`
- **Arquivo:** `routes/exames.py:16-141`
- **Risco:** Qualquer cliente pode listar/baixar/criar exames de paciente arbitrário.
- **Rotas afetadas:** `POST /exames`, `GET /exames/<id>`, `DELETE /exames/<id>`, `GET /exames/arquivos/...`
- **Recomendação:** Adicionar `@jwt_required` + checagem de tenant + ownership.

#### A6. Rotas de anúncios abertas a POSTs sem auth
- **Arquivo:** `routes/anuncios.py:129-247`
- **Risco:** `@cross_origin()` em vez de `@jwt_required()`. POST para `view/click` é público e escreve no DB (potencial DDoS/escrita abusiva).

#### A7. Rotas de voice sem `@jwt_required`
- **Arquivo:** `routes/voice.py:28-122`
- **Risco:** `/api/voice/sessions`, `/sessions/<id>/transcript`, `/sessions/<id>/end` são públicos. `/config` retorna URL do WebSocket interno (enumeração).
- **Recomendação:** Adicionar auth + validar tenant.

#### A8. Auth de paciente sem rate-limit específico
- **Arquivo:** `routes/patient_auth.py:170`
- **Risco:** Permite enumeração de emails (CPF/email lookup) e brute-force.

#### A9. Auth AAP sem rate-limit
- **Arquivo:** `routes/aap.py:320,343`

#### A10. Raw SQL sem filtro de tenant em sintomas personalizados
- **Arquivo:** `routes/sintomas.py:193,245,254,291,311,351,371`
- **Risco:** Bypass do filtro multi-tenant automático (que só atua em ORM).
- **Recomendação:** Adicionar `AND associacao_id = :tenant_id` em cada `text(...)`.

#### A11. `sanitize_input()` quebra senhas fortes
- **Arquivo:** `routes/auth.py:127-128`
- **Risco:** Remove `<>'";` antes de hash. Senhas válidas com esses caracteres não logam.
- **Recomendação:** Remover sanitização da senha. Aplicar só em identificadores.

#### A12. Upload de arquivos sem validação de MIME real
- **Arquivos:** `routes/exames.py:13-14`, `routes/pacientes.py:11-15`, `routes/patient_import_agent.py:29-32`
- **Risco:** Atacante faz upload de `.php` renomeado para `.jpg` (polyglot) ou HTML/JS que executa em outro contexto.
- **Recomendação:** Validar MIME real com `python-magic` ou `filetype`. Renomear para UUID.

#### A13. Rota de download de exame serve arquivo sem auth
- **Arquivo:** `routes/exames.py:235-242`
- **Risco:** Path traversal + acesso não autenticado a arquivos de pacientes.

#### A14. Uploads sem antivírus
- **Recomendação:** Integrar `pyclamd` ou fila assíncrona para scan ClamAV.

#### A15. CORS com credentials + origens amplas
- **Arquivo:** `app_cors_livre.py:62-81`
- **Risco:** Lista inclui `localhost:3000-3010`, IPs internos, domínios prod. Combinado com `supports_credentials=True`, qualquer origem comprometida lê o cookie.
- **Recomendação:** Restringir ALLOWED_ORIGINS a domínios prod exatos.

#### A16. CSP com `unsafe-inline` e `unsafe-eval`
- **Arquivo:** `security_config.py:111-130`
- **Risco:** XSS em qualquer ponto executa JS arbitrário.

#### A17. Endpoints dashboard cross-tenant
- **Arquivo:** `routes/dashboard.py:15,82`
- **Risco:** `Paciente.query.filter_by(profissional_responsavel_id=...)` não aplica `g.current_association`. Depende exclusivamente do filtro automático. Se raw query, mistura clínicas.

#### A18. Logs com PII (CPF, hash de senha)
- **Arquivos:**
  - `tools/importer/import_excel.py:124` (logger.info com CPF)
  - `routes/auth.py:117,130,144-149` (identificador de login + hash truncado)
- **Risco:** Logs centralizados contêm dados pessoais e hashes.

#### A19. Dependências com versão não fixada
- **Arquivo:** `requirements.txt`
- **Risco:** `Flask-JWT-Extended`, `Flask-CORS`, `Flask-SQLAlchemy`, `Flask-Limiter`, `crewai`, `langchain` — versões com `>=` permitem upgrades automáticos.
- **Recomendação:** `pip-audit` + pinning rigoroso.

#### A20. Webhook Evolution público
- **Arquivo:** `routes/dynamic_tenant_webhook.py:13-93`
- **Risco:** Qualquer pessoa pode enviar POST e fazer o sistema chamar OpenAI/Claude/Groq com payload arbitrário → **gasto de tokens e prompt injection**.

#### A21. Webhook Dr.Anderson público
- **Arquivo:** `routes/dr_anderson_webhook.py:108-181`
- **Risco:** Dispara LLM agent com prompts arbitrários.

#### A22. Webhook de módulos aceita GET
- **Arquivo:** `routes/modulos.py:352-411` (`if request.method == "GET": payload = request.args.to_dict()`)
- **Risco:** Webhook público permite ativar módulos via URL.

#### A23. `INTERNAL_SERVICE_KEY` com fallback hardcoded
- **Arquivos:** `routes/dr_anderson_webhook.py:15`, `services/dr_anderson_agent.py:114`, `routes/anamneses.py:56`
- **Risco:** Atacante que lê o código autentica como serviço interno com `'dr-anderson-internal-key'`.

---

### 🟡 MÉDIOS (18)

| Arquivo:Linha | Descrição | Recomendação |
|---|---|---|
| `routes/auth_decorators.py:27,47` | `_ROLE_BYPASS = {"admin", "superadmin"}` permite bypass total de decorators RBAC | RBAC granular + 2FA para admin |
| `routes/auth_decorators.py:73-167` | `require_permission` aplicado em só 1 blueprint | Aplicar em todos multi-tenant |
| `security_config.py` | `ANONYMIZATION_KEY`, `INTERNAL_SERVICE_KEY`, `WEBHOOK_SECRET_KEY`, `DATABASE_URL` NÃO validados pelo startup | Adicionar à validação obrigatória |
| `.env` (raiz) | Permissões `-rwxrwxrwx` (777) | `chmod 600` |
| `app_cors_livre.py:34` | `MAX_CONTENT_LENGTH=500MB` diverge de `config.py:88=16MB` | Padronizar 16MB |
| `routes/pacientes.py:74` | Mensagem de erro 413 reporta "50MB" hardcoded | Buscar de `current_app.config` |
| `tenant_middleware.py:51-65` | Header `X-Association-ID` é opcional | Tornar obrigatório em rotas multi-tenant |
| `tenant_lib.py:46` | Bypass por superadmin global | Logar ações cross-tenant em auditoria |
| `auth.py` (raiz) | Blueprint antigo `/register` não registrado — código morto | Remover |
| `security_config.py:122-124` | `X-XSS-Protection` deprecated | Remover (mantido apenas via CSP) |
| `security_config.py:127-129` | `Cache-Control: no-store` global | Aplicar só em endpoints com PII |
| `security_config.py:75-78` | Constantes `LOGIN_RATE_LIMIT`, etc. definidas mas não aplicadas | Aplicar via decorators |
| `app_cors_livre.py:59` | `limiter = init_limiter(app)` retorna local, não global | Atribuir em `app.extensions` |
| `services/anonymization_service/app/crypto.py` | Sem audit log de decrypt | Adicionar log de auditoria |
| `services/llm_gateway` (vários) | Envio para DeepSeek/Zhipu/Google sem DPA/SCC documentado | Avaliar Ollama local como default |
| `requirements.txt:13` | `mercadopago==2.2.1` desatualizado | Atualizar SDK oficial |
| `requirements.txt:9` | `psycopg2-binary` sem fixar versão | `>=2.9.9` |
| `models.py` (colunas Paciente) | Sem encryption-at-rest de CPF/CNS | `EncryptedType` (SQLAlchemy-Utils) |

---

### 🟢 BAIXOS (9)

- `security_config.py` — Falta `Permissions-Policy` (camera/mic/geolocation)
- `services/anonymization_service/app/crypto.py` — Sem rotação de chaves Fernet (envelope encryption ou AES-GCM)
- `models.py:764-788` — `LogAtividade` sem enum estruturado em `detalhes`
- `routes/lgpd.py:21-27` — Logs LGPD não registram IP nem UA
- `services/anonymization_service/app/anonymizer.py:62-72` — MD5 para token curto (trocar para SHA-256)
- `routes/patient_auth.py:175-187` — Senha do paciente aceita qualquer string >= 6 chars
- `routes/auth.py:60-185` — Uso inconsistente de `request.get_json(silent=True)`
- `nginx.conf:5` — App não reforça `PREFERRED_URL_SCHEME=https`
- `requirements.txt` — Sem `requirements-dev.txt` nem hashes

---

## Mapa de Risco por Arquivo (Top 10 hotspots)

| Arquivo | Críticos | Altos | Total |
|---------|---------|-------|-------|
| `routes/auth.py` | 2 | 5 | 7 |
| `routes/exames.py` | 0 | 4 | 4 |
| `services/anonymization_service/app/crypto.py` | 1 | 3 | 4 |
| `security_config.py` | 1 | 2 | 3 |
| `app_cors_livre.py` | 0 | 3 | 3 |
| `routes/mercadopago.py` + `routes/webhooks.py` | 1 | 1 | 2 |
| `routes/dynamic_tenant_webhook.py` | 0 | 2 | 2 |
| `routes/dr_anderson_webhook.py` | 0 | 2 | 2 |
| `routes/voice.py` | 0 | 2 | 2 |
| `routes/anuncios.py` | 0 | 2 | 2 |

---

## Validação Empírica (teste de carga — 2026-06-22)

O teste de carga executado contra `https://api.visualsmartflow.com.br` confirmou vários achados:

- **Cenário peak (200 usuários, 3 min):** 46/200 logins falharam com `429 Too Many Requests: 60 per 1 minute` — confirmando que rate-limit não estava aplicado em escala (C4).
- **GET /api/dashboard/stats:** 820 falhas com `500 Internal Server Error: column pacientes.data_revogacao does not exist` — bug real descoberto durante o teste (não estava na lista de achados anteriores).
- **GET /api/pacientes:** 715 falhas com mesmo erro de coluna.
- **Login p95:** 10.000ms (timeout) sob peak — servidor saturado.
- **GET /api/consultas:** 643 requests OK + 555 com 429 — saturação clara.

Estes números devem ser **referência baseline** para medir o impacto das correções P0/P1.

---

## Recomendações de Implementação

### Antes de ir para produção com dados reais:
1. Resolver todos os 5 CRÍTICOS
2. Resolver pelo menos A5, A6, A7, A10, A17 (rotas sem auth + multi-tenant)
3. Adicionar `@jwt_required` em **todos** os blueprints restantes
4. Habilitar HTTPS-only e HSTS preload
5. Configurar CSP estrita (sem unsafe-inline)

### Antes de escalar (acima de 50 usuários):
6. Migrar rate-limit para Redis (storage_uri=`redis://`)
7. Implementar fila assíncrona (Celery) para webhooks
8. Containerizar Ollama (atualmente SPOF no host)

---

**Gerado por:** Claude (MiniMax-M3) · 2026-06-22 · Auditoria read-only
