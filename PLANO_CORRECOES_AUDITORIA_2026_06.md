# Plano de Correções — Pós-Auditoria AraOS

**Data:** 2026-06-22
**Origem:** Auditoria em `docs/AUDITORIA_SEGURANCA_2026_06.md` + `docs/AUDITORIA_LGPD_2026_06.md` + `docs/AUDITORIA_CAPACIDADE_2026_06.md` + `RELATORIO_TESTE_CARGA_2026_06.md`
**Total de itens:** 77 (13 P0 + 15 P1 + 49 P2)

---

## Como ler este documento

Cada item tem:
- **#** — número sequencial
- **Tema** — área afetada
- **Item** — descrição executável
- **Arquivo:Linha** — onde aplicar
- **Impacto** — risco mitigado / capacidade ganha
- **Esforço** — horas estimadas
- **Aceitação** — como validar

---

## 🟥 Onda P0 — Críticos (1 sprint = ~5 dias úteis)

**Total: 13 itens · Esforço: ~40 horas · Pode paralelizar entre 2-3 devs**

### Segurança

| # | Tema | Item | Arquivo:Linha | Impacto | Esforço |
|---|------|------|---------------|---------|---------|
| 1 | Auth | Remover `GET /api/auth/create-admin` (público) ou exigir `@jwt_required` + role admin + senha aleatória | `routes/auth.py:26-56` | Fecha backdoor de admin | 2h |
| 2 | Crypto | Abortar startup se `ANONYMIZATION_KEY` ausente em prod + remover `print()` da chave | `services/anonymization_service/app/crypto.py:10-17` | Evita perda irrecuperável de dados + vazamento em logs | 2h |
| 3 | Webhooks | Validar HMAC SHA256 (`x-signature`) em MercadoPago, Evolution, Dr.Anderson, módulos (forçar POST) | `routes/mercadopago.py:119-159`, `routes/dynamic_tenant_webhook.py:13-93`, `routes/dr_anderson_webhook.py:108-181`, `routes/modulos.py:352-411` | Fecha 4 vetores de injeção de payload + gasto de tokens LLM | 6h |
| 4 | Auth | Adicionar `@jwt_required` em `routes/exames.py`, `routes/voice.py`, `routes/anuncios.py` | `routes/exames.py:16-141`, `routes/voice.py:28-122`, `routes/anuncios.py:129-247` | Fecha 3 vetores de vazamento cross-tenant | 3h |
| 5 | Login | Adicionar `@limiter.limit("5/min; 20/hour")` em `/auth/login` + storage Redis | `routes/auth.py:111`, `security_config.py:142` | Mitiga brute-force + DDoS | 2h |
| 6 | Auth | Remover `sanitize_input()` aplicado em senha (quebra senhas com `<>'";`) | `routes/auth.py:127-128` | Restaura login para usuários com senha forte | 1h |

### LGPD

| # | Tema | Item | Arquivo:Linha | Impacto | Esforço |
|---|------|------|---------------|---------|---------|
| 7 | Consentimento | Publicar termo versionado (`/politica-privacidade` em rota real) + bloquear ativação de paciente sem aceite | `routes/patient_auth.py:26-147`, `routes/lgpd.py:82-90` | Alinhamento ao art. 9º + art. 11º | 4h |
| 8 | Direitos titular | Criar `/api/patient/me/revogar-consentimento` (art. 18, IX) | novo endpoint em `routes/patient_portal.py` | Alinhamento ao art. 18, IX | 3h |
| 9 | Direitos titular | Criar `/api/patient/me/solicitar-eliminacao` (art. 18, VI) — workflow com anonimização progressiva | novo endpoint + migration de soft-delete em `Paciente` | Alinhamento ao art. 18, VI + CFP/CRM 20 anos | 6h |
| 10 | DPO | Designar DPO + publicar email de contato no termo | sem código (documentação + admin) | Alinhamento ao art. 41 | 1h |

### Capacidade

| # | Tema | Item | Arquivo:Linha | Impacto | Esforço |
|---|------|------|---------------|---------|---------|
| 11 | Banco | Aplicar fix SQL: `ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP` + adicionar coluna em `models.py` | nova migration `REDACTED.py` | **Resolve bug crítico detectado no teste de carga** — `/api/dashboard/stats` e `/api/pacientes` quebrados | 1h |
| 12 | Pool PG | Reduzir `pool_size=5 + max_overflow=10` + subir `max_connections=200` no PG | `config.py:55-61` + init PG no `docker-compose.prod.yml` | Suporta 500+ conexões sem estourar | 2h |
| 13 | Recursos | Adicionar `deploy.resources.limits` em todos containers prod + `--max-requests 1000 --max-requests-jitter 100` no gunicorn | `docker-compose.prod.yml` | Previne OOM + recicla workers com memory leak | 3h |

**Subtotal: ~36h de trabalho técnico + ~4h de overhead (testes, code review, deploy)**

---

## 🟧 Onda P1 — Altos (2 sprints = ~10 dias úteis)

**Total: 15 itens · Esforço: ~80 horas**

### Segurança

| # | Tema | Item | Arquivo:Linha | Esforço |
|---|------|------|---------------|---------|
| 14 | JWT | Implementar access (15min) + refresh (7d) tokens + `JWT_BLOCKLIST_ENABLED` | `config.py:77`, `routes/auth.py:168` | 6h |
| 15 | Segredos | Implementar `validate_required_secrets()` cobrindo JWT_SECRET_KEY, SECRET_KEY, ANONYMIZATION_KEY, INTERNAL_SERVICE_KEY, WEBHOOK_SECRET_KEY + remover fallbacks hardcoded | `security_config.py`, `config.py:27-30` | 4h |
| 16 | Uploads | Validar MIME real com `python-magic` + renomear para UUID | `routes/exames.py:13-14`, `routes/pacientes.py:11-15` | 4h |
| 17 | Uploads | Integrar ClamAV via `pyclamd` em fila assíncrona | novo worker | 8h |
| 18 | Multi-tenant | Adicionar filtro manual de `associacao_id` em raw SQL de `routes/sintomas.py` | `routes/sintomas.py:193-371` | 3h |
| 19 | Headers | CSP estrita (remover `unsafe-inline`/`unsafe-eval` + adicionar nonces) | `security_config.py:111-130` | 6h |
| 20 | CSRF | Decidir: aplicar `@csrf_protect` em rotas mutativas OU remover e marcar como SPA-only same-origin | `security_config.py:201-224` | 4h |
| 21 | Logging | Remover PII de logs (CPF, e-mail, hash de senha) + mascaramento | `tools/importer/import_excel.py:124`, `routes/auth.py:117,130,144-149`, `routes/pacientes.py:281,381` | 4h |
| 22 | Deps | Pinning rigoroso de versões + `pip-audit` no CI | `requirements.txt` | 4h |

### LGPD

| # | Tema | Item | Arquivo:Linha | Esforço |
|---|------|------|---------------|---------|
| 23 | Cripto | Criptografar PII em repouso (CPF, CNS, e-mail, endereço, data_nascimento) com Fernet envelope + KMS | `models.py:193-197` | 16h |
| 24 | Cripto | Substituir MD5 por SHA-256 em token de anonimização + KMS/rotação de chaves | `services/anonymization_service/app/anonymizer.py:62-72` | 6h |
| 25 | Direitos | Criar `/api/patient/me/export` em JSON+CSV (art. 18, II + V) | novo endpoint em `routes/patient_portal.py` | 6h |
| 26 | Direitos | Criar `/api/patient/me/anonimizar` (art. 18, IV) | novo endpoint | 4h |
| 27 | Retenção | Job mensal de retenção de logs (manter 5 anos; expurgar após) | novo cron + script | 4h |
| 28 | Retenção | Substituir hard delete de paciente por soft delete + anonimização progressiva | `routes/pacientes.py:548-587` | 8h |

### Capacidade

| # | Tema | Item | Arquivo:Linha | Esforço |
|---|------|------|---------------|---------|
| 29 | Backend | Aumentar gunicorn para 4 workers × 4 threads `--worker-class gthread` + `--timeout 60 --graceful-timeout 30` | `docker-compose.prod.yml:93` | 1h |
| 30 | Índices | Migration adicionando `db.Index` em TODAS as FKs (paciente_id, profissional_id, associacao_id, consulta_id) | nova migration | 4h |
| 31 | N+1 | Reescrever `/api/dashboard/stats` com subquery + group_by (eliminar loop com query por paciente) | `routes/dashboard.py:41-67` | 4h |
| 32 | Paginação | Adicionar `?limit=50&offset=0` em TODOS os `.all()` de listagem (pacientes, dosagens, consultas, etc.) | múltiplos routes | 8h |
| 33 | Cache | Conectar Redis ao app + cache de queries estáticas (planos, módulos, catálogo) com TTL 5min | `config.py` + `routes/planos.py`, `routes/catalogo_routes.py` | 6h |
| 34 | Assíncrono | Mover LLM/WhatsApp/VSF para Celery + Redis (fila + polling) | `routes/ai_clinical.py`, `routes/consultas.py`, `services/vsf_bridge.py` | 16h |

---

## 🟨 Onda P2 — Médios/Baixos (backlog)

**Total: 49 itens · Esforço: ~150 horas** (estimado)

### Segurança (18 itens)
- Validar algoritmo JWT explicitamente
- Remover `MAX_CONTENT_LENGTH=500MB` (padronizar 16MB)
- Adicionar `Permissions-Policy` (camera, mic, geolocation)
- RBAC granular (substituir `_ROLE_BYPASS`)
- Aplicar `require_permission` em todos os blueprints multi-tenant
- Audit log de decrypt no `anonymization_service`
- Remover blueprint antigo em `auth.py` raiz
- Tornar `X-Association-ID` header obrigatório
- Auditar ações cross-tenant de superadmin
- E mais 9 itens (ver `docs/AUDITORIA_SEGURANCA_2026_06.md`)

### LGPD (7 itens)
- Dicionário de finalidades por campo
- Consentimento granular (por finalidade: IA, pesquisa, marketing, comunicação)
- Consentimento destacado para dados sensíveis (saúde)
- Migração de Ollama local para evitar envio de dados a China
- DPA/SCC documentado com DeepSeek/Zhipu/Google
- RIPD (Relatório de Impacto à Proteção de Dados)
- Política de força de senha do paciente (Zxcvbn / NIST)

### Capacidade (10 itens)
- Tuning de PostgreSQL (shared_buffers, work_mem)
- PgBouncer em frente ao PG (transaction pooling)
- RLS (Row Level Security) como segunda camada de defesa multi-tenant
- Streaming de export (CSV/Excel em chunks)
- Logs estruturados com JSON formatter + rotação
- Monitoring com Prometheus + Grafana
- Healthcheck no backend
- Cache de Brasil API com TTL 24h
- Containerizar Ollama (SPOF no host)
- Read replicas do PG

### Diversos (14 itens)
- 4 melhorias médias em rotas
- 4 melhorias em models
- 6 melhorias em infraestrutura (Docker, Nginx)

---

## 📅 Cronograma Sugerido

```
Semana 1 (P0):
  Seg-Ter: #1-3 (Auth + Crypto + Webhooks)
  Qua:     #4-6 (Rotas sem auth + Login + sanitize)
  Qui:     #7-9 (LGPD crítico: termo, revogar, eliminar)
  Sex:     #10-13 (DPO + fix data_revogacao + PG pool + recursos)
  
Semana 2-3 (P1 Segurança):
  Seg-Sex semana 2: #14-22 (JWT, segredos, uploads, CSRF, logs, deps)
  Seg-Sex semana 3: testes, code review, deploy parcial

Semana 4-5 (P1 LGPD + Capacidade):
  Seg-Sex semana 4: #23-28 (LGPD restante)
  Seg-Sex semana 5: #29-34 (Capacidade)

Semana 6+ (P2 backlog):
  Conforme prioridade do negócio
```

---

## ✅ Validação Pós-Correções

Após cada onda, reexecutar:
```bash
# regressão
locust -f tests/load/locustfile.py --headless \
  --host=https://api.visualsmartflow.com.br \
  -u 50 -r 5 -t 5m \
  --html reports/regression_baseline.html --csv reports/regression_baseline
```

**Critérios de aceitação por onda:**

| Onda | Failure rate em 50u/5m | p95 em 200u/3m | LGPD |
|------|------------------------|------------------|------|
| P0 | < 30% | < 1000ms | termo + revogar OK |
| P1 | < 5% | < 500ms | 5 endpoints `/me/*` funcionando |
| P2 | < 1% | < 200ms | DPO + RIPD + DPA publicados |

---

## 🚦 Critério para começar a Onda P0

**Pré-requisitos:**
- [ ] Aprovar este plano com equipe + gestão
- [ ] Definir dono de cada item
- [ ] Configurar branch `feat/auditoria-2026-06` no Git
- [ ] Alinhar com equipe jurídica sobre LGPD (#10, #15-18 LGPD) — DPO deve ser designado ANTES de ir para prod
- [ ] Backup completo do banco de produção antes de aplicar fix `data_revogacao` (#11)
- [ ] Janela de manutenção programada para deploy de correções de pool PG (#12)

---

**Gerado por:** Claude (MiniMax-M3) · 2026-06-22 · Roadmap de 77 correções em 3 ondas
