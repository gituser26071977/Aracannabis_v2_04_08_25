# Índice de Documentação — AraOS SIAP

**Última atualização:** 2026-06-27 (M32 — Repository Stabilization)
**Total:** 119 documentos em `docs/`

---

## Documentos ativos (release RC1)

Estes são os documentos relevantes para o Release Candidate `v1.0.0-rc.1`. Devem ser consultados em produção.

### Release & Certificação

| Documento | Descrição |
|-----------|-----------|
| [RELEASE_PREPARATION_REPORT.md](RELEASE_PREPARATION_REPORT.md) | M31 — Plano de preparação do RC1 |
| [RELEASE_REPAIR_REPORT.md](RELEASE_REPAIR_REPORT.md) | M27 — Resolução do B-001 (data_revogacao) |
| [RELEASE_CANDIDATE_REPORT.md](RELEASE_CANDIDATE_REPORT.md) | Análise de candidato a release |
| [BETA_RELEASE_CANDIDATE.md](BETA_RELEASE_CANDIDATE.md) | Versão beta — checklist |
| [GO_LIVE_CERTIFICATION.md](GO_LIVE_CERTIFICATION.md) | M29 — Decisão GO/NO-GO para produção |
| [GO_LIVE_CHECKLIST.md](GO_LIVE_CHECKLIST.md) | Checklist pré-go-live |
| [GO_NO_GO_FINAL.md](GO_NO_GO_FINAL.md) | Decisão final GO/NO-GO |
| [PRODUCTION_RECONCILIATION_REPORT.md](PRODUCTION_RECONCILIATION_REPORT.md) | M30 — Reconciliação produção × repo |
| [PRODUCTION_CONFIDENCE.md](PRODUCTION_CONFIDENCE.md) | Confiança de produção |
| [PRODUCTION_INFRASTRUCTURE_REPORT.md](PRODUCTION_INFRASTRUCTURE_REPORT.md) | Infra de produção |
| [FINAL_DEPLOY_CERTIFICATION.md](FINAL_DEPLOY_CERTIFICATION.md) | Certificação final de deploy |

### Operacional (runbooks)

| Documento | Descrição |
|-----------|-----------|
| [DEPLOY_RUNBOOK.md](DEPLOY_RUNBOOK.md) | Procedimento de deploy |
| [DEPLOY_PIPELINE_HARDENING.md](DEPLOY_PIPELINE_HARDENING.md) | M28 — Hardening do pipeline |
| [DEPLOY_READINESS_PHASE4.md](DEPLOY_READINESS_PHASE4.md) | Readiness fase 4 |
| [PHASE4_DEPLOY_CHECKLIST.md](PHASE4_DEPLOY_CHECKLIST.md) | Checklist fase 4 |
| [DEPLOY_BLOCKERS.md](DEPLOY_BLOCKERS.md) | Bloqueadores de deploy |
| [ROLLBACK_PLAYBOOK.md](ROLLBACK_PLAYBOOK.md) | Procedimento de rollback |
| [DISASTER_RECOVERY_REPORT.md](DISASTER_RECOVERY_REPORT.md) | Recuperação de desastre |
| [OBSERVABILITY_REPORT.md](OBSERVABILITY_REPORT.md) | Observabilidade |
| [POST_DEPLOY_SMOKE.md](POST_DEPLOY_SMOKE.md) | Smoke pós-deploy |
| [SMOKE_EXECUTION_REPORT.md](SMOKE_EXECUTION_REPORT.md) | Execução do smoke |
| [SECRETS_INVENTORY.md](SECRETS_INVENTORY.md) | Inventário de secrets |
| [SECRETS_MIGRATION.md](SECRETS_MIGRATION.md) | Migração de secrets |

### Segurança

| Documento | Descrição |
|-----------|-----------|
| [AUDITORIA_SEGURANCA_2026_06.md](AUDITORIA_SEGURANCA_2026_06.md) | Auditoria de segurança Jun/2026 |
| [SECURITY_FINAL_SCORECARD.md](SECURITY_FINAL_SCORECARD.md) | Scorecard final de segurança |
| [WEBHOOK_SECURITY_FINAL_REVIEW.md](WEBHOOK_SECURITY_FINAL_REVIEW.md) | Review final de segurança de webhooks |
| [WEBHOOK_IDEMPOTENCY_REPORT.md](WEBHOOK_IDEMPOTENCY_REPORT.md) | Idempotência de webhooks |
| [WEBHOOK_PRODUCTION_SMOKE_REPORT.md](WEBHOOK_PRODUCTION_SMOKE_REPORT.md) | Smoke de webhooks em produção |
| [P0_REMEDIATION_REPORT.md](P0_REMEDIATION_REPORT.md) | Remediação P0 |

### LGPD / Compliance

| Documento | Descrição |
|-----------|-----------|
| [AUDITORIA_LGPD_2026_06.md](AUDITORIA_LGPD_2026_06.md) | Auditoria LGPD Jun/2026 |
| [LGPD_FINAL_AUDIT.md](LGPD_FINAL_AUDIT.md) | Auditoria final LGPD |
| [LGPD_OPERATIONAL_REPORT.md](LGPD_OPERATIONAL_REPORT.md) | LGPD operacional |
| [security_lgpd_assessment.md](security_lgpd_assessment.md) | Avaliação segurança + LGPD |

### Capacidade / Performance

| Documento | Descrição |
|-----------|-----------|
| [AUDITORIA_CAPACIDADE_2026_06.md](AUDITORIA_CAPACIDADE_2026_06.md) | Auditoria de capacidade Jun/2026 |
| [PERFORMANCE_ACCEPTANCE_REPORT.md](PERFORMANCE_ACCEPTANCE_REPORT.md) | Aceitação de performance |
| [PERFORMANCE_EVIDENCE.md](PERFORMANCE_EVIDENCE.md) | Evidências de performance |
| [PERFORMANCE_FINAL_REPORT.md](PERFORMANCE_FINAL_REPORT.md) | Relatório final de performance |
| [LIGHTHOUSE_REPORT.md](LIGHTHOUSE_REPORT.md) | Lighthouse |
| [CHAOS_REPORT.md](CHAOS_REPORT.md) | Chaos engineering |
| [FAILOVER_REPORT.md](FAILOVER_REPORT.md) | Failover |

### Billing

| Documento | Descrição |
|-----------|-----------|
| [BILLING_VALIDATION_REPORT.md](BILLING_VALIDATION_REPORT.md) | Validação de billing |

### Bugs / Issues

| Documento | Descrição |
|-----------|-----------|
| [BUG_CATALOG.md](BUG_CATALOG.md) | Catálogo de bugs |
| [BUG_FIX_REPORT.md](BUG_FIX_REPORT.md) | Relatório de correção de bugs |
| [DEAD_COMPONENTS.md](DEAD_COMPONENTS.md) | Componentes não utilizados |
| [UI_INCONSISTENCIES.md](UI_INCONSISTENCIES.md) | Inconsistências de UI |
| [FRONTEND_AUDIT.md](FRONTEND_AUDIT.md) | Auditoria de frontend |
| [FRONTEND_BACKLOG.md](FRONTEND_BACKLOG.md) | Backlog de frontend |
| [FASE4_5_HOTFIX_BLOQUEADORES.md](FASE4_5_HOTFIX_BLOQUEADORES.md) | Hotfix de bloqueadores |
| [FASE5_INVENTARIO_RATE_LIMIT.md](FASE5_INVENTARIO_RATE_LIMIT.md) | Inventário rate limit fase 5 |
| [FASE5_RATE_LIMIT_INVENTARIO_FINAL.md](FASE5_RATE_LIMIT_INVENTARIO_FINAL.md) | Rate limit inventário final |
| [RATE_LIMIT_PHASE5A_REPORT.md](RATE_LIMIT_PHASE5A_REPORT.md) | Rate limit fase 5A |

### UX / Jornada

| Documento | Descrição |
|-----------|-----------|
| [USER_JOURNEY_REPORT.md](USER_JOURNEY_REPORT.md) | Jornada do usuário |
| [UX_FRICTION_REPORT.md](UX_FRICTION_REPORT.md) | Atrito de UX |
| [UX_PRODUCTION_REPORT.md](UX_PRODUCTION_REPORT.md) | UX em produção |
| [EVIDENCE_MATRIX.md](EVIDENCE_MATRIX.md) | Matriz de evidências |
| [FUNCTIONAL_RED_TEAM.md](FUNCTIONAL_RED_TEAM.md) | Red team funcional |
| [PRE_DEPLOY_RED_TEAM_REPORT.md](PRE_DEPLOY_RED_TEAM_REPORT.md) | Red team pré-deploy |
| [OAT_REPORT.md](OAT_REPORT.md) | Operational Acceptance Testing |
| [M21_FINAL_SYNTHESIS.md](M21_FINAL_SYNTHESIS.md) | Símtese final M21 |

### Validação

| Documento | Descrição |
|-----------|-----------|
| [BETA_READINESS_REPORT.md](BETA_READINESS_REPORT.md) | Readiness beta |
| [PLAYWRIGHT_EVIDENCE.md](PLAYWRIGHT_EVIDENCE.md) | Evidências Playwright |
| [STAGING_CERTIFICATION_REPORT.md](STAGING_CERTIFICATION_REPORT.md) | Certificação staging |
| [STAGING_EXECUTION_REPORT.md](STAGING_EXECUTION_REPORT.md) | Execução staging |
| [OPERATIONAL_VALIDATION_FASE4.md](OPERATIONAL_VALIDATION_FASE4.md) | Validação operacional fase 4 |
| [RUNBOOK_VALIDATION_REPORT.md](RUNBOOK_VALIDATION_REPORT.md) | Validação de runbook |
| [DOCUMENTATION_REMEDIATION_REPORT.md](DOCUMENTATION_REMEDIATION_REPORT.md) | Remediação de docs |

### Arquitetura & Especificação

| Documento | Descrição |
|-----------|-----------|
| [AI_CLINICAL_PIPELINE_ARCHITECTURE.md](AI_CLINICAL_PIPELINE_ARCHITECTURE.md) | Arquitetura do pipeline AI Clinical |
| [API_CONVENTIONS.md](API_CONVENTIONS.md) | Convenções de API |
| [ARAOS_ARQUITETURA_ESTRATEGICA.md](ARAOS_ARQUITETURA_ESTRATEGICA.md) | Arquitetura estratégica |
| [ARAOS_PLATFORM_ARCHITECTURE.md](ARAOS_PLATFORM_ARCHITECTURE.md) | Arquitetura de plataforma |
| [ARAOS_REBRANDING_AUDIT.md](ARAOS_REBRANDING_AUDIT.md) | Auditoria de rebranding |
| [ARAOS_REBRANDING_PLAN.md](ARAOS_REBRANDING_PLAN.md) | Plano de rebranding |
| [ARAOS_SPRINT0_FOUNDATION.md](ARAOS_SPRINT0_FOUNDATION.md) | Fundação Sprint 0 |
| [ARAOS_VOICE_ESPECIFICACAO.md](ARAOS_VOICE_ESPECIFICACAO.md) | Especificação de voz |
| [ESPECIFICACAO_AGENTES_FASE1.md](ESPECIFICACAO_AGENTES_FASE1.md) | Especificação de agentes fase 1 |
| [INSTRUCOES_API.md](INSTRUCOES_API.md) | Instruções de API |
| [README.md](README.md) | README principal |

### Relatórios por sprint / release

| Documento | Sprint |
|-----------|--------|
| [WEEK6_INTEGRATION_SPRINT.md](WEEK6_INTEGRATION_SPRINT.md) | Week 6 |
| [WEEK6_RELATORIO_FINAL.md](WEEK6_RELATORIO_FINAL.md) | Week 6 |
| [WEEK7A_PLATFORM_HARDENING.md](WEEK7A_PLATFORM_HARDENING.md) | Week 7A |
| [WEEK7B_INTELLIGENCE_LAYER.md](WEEK7B_INTELLIGENCE_LAYER.md) | Week 7B |
| [WEEK8_KNOWLEDGE_LAYER.md](WEEK8_KNOWLEDGE_LAYER.md) | Week 8 |
| [WEEK10_SPECIALTY_FRAMEWORK.md](WEEK10_SPECIALTY_FRAMEWORK.md) | Week 10 |
| [WEEK11A_ADAPTIVE_FOLLOWUP.md](WEEK11A_ADAPTIVE_FOLLOWUP.md) | Week 11A |
| [WEEK_11B_RELEASE.md](WEEK_11B_RELEASE.md) | Week 11B |
| [WEEK11D_PRODUCTIZATION.md](WEEK11D_PRODUCTIZATION.md) | Week 11D |

### Sistemas implementados (referência técnica)

| Documento | Sistema |
|-----------|---------|
| [REDACTED.md](REDACTED.md) | Sistema de exames |
| [SISTEMA_EXAMES_FINALIZADO.md](SISTEMA_EXAMES_FINALIZADO.md) | Exames (final) |
| [SISTEMA_LEMBRETES.md](SISTEMA_LEMBRETES.md) | Lembretes |
| [SISTEMA_PRODUTOS_IMPLEMENTADO.md](SISTEMA_PRODUTOS_IMPLEMENTADO.md) | Produtos |
| [SISTEMA_SEM_IA_INICIADO.md](SISTEMA_SEM_IA_INICIADO.md) | Sem IA |
| [REDACTED.md](REDACTED.md) | Sintomas personalizados |
| [INTEGRAÇÃO_MERCADOPAGO_IMPLEMENTADA.md](INTEGRAÇÃO_MERCADOPAGO_IMPLEMENTADA.md) | Integração MercadoPago |

---

## Documentos históricos / arquiváveis

Estes documentos são **snapshots de missões específicas** (M17-M31). Mantidos para auditoria. NÃO devem ser referenciados em produção.

### Missões 17-19 (P0/P1)
- [CAMPO_EM_TRATAMENTO.md](CAMPO_EM_TRATAMENTO.md)
- [CORREÇÃO_EXAMES_INVALID_DATE_FINALIZADA.md](CORREÇÃO_EXAMES_INVALID_DATE_FINALIZADA.md)
- [CORREÇÕES_FINAIS_EXAMES.md](CORREÇÕES_FINAIS_EXAMES.md)
- [MELHORIAS_GRÁFICOS_IMPLEMENTADAS.md](MELHORIAS_GRÁFICOS_IMPLEMENTADAS.md)
- [MELHORIAS_IMPLEMENTADAS.md](MELHORIAS_IMPLEMENTADAS.md)
- [SOLUÇÃO_LOGIN_CORRIGIDA.md](SOLUÇÃO_LOGIN_CORRIGIDA.md)
- [SOLUÇÃO_NETWORK_ERROR_IA.md](SOLUÇÃO_NETWORK_ERROR_IA.md)
- [TESTE_COMPLETO_FINALIZADO.md](TESTE_COMPLETO_FINALIZADO.md)
- [VERSÃO_SEM_IA_IMPLEMENTADA.md](VERSÃO_SEM_IA_IMPLEMENTADA.md)
- [VERSÃO_SIMPLES_FUNCIONANDO.md](VERSÃO_SIMPLES_FUNCIONANDO.md)
- [VERSÕES_DO_SISTEMA.md](VERSÕES_DO_SISTEMA.md)

### Guias antigos (devem ser consolidados em DEPLOY_RUNBOOK)
- [INSTRUÇÕES_COMPLETAS_COM_VENV.md](INSTRUÇÕES_COMPLETAS_COM_VENV.md)
- [INSTRUÇÕES_DEPLOY_HOSTINGER_COMPLETAS.md](INSTRUÇÕES_DEPLOY_HOSTINGER_COMPLETAS.md)
- [INSTRUÇÕES_LOGIN.md](INSTRUÇÕES_LOGIN.md)
- [INSTRUÇÕES_LOGIN_DETALHADAS.md](INSTRUÇÕES_LOGIN_DETALHADAS.md)
- [INSTRUÇÕES_LOGIN_FUNCIONANDO.md](INSTRUÇÕES_LOGIN_FUNCIONANDO.md)
- [LOGIN_SIMPLES.md](LOGIN_SIMPLES.md)
- [README_DOCKER.md](README_DOCKER.md)
- [COMO_INICIAR_SOFTWARE.md](COMO_INICIAR_SOFTWARE.md)
- [REVISAO_SISTEMA_DEPLOY_HOSTINGER.md](REVISAO_SISTEMA_DEPLOY_HOSTINGER.md)
- [termius_guide.md](termius_guide.md)
- [vps_deploy_guide.md](vps_deploy_guide.md)
- [WHATSAPP_SETUP.md](WHATSAPP_SETUP.md)

### Versões / snapshots específicos
- [REVISAO_SISTEMA_DEPLOY_HOSTINGER.md](REVISAO_SISTEMA_DEPLOY_HOSTINGER.md)
- [VERSÕES_DO_SISTEMA.md](VERSÕES_DO_SISTEMA.md)

---

## Subdiretórios

### [`AraFlow/`](AraFlow/)

Documentos do produto AraFlow (futuro DTx). 39 documentos cobrindo visão, PRD, personas, jornada, IA, business model, regulatory. **Não relacionado ao RC1 do SIAP** — manter separado até AraFlow Sprint 1.

### [`adr/`](adr/)

Architecture Decision Records. 7 documentos + template:
- `README.md` — Template e processo
- `016-npm-workspaces.md`
- `017-typescript-strict-branded.md`
- `018-conventional-commits.md`
- `019-master-clock-implementation.md`
- `020-breath-engine.md`
- `021-core-contracts.md`
- `022-protocol-compiler.md`

---

## Política de versionamento

- **Ativos:** nunca remover sem aprovação.
- **Histórico:** snapshots de missões podem ser arquivados em `docs/archive/` no próximo ciclo.
- **AraFlow/:** manter intacto até release independente.
- **adr/:** append-only.

## Pendências M32

- Mover 16 docs históricos para `docs/archive/` (não executado em M32 — proposto para próximo ciclo).
- Consolidar 11 guias antigos em `DEPLOY_RUNBOOK.md` (não executado em M32).