# MVP_GAP_ANALYSIS.md — Análise Objetiva do que Falta para o MVP

**Data:** 2026-07-22
**Escopo:** read-only — gap analysis contra um MVP comercial mínimo.
**Definição de MVP:** software funcional em produção comercial, LGPD/ANVISA-compliant, multi-tenant, com persistência completa e dashboard mínimo.

---

## 1. Definição do MVP Comercial Mínimo

Para ser "MVP comercial", o AraOS precisa atender:

| Critério | Justificativa |
|---|---|
| Persistência multi-tenant funcional | LGPD requirement |
| Autenticação robusta (JWT + refresh + MFA opcional) | Compliance |
| RBAC aplicado em endpoints sensíveis | Auditoria |
| Audit log automático | Compliance |
| CSRF aplicado em mutações | Segurança básica |
| Tenant isolation único e consistente | LGPD |
| Dashboard básico funcional | UX comercial |
| 0 endpoints Knowledge REST | Sem isto, o diferencial competitivo não está exposto |

## 2. Estado Atual vs MVP

### 2.1 O que já atende critérios MVP

| Critério | Estado | Evidência |
|---|---|---|
| Tenant isolation schema | ✅ | araos_organizations + composite PKs |
| Autenticação JWT | ✅ | flask-jwt-extended |
| Audit Log | 🟡 | hash chain pronto (AraOS), mas rotas usam LogAtividade manual |
| Persistência multi-tenant (legado) | ✅ | associacao_id em produção |
| Pacientes + Clínico básico | ✅ | rotas funcionais |
| 9 escalas neuropsicológicas | ✅ | Sprint 1+2 completas |
| Voice Sessions | ✅ | sub-produto funcional |
| Billing MercadoPago | ✅ | produção |
| Followup | ✅ | rotas funcionais |
| AI integration | ✅ | ai_management + crew_ai |
| Anonymization | ✅ | container read_only |

### 2.2 O que NÃO atende critérios MVP

| Critério | Bloqueio | Esforço |
|---|---|---:|
| RBAC aplicado | 0 endpoints com @require_permission | 1-3 sprints |
| Tenant isolation UNIFICADO | 3 mecanismos divergentes | 1 sprint (ADR + decorator) |
| Refresh token | Provider AraOS paralelo | 0.5 sprint |
| MFA operacional | Modelo existe, sem OTP/TOTP | 1-2 sprints |
| CSRF aplicado | Helper existe, 0 aplicação | 0.5 sprint |
| Audit automático | Código pronto, sem integração | 1 sprint |
| Knowledge REST endpoints | 0 implementados | 1 sprint |
| Knowledge Frontend dashboard | Wave 4 não implementada | 1 sprint |
| SQLKnowledgeRepository | Não existe | 1 sprint |
| Frontend tests | 0 arquivos | 1-2 sprints |

## 3. Bloqueadores Críticos para MVP (Top 10)

| # | Bloqueador | Impacto | Esforço | Caminho de Resolução |
|---|---|---|---:|---|
| 1 | RBAC não aplicado | Permite escalação de privilégios | 3 sprints | ADR-0009 + aplicação massiva |
| 2 | Tenant isolation divergente | Cross-tenant leak risk | 1 sprint | ADR-0007 + decorator |
| 3 | MFA sem implementação | Compliance bloqueia | 1.5 sprints | TOTP + integração |
| 4 | Audit central desconectado | Auditoria falha LGPD | 1 sprint | Middleware + decorator |
| 5 | CSRF não aplicado | Mutações inseguras | 0.5 sprint | Cross-cutting decorator |
| 6 | SECRET_KEY hardcoded | Secret em produção | 0.1 sprint | Variável ambiente |
| 7 | SQLKnowledgeRepository | Knowledge sem persistência | 1 sprint | Mappers + sql.py |
| 8 | REST /api/knowledge/* | Knowledge sem exposição REST | 1 sprint | Wave 3 |
| 9 | Dashboard Knowledge read-only | Sem UI Knowledge | 1 sprint | Wave 4 |
| 10 | hypothesis_id cross-tenant leak | Inconsistência detectada | 0.2 sprint | task #197 |

## 4. Bloqueadores Não-Críticos para MVP (registro)

- Frontend sem testes (qualidade, não bloqueador)
- i18n ausente (mercado único)
- Cobertura artifacts zerados (qualidade de report)
- Schema legacy sem soft delete (LGPD delete é manual hoje)
- File upload sem inspeção (risco latente)
- JWT revocation in-memory (risco latente)
- V1/V2 violações (precisam ADR-0007 mas não impedem MVP)
- 5 clinical BCs × 3 ORM styles (cognitive load)

## 5. Caminho Mais Curto para MVP — Trilha A (Knowledge + Segurança)

### Sprint 4.5 (em curso, ~5 dias)

| Tarefa | Status | Categoria |
|---|---|---|
| ✅ G1-G5 Pre-Wave Governance Gates | entregue | foundational |
| ✅ W1.1 Alembic Migration | entregue | foundational |
| ✅ G3 KnowledgeRepository tenant-bound ABC | entregue | foundational |
| ✅ W1.3 mappers.py | entregue (585 linhas) | foundational |
| 🟡 W1.3 SQLKnowledgeRepository class | **PENDENTE** | MVP core |
| 🟡 W1.5 KnowledgeUnitOfWork | **PENDENTE** | MVP core |
| 🟡 W1.7 PostgreSQL integration tests | **PENDENTE** | MVP core |
| 🟡 hypothesis_id fix | **PENDENTE** | MVP core |

### Trilha A estimativa (após Sprint 4.5)

| Sprint | Foco | Entregas |
|---|---|---|
| Sprint 4.6 | Wave 3 + Audit + RBAC core | 14 endpoints REST Knowledge + Audit middleware cross-cutting + 5 permissions aplicadas nos Knowledge endpoints |
| Sprint 4.7 | Wave 4 Dashboard + Frontend tests base | KnowledgeGraphViewer + CohortDashboard + 10 testes React Testing Library |
| Sprint 4.8 | Tenant cross-cutting + CSRF + Refresh | @tenant_required aplicado massivamente + @csrf_protect + Flask refresh token |
| Sprint 4.9 | MFA + ADR-0007 + hypothesis_id fix | TOTP + ADR-0007 resolvendo V1/V2 + tenant_id em hypothesis |
| Sprint 4.10 | Smoke E2E produção + housekeeping | Smoke complete pipeline + remove dead code + Wiki docs |

**Total:** 5 sprints após Sprint 4.5 (~10 semanas) → MVP Knowledge comercial viável.

## 6. Caminho Mais Curto para MVP — Trilha B (Legado SIAP)

| Sprint | Foco | Entregas |
|---|---|---|
| Sprint A | Tenant isolation unificado | Middleware Flask final + remover divergência |
| Sprint B | RBAC core aplicado | @require_permission em 57 blueprints (mínimo 3 sprints paralelos a 4.5) |
| Sprint C | MFA + Audit + Refresh + CSRF | All already mentioned |

**Total:** 3 sprints paralelos ao Sprint 4.5 (~6 semanas) → MVP SIAP legado endurecido.

## 7. Recomendação

**Recomendação primária:** Trilha A (Knowledge Engine) primeiro.
- Knowledge Engine é o diferencial competitivo (5 sprints já investidos)
- Está 75% concluído (não 100%, mas muito perto)
- Já tem ADR e tests rigorosos

**Execução paralela:** Trilha B em paralelo a partir de Sprint 4.5.
- Trilha B preserva o legado em produção
- Trilha B pode usar um developer paralelo

**Decisão-chave:** Sprint 4.5 W1.3 (SQLKnowledgeRepository) **NÃO pode ser adiada novamente** sem re-pivot. É a fundação de toda a Trilha A.

## 8. Riscos Calculados para MVP

| # | Risco calculado | Probabilidade | Impacto |
|---|---|:---:|:---:|
| 1 | RBAC atrasa 3 sprints (estimativa subestimada) | Média | Crítico |
| 2 | Sprint 4.5 W1.3 encontra issue estrutural em Knowledge domain | Baixa | Alto (re-pivot) |
| 3 | MFA integra com provider existente pero UI/UX complicada | Alta | Médio |
| 4 | PostgreSQL tests revelam bugs fora Hibernate | Média | Alto |
| 5 | Frontend dashboard adiciona complexidade de bundle | Alta | Baixo |
| 6 | V1/V2 violations exigem refactor fora de sprint | Média | Crítico |
| 7 | Tenant cross-cutting causa regressão massiva | Média | Crítico |
| 8 | Sprint 4.6 não fecha no prazo | Alta | Alto |

## 9. Métricas de Saída do MVP

| Métrica | Target MVP |
|---|---|
| Cobertura de testes core | ≥ 85% |
| Testes | ≥ 2.000 funções |
| Endpoints com @require_permission | ≥ 50 (core flows) |
| Audit entries por mutação | 100% |
| Tenant cross-cutting | 100% rotas |
| Security headers | 100% rotas |
| CSRF aplicado | 100% mutações |
| Refresh token | 100% sessões |
| MFA setup | 100% admins |
| Permissions matrix publicada | ✅ |
| Documentação REST pública | ✅ |
| Load test (100 RPS sustained 1min) | ✅ |
| LGPD delete (right to be forgotten) | ✅ |
| i18n mínimo (pt-BR + en) | opcional |

## 10. Pós-MVP (próxima onda)

Após MVP, próximos passos hipotéticos (NÃO executados):

| Onda | Tema | Sprints |
|---|---|---:|
| Pós 1 | + Escalas (ABC, PSQI, AQ, Conners — Sprint 3.6) | 1 |
| Pós 2 | Clinical Graph camada relacional | 2-3 |
| Pós 3 | Longitudinal Digital Twin | 2-3 |
| Pós 4 | i18n mínimo (pt-BR + en) | 2 |
| Pós 5 | ML Prep + embeddings | 3 |
| Pós 6 | Marketplace integrations | 2+ |

## 11. Conclusão

O MVP é viável em **5 sprints após Sprint 4.5** (Trilha A), com dois caminhos paralelos possíveis. O gargalo fundamental NÃO é quantidade de código mas sim:
1. **Aplicar a infraestrutura de segurança já existente** (RBAC, audit, CSRF, tenant) que está implementada como helper mas não usada nos endpoints.
2. **Concluir a camada SQL do Knowledge Engine** (W1.3 + W1.5 + W1.7).
3. **Expor REST + Dashboard** para o Knowledge Engine já construído.

Cada gap tem solução conhecida e esforço estimado — não há necessidade de "novo design" para o MVP, apenas execução disciplinada.

---

**Ver também:**
- [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md)
- [ARAOS_SYSTEM_AUDIT.md](ARAOS_SYSTEM_AUDIT.md)
- [TECHNICAL_DEBT.md](TECHNICAL_DEBT.md)
- [SECURITY_AUDIT.md](SECURITY_AUDIT.md)
