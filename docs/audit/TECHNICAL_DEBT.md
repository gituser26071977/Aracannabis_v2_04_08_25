# TECHNICAL_DEBT.md — Dívidas Técnicas Classificadas por Criticidade

**Data:** 2026-07-22
**Escopo:** read-only — inventário do passivo técnico acumulado.
**Escala:** 🔴 Crítica → 🟠 Alta → 🟡 Média → 🟢 Baixa

---

## 1. Divida Crítica (🔴 — bloqueia MVP comercial)

### 1.1 RBAC não aplicado em endpoints

- **Impacto:** qualquer usuário autenticado tem acesso a qualquer endpoint que não faça verificação manual
- **Evidência:** `routes/auth_decorators.py` define `@require_permission` mas 106 permissions e 0 aplicações em produção
- **Workaround atual:** verificações manuais espalhadas em ~30 rotas
- **Bloqueio:** produção comercial sem isto é inviável juridicamente
- **Esforço para resolver:** ~1 sprint + 3 sprints de aplicação massiva

### 1.2 Tenant Isolation divergente (3 mecanismos)

- **Impacto:** inconsistência em como tenant é resolvido; potencial cross-tenant leak
- **Evidência:** `tenant_middleware.py` (Flask) + `_helpers.py` (Sprint 4 helpers) + `platform/tenant/*` resolver
- **Bloqueio:** LGPD compliance depende de isolamento correto
- **Resolução:** ADR-0007 + `@tenant_required` cross-cutting

### 1.3 SQLKnowledgeRepository não implementado

- **Impacto:** Sprint 4.4 Knowledge Engine não tem persistência SQL
- **Evidência:** apenas `InMemoryKnowledgeRepository` + migration SQL criada mas sem classe
- **Bloqueio:** Knowledge Engine não vai pra produção sem isto
- **Esforço:** 1 sprint (mappers prontos em `infrastructure/mappers.py`)

### 1.4 Refresh Token ausente no Flask login

- **Impacto:** usuários precisam logar novamente a cada 12h
- **Evidência:** `routes/auth.py` cria apenas access_token
- **AraOS provider** tem refresh 30d mas não está integrado
- **Bloqueio:** UX comercial inviável sem refresh (12h limite comercial)
- **Esforço:** 0.5 sprint (provedor já existe)

### 1.5 MFA sem implementação operacional

- **Impacto:** campo `mfa_enabled` em modelo + evento `MFA_ENABLED`, sem OTP/TOTP/recovery codes
- **Evidência:** `models.py` + event catalog
- **Bloqueio:** Healthcare compliance depende de MFA em produção comercial
- **Esforço:** 1-2 sprints (TOTP puro-Python é trivial; integração com provider AraOS é mais custosa)

### 1.6 SECRET_KEY hardcoded

- **Impacto:** segredo dev/staging `SIAP_SECRET_REDACTED` < 32 chars
- **Evidência:** `docker-compose.siap.yml`
- **Bloqueio:** se este valor for para produção, qualquer um com acesso ao compose quebra JWT
- **Esforço:** 0.1 sprint (variável de ambiente)

### 1.7 CSRF não aplicado em produção

- **Impacto:** helper existe mas 0 endpoints usam `@csrf_protect`
- **Evidência:** `security_config.py` + `tests/security/test_p0_remediation_m18.py` (única aplicação)
- **Bloqueio:** POSTs autenticados vulneráveis a CSRF
- **Esforço:** 0.5 sprint de aplicação massiva

## 2. Divida Alta (🟠 — degrada qualidade mas não bloqueia MVP mínimo)

### 2.1 Audit Ledger central AraOS desconectado

- **Impacto:** `routes/*` gravam `LogAtividade` manual; ledger central SHA-256 não recebe
- **Evidência:** `araos/platform/audit/ledger.py` pronto mas não integrado
- **Esforço:** 1 sprint (middleware + adapter)

### 2.2 Knowledge Endpoint REST ausentes

- **Impacto:** zero rotas `/api/knowledge/*`
- **Evidência:** `interfaces/rest/` não existe; 14 endpoints declarados no plano mas 0 implementados
- **Esforço:** 1 sprint (W3 completo)

### 2.3 KnowledgeUnitOfWork ausente

- **Impacto:** transação entre repositórios + event store não coordenada
- **Evidência:** `infrastructure/unit_of_work.py` não existe
- **Esforço:** 0.5 sprint (SqlAlchemyClinicalEventStore autocommit param já adicionado em W1.6)

### 2.4 hypothesis_id cross-tenant leak (manifest/code gap)

- **Impacto:** SHA-256 inclui `rule_id|sorted(gene_ids)|sorted(correlation_ids)|claim` — sem tenant_id
- **Evidência:** `hypothesis.py:68-75`; manifest declara `tenant_id|rule_name|gene_ids_sorted|correlation_id`
- **Fix:** adicionar tenant_id no composition (task #197)
- **Esforço:** 0.2 sprint

### 2.5 3 diferentes ORM styles

- **Impacto:** learning curve para novos devs; debugging misto
- **Evidência:**
  - Legacy: Flask-SQLAlchemy (`db.Model`)
  - AraOS Platform: SQLAlchemy 2.0 declarative (`Base` + `Mapped`)
  - Knowledge: pure Python dataclasses + SQLAlchemy 2.0 models
- **Esforço:** ~2 sprints para unificar (BAIXA prioridade estratégica)

### 2.6 Frontend sem testes

- **Impacto:** regressões silenciosas
- **Evidência:** 0 arquivos `.test.js` em `frontend/src/`
- **Esforço:** 1-2 sprints de setup + criação de tests críticos

### 2.7 ADR-0007 ausente

- **Impacto:** V1/V2 e hypothesis_id gap sem trilha formal de decisão
- **Evidência:** numeração tem gap em 0007
- **Esforço:** 0.1 sprint (redação)

### 2.8 `result_json` TEXT vs JSONB inconsistência

- **Impacto:** decisions de ADR-0008 (JSONB para `knowledge_graphs.graph_json`) pode conflitar com `result_json` TEXT em `knowledge_research_sessions`
- **Evidência:** `migrations/versions/REDACTED.py` usa TEXT para research_sessions (bit-identical research reproduction) e JSONB para graphs
- **Esforço:** ADR + ajuste (não bloqueante)

### 2.9 `clinical/twin` stub vs `routes/twin.py` produção

- **Impacto:** dois "twins" paralelos; candidatos a consolidação
- **Evidência:** `clinical/twin/` é stub; rota Flask funciona
- **Esforço:** 0.2 sprint para design

### 2.10 JWT provider paralelo (Flask × AraOS)

- **Impacto:** dois sistemas de claims diferentes
- **Bloqueio baixo:** Flask emite SEM tenant_id; AraOS emite com claims ricos
- **Esforço:** 0.5 sprint se deseja unificar

## 3. Divida Média (🟡 — qualidade técnica)

### 3.1 Coverage artifacts zerados

- **Impacto:** `coverage/coverage-final.json = {}`; report não confiável
- **Evidência:** CI roda pytest-cov mas resultado zerado
- **Esforço:** 0.1 sprint (verificar config coverage)

### 3.2 SQLite vs PostgreSQL drift

- **Impacto:** testes unitários rodam SQLite; CI sem PostgreSQL
- **Evidência:** Sprint 4.5 W1.7 planeja PostgreSQL 16 test container
- **Esforço:** 0.5 sprint (docker-compose.test.yml + script)

### 3.3 i18n ausente

- **Impacto:** pt-BR hardcoded em ~13.000 linhas
- **Esforço:** 3-4 sprints de migração completa (BAIXA prioridade)

### 3.4 AraFlow ADRs 001-015 sem arquivos físicos

- **Impacto:** índice numérico sem trilha
- **Esforço:** 0.2 sprint de catalogação

### 3.5 5 clinical BCs × 3 ORM styles × tenant triplicado

- **Impacto:** complexidade cognitiva
- **Esforço:** longo prazo (refatoração arquitetural)

### 3.6 Schema legacy sem soft delete

- **Impacto:** `log_atividade` legacy persiste; LGPD delete é manual
- **Esforço:** 1-2 sprints de migração

### 3.7 File upload sem inspeção

- **Impacto:** uploads PDF/foto sem inspeção magic bytes
- **Esforço:** 0.2 sprint (ClamAV + MIME real)

### 3.8 CSRF endpoint `/api/csrf-token` expõe token

- **Impacto:** processo-token atual é global; ideal é per-session
- **Esforço:** 0.1 sprint

### 3.9 `aios._helpers.py` middleware engole exceções

- **Impacto:** debugging perde contexto
- **Esforço:** 0.05 sprint

### 3.10 `clinical/profile` código legado

- **Impacto:** redundante com `specialties/cannabis/profile`
- **Esforço:** 0.1 sprint

### 3.11 V1/V2 violações ativas

- **Impacto:** arquitetura não 100% limpa; ADR-0007 pendente
- **V1:** `clinical/timeline/app/query.py:23` importa `append` de `event_store/store.py` (manifest re-exporta função de infrastructure)
- **V2:** `knowledge/domain/clinical_genome.py:45` importa `ReplayEngine` de `genome/app/replay_engine.py`
- **Esforço:** 1 sprint (ADR + refactor)

### 3.12 SPRINT_4_5_REST_INVENTORY.md inconsistências internas

- **Impacto:** texto declara 14 endpoints, tabela soma 18
- **Esforço:** 0.05 sprint

### 3.13 JWT revocation em memória

- **Impacto:** `_revoked_jtis` set local do processo; reinício = token revive
- **Esforço:** 0.5 sprint (Redis adapter)

## 4. Divida Baixa (🟢 — melhorias incrementais)

### 4.1 `style-src 'unsafe-inline'` no CSP

- **Impacto:** XSS via CSS possível (raro)
- **Esforço:** 0.05 sprint

### 4.2 Paginação / ordenação não padronizadas

- **Impacto:** cada endpoint Flask retorna estrutura diferente
- **Esforço:** ~1 sprint

### 4.3 64 tabelas sem nomenclatura única

- **Impacto:** mistura snake_case + CamelCase (mas em SQL tudo vira snake)
- **Esforço:** BAIXA

### 4.4 CORS allowlist com duplicação

- **Impacto:** `192.168.0.104:3000` duplicado
- **Esforço:** 0.01 sprint

### 4.5 Migration `0331305d2b3c` dead

- **Impacto:** filename vs conteúdo divergente
- **Esforço:** 0.02 sprint (rename)

### 4.6 Dockerfiles duplicados (`Dockerfile.dockerfile` + `Dockerfile.js`)

- **Impacto:** redundância
- **Esforço:** 0.02 sprint

### 4.7 Páginas órfãs (Neuro + IntelligentImportPage)

- **Impacto:** frontend tem 3 arquivos sem rota
- **Esforço:** 0.02 sprint

### 4.8 Comentários `# Em produção: Redis/DB` no código

- **Impacto:** reconhecendo débito sem ação
- **Esforço:** depende da issue específica

### 4.9 Re-exportação de `event_store.append` em timeline.app

- **Impacto:** V1 violation, registrada
- **Esforço:** ADR + refactor

### 4.10 Paginação/ordenação no frontend

- **Impacto:** tabelas não ordenam consistentemente
- **Esforço:** 0.5 sprint

## 5. Resumo Quantitativo

| Severidade | Total | Esforço agregado |
|:---:|:---:|---:|
| 🔴 Crítica | 7 | ~5 sprints |
| 🟠 Alta | 10 | ~6 sprints |
| 🟡 Média | 13 | ~6 sprints |
| 🟢 Baixa | 10 | ~0.5 sprint |
| **Total** | **40** | **~17 sprints** |

Em 4-6 sprints de foco, **MVP comercial mínimo** é viável atacando prioritariamente 🔴 Crítica + 🟠 Alta #2.1-2.3.

## 6. Dependências Circulares Entre Débitos

```
1. RBAC não aplicado
   └─ depende de #tenant_required centralizado (1.2)
      └─ depende de ADR-0007 (2.7) + helper em platform

2. Knowledge Engine backend completo
   ├─ SQLKnowledgeRepository (1.3)
   ├─ KnowledgeUnitOfWork (2.3)
   ├─ REST endpoints (2.2)
   └─ Frontend dashboard
      └─ depende de Knowledge REST

3. Audit central
   └─ depende de RBAC estabilizado
      └─ depende de tenant_required
```

## 7. Decisão Recomendada

Para MVP comercial em horizonte mínimo:
1. 🔴 Crítica: 7 débitos (5 sprints agregados)
2. 🟠 Prioridade 2.1-2.3 (audit + Knowledge REST/UoW) (3 sprints)
3. **Trilha MVP Sprint 4.5-4.10 conforme EXECUTIVE_SUMMARY.md**

---

**Ver também:**
- [ARAOS_SYSTEM_AUDIT.md](ARAOS_SYSTEM_AUDIT.md)
- [DEAD_CODE_REPORT.md](DEAD_CODE_REPORT.md)
- [MVP_GAP_ANALYSIS.md](MVP_GAP_ANALYSIS.md)
