# GO_NO_GO_FINAL — MISSÃO 22

**Data:** 2026-06-25
**Modo:** EXECUTE
**Objetivo:** responder objetivamente às 7 perguntas obrigatórias

---

## Respondendo as 7 perguntas

### 1. Existe algum bloqueador técnico REAL?

**SIM — 5 BLOQUEADORES REAIS documentados em `DEPLOY_BLOCKERS.md`:**

1. **P0-05 (CSP) não deployado** — provado por curl 2026-06-25
2. **P0-12 (X-Association-ID) não deployado** — provado por curl
3. **LGPD art. 18 VI não implementado** — provado por código
4. **`/api/health` não deployado** — provado por curl
5. **Pool PG real em prod DESCONHECIDO** — sem `.env.production` acessível

> **Tese:** Os 5 bloqueadores podem ser resolvidos em **≤ 1 sprint** (deploy M18 + M20 + implementar LGPD-04). Após isso, **zero bloqueadores técnicos remanescentes**.

### 2. Existe alguma dependência humana?

**SIM — múltiplas:**

| Dependência | Quem | Tempo |
|-------------|------|-------|
| Provisionar staging | SRE/DevOps | 2h |
| Configurar 9 secrets no GitHub | DevOps | 30min |
| Configurar Slack webhooks (3) | DevOps | 15min |
| Provisionar VPS monitoring | SRE | 4h |
| Autorizar deploy em prod | PO/Gerente | 1 dia |
| Confirmar 5 médicos-piloto | Gerente | 1 dia |
| Configurar backup automatizado | SRE | 1h |
| Janela de manutenção | Todos | 4h |

**Total humano estimado:** 2-3 dias úteis com equipe disponível.

### 3. Existe alguma dependência externa?

**SIM — externas ao AraOS:**

| Dependência | Provedor | SLA | Risco |
|-------------|----------|-----|-------|
| DNS / domínio | Registro.br | 99.9% | baixo |
| TLS / Let's Encrypt | Let's Encrypt | 99.9% | baixo (renova 60d) |
| VPS | Hostinger | depende do plano | médio |
| Traefik | self-hosted | 99% (uptime histórico) | baixo |
| Mercado Pago | MP | 99.9% (com sandbox fallback) | baixo |
| Evolution (WhatsApp) | self-hosted em VPS | 99% | **alto** (caiu 1x na auditoria M17) |
| LLM providers (Gemini, Claude, etc) | externos | variável | **alto** (rate limit externo) |
| SMTP | provedor externo | 99% | médio |

> **Nota:** LLM providers externos são o maior risco — se Gemini cair, IA chat para.

### 4. Quanto tempo leva o deploy completo?

| Etapa | Tempo |
|-------|-------|
| Pré-deploy (build + backup) | 5-10min |
| Restart backend | 2-3min |
| Smoke backend | 1min |
| Restart frontend | 2-3min |
| Smoke frontend | 30s |
| Validação H+15 | 5min |
| Validação H+30 | 15min |
| Validação H+60 | 30min |
| **TOTAL deploy ativo** | **~10-15min** |
| **TOTAL janela de manutenção** | **~1h-1h30min** (incluindo validações) |

### 5. Quanto tempo leva o rollback?

| Tipo | Tempo |
|------|-------|
| Rollback só de aplicação | **2-5 min** |
| Rollback com restore de DB 1GB | **15-30 min** |
| Rollback total com restore de DB 10GB | **1-2 horas** |

> **Ver `ROLLBACK_PLAYBOOK.md` Seção 4** para a tabela completa.

### 6. Qual o risco operacional restante?

**Risco residual (após deploy dos 5 BLOQUEADORES):**

| Risco | Origem | Mitigação atual | Mitigação ideal |
|-------|--------|------------------|------------------|
| Capacidade <50u | M17 (medido) | Rate-limit MemoryStorage | Pool PG 30+60 + rate-limit Redis |
| DLQ ausente em webhooks | M17 backlog | log manual | Tabela `webhook_dlq` |
| LGPD-04 ausente | M17 backlog | não implementado | MISSÃO 23 |
| Sem monitoramento | M20 não provisionado | healthcheck via curl | Prometheus + Grafana |
| Sem tracing | M21 backlog | logs básicos | OpenTelemetry |
| RPO 24h | M20 não implantado | backup diário | WAL archiving |

**Risco total residual:** MÉDIO (após deploy dos 5 bloqueadores).

### 7. Você autorizaria executar este deploy numa sexta-feira às 18h?

> ❌ **NÃO**
>
> **Justificativa objetiva:**
>
> 1. **Sexta 18h** = início de fim de semana + plantão fino
> 2. **Em caso de rollback**, SRE pode não estar disponível em 30min
> 3. **Janela de manutenção de 1h** + tempo de recuperação potencial = **atinge sábado de madrugada**
> 4. **Histórico**: falhas em deploy sexta 18h tradicionalmente viram incidentes de 36h+ sem resolução
>
> **Recomendações:**
> - **Melhor janela:** terça ou quarta, **10h-14h** (SRE completo, médico-piloto disponível)
> - **Evitar:** sexta 18h, véspera de feriado, 1º dia do mês
> - **Após deploy:** SRE em alerta até D+1 completo

---

## Decisão GO / NO-GO

| Cenário | Veredicto |
|---------|-----------|
| Estado atual (com 5 BLOQUEADORES) | **❌ NO-GO** |
| Após deploy M18 + M20 | **🟠 GO CONDICIONAL** (5 médicos; staging primeiro) |
| Após LGPD-04 implementado | **🟢 GO** (até 50 médicos) |
| Após WAL archiving + capacity fix | **🟢 GO** (até 100 médicos) |
| Após scaling horizontal | **🟢 GO** (100-500 médicos) |

---

## Resposta final

**SIM**, autorizaria o deploy **APENAS SE**:

1. ✅ Os 5 BLOQUEADORES REAIS estiverem resolvidos em staging
2. ✅ Janela de 1h30min confirmada para terça/quarta 10h
3. ✅ SRE + médico-piloto em alerta até D+1
4. ✅ Smoke pós-deploy OK em todos os 17 itens do `POST_DEPLOY_SMOKE.md`
5. ✅ Plano de rollback testado em staging nas últimas 24h

**SEM ESSAS CONDIÇÕES:** ❌ NÃO autorizo.

---

**Esta é a posição final após MISSÕES 17-22. Aguardando revisão humana.**
