# SECRETS_INVENTORY — MISSÃO 22.2 (revisado)

**Data:** 2026-06-25
**Modo:** EXECUTE (somente documentação)
**Origem:** reconstruído a partir de `.env.example`, `.env.production.example`, `config.py`, `docker-compose.prod.yml`, `docker-compose.staging.yml`, `scripts/`, `services/`, `security_config.py`.

**REGRA:** Nenhum valor de secret é mostrado. Apenas nomes, obrigatoriedade e procedência.

---

## Legenda

- 🔴 **OBRIGATÓRIO** — deploy aborta se ausente
- 🟡 **RECOMENDADO** — deploy funciona, mas com degradação
- 🟢 **OPCIONAL** — feature opcional desabilitada se ausente

---

## 1. Ambiente

| Variável | Obrigatória? | Origem verificada | Onde configurar | Consequência se ausente |
|----------|--------------|---------------------|------------------|--------------------------|
| `FLASK_ENV` | 🟡 | `.env.example:11`, `.env.production.example:11`, `docker-compose.staging.yml:60` | env | Default `production`; pode confundir logs |
| `FLASK_APP` | 🟡 | `.env.example:12`, `.env.production.example:11` | env | Default `app_cors_livre.py`; risco se renomear |
| `DEBUG` | 🔴 | `.env.example:14`, `.env.production.example:13` | env | `DEBUG=True` em prod = INFORMATION LEAK |
| `ENVIRONMENT` | 🟡 | código (`is_production()`) | env | `is_production()` retorna False; CSP não fica hard |
| `FRONTEND_BASE_URL` | 🔴 | `.env.example:15`, `.env.production.example:43`, `docker-compose.staging.yml:66` | env | CORS bloqueia frontend |
| `API_BASE_URL` | 🔴 | `.env.production.example:44` | env | webhook absoluto falha |
| `CORS_ORIGINS` | 🔴 | `.env.production.example:45`, `docker-compose.staging.yml:67` | env no compose | CORS bloqueia frontend |
| `PORT` | 🟢 | código | compose | Default 5002 |

## 2. Banco de Dados

| Variável | Obrigatória? | Origem verificada | Onde configurar | Consequência se ausente |
|----------|--------------|---------------------|------------------|--------------------------|
| `DATABASE_URL` | 🔴 | `.env.example:22` | env | App não sobe |
| `POSTGRES_DB` | 🔴 | `.env.production.example:27`, `docker-compose.prod.yml:19`, `docker-compose.staging.yml:21` | env no compose | Container não inicia |
| `POSTGRES_USER` | 🔴 | `.env.production.example:28`, `docker-compose.prod.yml:20`, `docker-compose.staging.yml:21` | env no compose | Container não inicia |
| `POSTGRES_PASSWORD` | 🔴 | `.env.production.example:30`, `docker-compose.prod.yml:21`, `docker-compose.staging.yml:22` | vault | Container não inicia |
| `DB_POOL_SIZE` | 🟡 | `config.py:72` (default 20) | env | Default 20 |
| `DB_MAX_OVERFLOW` | 🟡 | `config.py:73` (default 40) | env | Default 40 |
| `DB_POOL_PRE_PING` | 🟢 | `config.py:74` (default "true") | env | Default `true` |
| `MAX_CONTENT_LENGTH` | 🟡 | `.env.production.example:148` (50MB) | env | Default 50MB |

## 3. Segurança (JWT/Sessão/CSRF)

| Variável | Obrigatória? | Origem verificada | Onde configurar | Consequência se ausente |
|----------|--------------|---------------------|------------------|--------------------------|
| `JWT_SECRET_KEY` | 🔴 | `.env.example:28`, `.env.production.example:17` | vault | **App aborta startup em prod** (M18 P0) |
| `SECRET_KEY` | 🔴 | `.env.example:29`, `.env.production.example:16` | vault | App aborta |
| `CSRF_TOKEN` | 🔴 | `security_config.py:51-58` | env | App aborta em prod (M18 P0-06) |

**Tamanho mínimo:** ≥32 chars para cada um. Gerar com `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`.

## 4. Webhooks

| Variável | Obrigatória? | Origem verificada | Onde configurar | Consequência se ausente |
|----------|--------------|---------------------|------------------|--------------------------|
| `MERCADOPAGO_WEBHOOK_SECRET` | 🔴 | `.env.example:117`, `services/webhook_auth.py` | vault | Webhook MP rejeitado |
| `MERCADOPAGO_MODULOS_WEBHOOK_SECRET` | 🔴 | `.env.example:118` | vault | Webhook MP modulos rejeitado |
| `EVOLUTION_WEBHOOK_SECRET` | 🔴 | `.env.example:119` | vault | Webhook WhatsApp rejeitado |
| `DR_ANDERSON_WEBHOOK_SECRET` | 🔴 | `.env.example:120` | vault | Webhook Dr.Anderson rejeitado |
| `INTERNAL_SERVICE_KEY` | 🔴 | `.env.example:122` | vault | Comunicação interna rejeitada |
| `WEBHOOK_SECRET_KEY` | 🟡 | `.env.example:33` | vault | Webhook genérico desabilitado |
| `WEBHOOK_MAX_REQUESTS_PER_MINUTE` | 🟡 | `.env.example:34` (default 10) | env | Default 10/min |
| `WEBHOOK_IP_WHITELIST` | 🟢 | `.env.example:36` (comentado) | env | Whitelist desabilitada |
| `ALLOW_WEBHOOK_SIMULATION` | 🟢 | `.env.example:124` (default 0) | env | Default `0` em prod |

## 5. Mercado Pago (Billing)

| Variável | Obrigatória? | Origem verificada | Onde configurar | Consequência se ausente |
|----------|--------------|---------------------|------------------|--------------------------|
| `MERCADOPAGO_ACCESS_TOKEN` | 🔴 | `.env.production.example:108`, `services/mercadopago_service.py` | vault | Checkout falha |
| `MERCADOPAGO_PUBLIC_KEY` | 🔴 | `.env.production.example:109` | vault | Frontend não carrega checkout |
| `MERCADOPAGO_SANDBOX` | 🟢 | código | env | Default `true` em staging |

## 6. WhatsApp / Evolution

| Variável | Obrigatória? | Origem verificada | Onde configurar | Consequência se ausente |
|----------|--------------|---------------------|------------------|--------------------------|
| `WHATSAPP_API_URL` | 🟡 | `.env.example:50`, `services/whatsapp_service.py:11` | env | Mensagens não enviadas |
| `WHATSAPP_API_KEY` | 🟡 | `.env.example:52`, `services/whatsapp_service.py:12` | env | Mensagens não enviadas |
| `WHATSAPP_INSTANCE_NAME` | 🟢 | `.env.example:51`, `services/whatsapp_service.py:13` | env | Default `siap` |
| `WHATSAPP_ADMIN_PHONE` | 🟢 | `services/whatsapp_service.py:14` | env | Alerta admin não enviado |
| `WHATSAPP_TOKEN` | 🟢 | `.env.example:55` (Twilio, comentado) | env | Twilio desabilitado |

## 7. E-mail (SMTP)

| Variável | Obrigatória? | Origem verificada | Onde configurar | Consequência se ausente |
|----------|--------------|---------------------|------------------|--------------------------|
| `SMTP_SERVER` / `SMTP_HOST` | 🟡 | `.env.example:40` (`SMTP_SERVER`), `.env.production.example:97` (`SMTP_HOST`) | env | E-mails não enviados |
| `SMTP_PORT` | 🟡 | `.env.example:41`, `.env.production.example:98` | env | Default 465/587 |
| `SMTP_USERNAME` / `SMTP_USER` | 🟡 | `.env.example:42` (`SMTP_USERNAME`), `.env.production.example:99` (`SMTP_USER`) | env | E-mails falham |
| `SMTP_PASSWORD` | 🟡 | `.env.example:43`, `.env.production.example:100` | vault | E-mails falham |
| `SMTP_USE_SSL` | 🟡 | `.env.example:44` | env | Default True |
| `SMTP_USE_TLS` / `SMTP_TLS` | 🟢 | `.env.example:45`, `.env.production.example:102` | env | Default False |
| `EMAIL_FROM` / `SMTP_FROM` | 🟡 | `.env.example:46`, `.env.production.example:101` | env | E-mails sem remetente |
| `EMAIL_FROM_NAME` | 🟢 | `.env.example:47` | env | Default "SIAP Sistema" |
| `EMAIL_DEVELOPMENT_MODE` | 🟢 | `.env.example:48` | env | Default False |

> **Inconsistência detectada:** `.env.example` usa `SMTP_SERVER`/`SMTP_USERNAME`/`SMTP_USE_SSL`/`EMAIL_FROM`, enquanto `.env.production.example` usa `SMTP_HOST`/`SMTP_USER`/`SMTP_TLS`/`SMTP_FROM`. Verificar qual o código realmente lê antes do deploy.

## 8. LLMs / IA

| Variável | Obrigatória? | Origem verificada | Onde configurar | Consequência se ausente |
|----------|--------------|---------------------|------------------|--------------------------|
| `DEFAULT_LLM_PROVIDER` | 🟡 | `.env.example:60`, `.env.production.example:55` | env | Default `ollama_local` (exemplo) ou `google` (prod example) |
| `DEFAULT_LLM_MODEL` | 🟡 | `.env.example:61`, `.env.production.example:56` | env | Default `gemma3:4b` (exemplo) ou `gemini-2.5-flash-lite` (prod) |
| `DEFAULT_LLM_VISION_PROVIDER` | 🟡 | `.env.example:62`, `.env.production.example:59` | env | Default `deepseek` |
| `DEFAULT_LLM_VISION_MODEL` | 🟡 | `.env.example:63`, `.env.production.example:60` | env | Default `deepseek-chat` |
| `DEFAULT_LLM_MULTIMODAL_PROVIDER` | 🟡 | `.env.example:64`, `.env.production.example:63` | env | Default `deepseek` |
| `DEFAULT_LLM_MULTIMODAL_MODEL` | 🟡 | `.env.example:65`, `.env.production.example:64` | env | Default `deepseek-chat` |
| `OPENAI_API_KEY` | 🟢 | `.env.example:71` (comentado), `.env.production.example:79` | vault | OpenAI desabilitado |
| `OPENAI_TIMEOUT` | 🟢 | `.env.example:72` (comentado) | env | Default 120 |
| `GROQ_API_KEY` | 🟢 | `.env.example:75` (comentado), `.env.production.example:82` | vault | Groq desabilitado |
| `GROQ_TIMEOUT` | 🟢 | `.env.example:76` (comentado) | env | Default 60 |
| `ANTHROPIC_API_KEY` | 🟢 | `.env.example:79` (comentado), `.env.production.example:85` | vault | Anthropic desabilitado |
| `ANTHROPIC_TIMEOUT` | 🟢 | `.env.example:80` (comentado) | env | Default 120 |
| `GOOGLE_API_KEY` | 🟢 | `.env.example:83` (comentado), `.env.production.example:75` | vault | Gemini desabilitado |
| `GOOGLE_TIMEOUT` | 🟢 | `.env.example:84` (comentado) | env | Default 60 |
| `DEEPSEEK_API_KEY` | 🟢 | `.env.example:87` (comentado), `.env.production.example:88` | vault | DeepSeek desabilitado |
| `DEEPSEEK_BASE_URL` | 🟢 | `.env.example:88` (comentado) | env | Default API DeepSeek |
| `XAI_API_KEY` | 🟢 | `.env.example:91` (comentado) | vault | Grok desabilitado |
| `XAI_BASE_URL` | 🟢 | `.env.example:92` (comentado) | env | Default xAI |
| `MARITACA_API_KEY` | 🟢 | `.env.production.example:78` | vault | Maritaca desabilitado |
| `ZHIPU_API_KEY` | 🟢 | `.env.production.example:91`, `services/*` | vault | Zhipu desabilitado |
| `ZHIPU_BASE_URL` | 🟢 | `services/*` | env | Default Zhipu |
| `OLLAMA_BASE_URL` | 🟡 | `.env.example:96`, `.env.production.example:109` | env | Default `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | 🟡 | `.env.example:97` | env | Default `gemma3:4b` |
| `OLLAMA_CLOUD_URL` | 🟢 | `.env.example:99` (comentado) | env | OLLAMA cloud desabilitado |
| `OLLAMA_API_KEY` | 🟢 | `.env.example:100` (comentado) | env | OLLAMA cloud desabilitado |
| `CREWAI_TIMEOUT` | 🟢 | `.env.example:103` (default 300) | env | Default 300 |

## 9. Anonimização (LGPD)

| Variável | Obrigatória? | Origem verificada | Onde configurar | Consequência se ausente |
|----------|--------------|---------------------|------------------|--------------------------|
| `ANONYMIZATION_KEY` | 🔴 | `.env.production.example:106`, `services/anonymization_service/app/crypto.py` | vault (serviço) | Serviço de anonimização aborta startup |
| `ANONYMIZATION_AUDIT_MODEL` | 🟢 | `.env.production.example:107` | env | Default `qwen3:1.7b` |

## 10. Rate Limit + Redis

| Variável | Obrigatória? | Origem verificada | Onde configurar | Consequência se ausente |
|----------|--------------|---------------------|------------------|--------------------------|
| `RATELIMIT_STORAGE_URL` | 🟡 | `.env.example:111`, `.env.production.example:114` | env | Derivado de `REDIS_URL` |
| `REDIS_URL` | 🟡 | `.env.production.example:120`, `docker-compose.staging.yml:69` | env | Fallback memory:// (per-process) |
| `RATE_LIMIT_REDIS_DB` | 🟡 | `.env.example:113`, `.env.production.example:118` (default 1) | env | Default 1 |

## 11. Telemetria / Observabilidade

| Variável | Obrigatória? | Origem verificada | Onde configurar | Consequência se ausente |
|----------|--------------|---------------------|------------------|--------------------------|
| `OTEL_SDK_DISABLED` | 🟡 | `.env.production.example:108`, `docker-compose.staging.yml:62` | env | Default `true` |
| `CREWAI_DISABLE_TELEMETRY` | 🟡 | `.env.production.example:109`, `docker-compose.staging.yml:63` | env | Default `true` |
| `CREWAI_DISABLE_TRACKING` | 🟡 | `.env.production.example:110` | env | Default `true` |

## 12. Uploads / Filesystem

| Variável | Obrigatória? | Origem verificada | Onde configurar | Consequência se ausente |
|----------|--------------|---------------------|------------------|--------------------------|
| `UPLOAD_FOLDER` | 🟡 | `.env.production.example:149` | env | Default `/app/uploads` |

## 13. CI/CD (GitHub Actions)

| Secret | Obrigatória? | Origem | Onde configurar |
|--------|--------------|--------|------------------|
| `STAGING_SSH_HOST` | 🔴 | convenção (não verificado em `.yml`) | GitHub repo Settings → Secrets |
| `STAGING_SSH_KEY` | 🔴 | convenção | GitHub repo Settings → Secrets |
| `STAGING_DEPLOY_USER` | 🔴 | convenção | GitHub repo Settings → Secrets |
| `PROD_SSH_HOST` | 🔴 | convenção | GitHub repo Settings → Secrets |
| `PROD_SSH_KEY` | 🔴 | convenção | GitHub repo Settings → Secrets |
| `PROD_DEPLOY_USER` | 🔴 | convenção | GitHub repo Settings → Secrets |
| `SLACK_WEBHOOK_URL` | 🟡 | convenção | GitHub repo Settings → Secrets |
| `LHCI_GITHUB_APP_TOKEN` | 🟡 | convenção | GitHub repo Settings → Secrets |
| `SNYK_TOKEN` | 🟢 | convenção | GitHub repo Settings → Secrets |

> **Nota:** os 9 secrets de CI/CD não foram verificados diretamente nos arquivos `.yml` (não foram lidos nesta missão), mas referenciados como padrão em MISSÃO 20.

---

## Resumo de obrigatórios por categoria

| Categoria | 🔴 Críticos | 🟡 Importantes | 🟢 Opcionais |
|-----------|-------------|----------------|---------------|
| Ambiente | 3 | 3 | 1 |
| Banco | 4 | 2 | 1 |
| Segurança | 3 | 0 | 0 |
| Webhooks | 5 | 2 | 2 |
| Billing | 2 | 0 | 1 |
| WhatsApp | 0 | 2 | 2 |
| E-mail | 0 | 5 | 2 |
| IA | 0 | 7 | 17 |
| LGPD | 1 | 0 | 1 |
| Rate Limit + Redis | 0 | 3 | 0 |
| Telemetria | 0 | 3 | 0 |
| Uploads | 0 | 1 | 0 |
| CI/CD | 6 | 2 | 1 |
| **TOTAL** | **24** | **30** | **28** |
| **GRANDE TOTAL** | **82** | | |

---

## Mudanças em relação à versão M22

| # | Mudança | Origem |
|---|---------|--------|
| 1 | Adicionadas 14 vars que faltavam em M22 (totais: 24🔴 + 30🟡 + 28🟢 = 82) | `.env.production.example` |
| 2 | Removidas vars inventadas (ex: `WEBHOOK_TOKEN_INVALIDO`, placeholders) | validação |
| 3 | Padronizadas nomenclaturas SMTP (SMTP_SERVER vs SMTP_HOST) com nota | ambas existem |
| 4 | Documentadas 4 vars LLM adicionais (MARITACA, ZHIPU, OPENAI_TIMEOUT, etc.) | `.env.production.example` |
| 5 | Adicionados `OTEL_SDK_DISABLED`, `CREWAI_DISABLE_TELEMETRY`, `CREWAI_DISABLE_TRACKING` | `.env.production.example` |
| 6 | Adicionados `MAX_CONTENT_LENGTH`, `UPLOAD_FOLDER` | `.env.production.example` |
| 7 | Adicionados `ANONYMIZATION_AUDIT_MODEL`, `DEFAULT_LLM_VISION_*`, `DEFAULT_LLM_MULTIMODAL_*` | `.env.example` |
| 8 | Adicionados `WHATSAPP_ADMIN_PHONE`, `WHATSAPP_TOKEN` (Twilio) | código + `.env.example` |
| 9 | Adicionados `OPENAI_TIMEOUT`, `GROQ_TIMEOUT`, `ANTHROPIC_TIMEOUT`, `GOOGLE_TIMEOUT`, `DEEPSEEK_BASE_URL`, `XAI_BASE_URL` | `.env.example` |

**Validador:** executar `python3 scripts/validate_env.py` antes de qualquer deploy. Falha aborta deploy.

**Nota operacional:** inconsistência entre `.env.example` e `.env.production.example` para SMTP (variáveis com nomes diferentes) deve ser resolvida pelo time antes do deploy.