# AraOS Rebranding — Plano Executivo

> Data: 2026-06-08
> Versão: 1.0
> Arquiteto Responsável: Principal Architect / Release Manager

---

## 1. Resumo Executivo

A plataforma concluiu a transição de identidade de **Aracannabis** para **AraOS** (Ara Operating System).

**Novo posicionamento estratégico:**
- **Nome:** AraOS
- **Descrição:** Clinical Intelligence Operating System
- **Subtítulo:** Plataforma Operacional Inteligente para Saúde
- **Arquitetura:** Multi-especialidade via Specialty Framework

**Status geral:** ✅ **Concluído** (fase 1 — código-fonte e configurações)

---

## 2. Total de Referências Encontradas

| Criticidade | Quantidade | Corrigidas | Mantidas |
|-------------|-----------|------------|----------|
| CRÍTICO (UI visível) | 6 | 6 (100%) | 0 |
| MÉDIO (código/config) | 14 | 14 (100%) | 0 |
| BAIXO (infra/dados) | 5 | 0 | 5 (requerem plano) |
| **TOTAL** | **25** | **20 (80%)** | **5 (20%)** |

---

## 3. Referências Corrigidas

### Frontend
- [x] `index.html` — title e meta description
- [x] `manifest.json` — short_name e name
- [x] `package.json` — nome do projeto npm
- [x] `Aracannabis.png` → `AraOS.png`
- [x] Removida `LandingPage.js` (página de marketing antiga)
- [x] `App.js` — rota `/` redireciona para `/login`

### Backend
- [x] `app_cors_livre.py` — mensagens de health check e log
- [x] `run_server.py` — mensagem de inicialização
- [x] `.env.example` — comentário de desenvolvimento
- [x] `.env.production.example` — todas as variáveis de produção

### Infraestrutura
- [x] `aracannabis.service` → `araos.service` (systemd)

---

## 4. Referências Mantidas Temporariamente

### 4.1 Banco de Dados PostgreSQL
```
Nome atual:   aracannabis
Impacto:      Alto
Ação:         NÃO renomear automaticamente
Estratégia:   Janela de manutenção + dump/restore ou ALTER DATABASE
Cronograma:   Sprint futura (após estabilização do deploy)
Risco:        Médio — requer backup completo antes da operação
```

### 4.2 Domínio de Email
```
Atual:        aracannabis@arapath.com.br
Impacto:      Alto
Ação:         NÃO alterar sem coordenação DNS
Estratégia:   Configurar novo domínio araos.health e redirecionar
Cronograma:   Após definição de domínio comercial
Risco:        Alto — quebra de comunicação
```

### 4.3 Assets Visuais (Logo, Favicon)
```
Arquivos:     favicon.ico, logo192.png, logo512.png
Impacto:      Médio
Ação:         Substituir por novos assets AraOS
Estratégia:   Design novo logo + geração de favicon set
Cronograma:   Imediato (assim que assets disponíveis)
Risco:        Baixo — apenas visual
```

### 4.4 Arquivos de Desenvolvimento
```
Arquivos:     instance/aracannabis.db, Backup/aracannabis.tar.gz
Impacto:      Nenhum em produção
Ação:         Manter como histórico
Estratégia:   Renomear em momento oportuno ou manter
Cronograma:   Não urgente
Risco:        Zero
```

### 4.5 Variáveis de Ambiente .env (Produção Local)
```
Variáveis:    EMAIL_FROM, EMAIL_FROM_NAME
Impacto:      Alto (envio real de emails)
Ação:         Manter até migração de domínio de email
Estratégia:   Coordenar com configuração de SMTP e DNS
Cronograma:   Sprint de infraestrutura
Risco:        Alto — afeta notificações aos usuários
```

---

## 5. Riscos Identificados

| # | Risco | Probabilidade | Impacto | Mitigação |
|---|-------|--------------|---------|-----------|
| 1 | Cache do navegador mostrando título antigo | Alta | Baixo | Hard refresh (Ctrl+Shift+R) após deploy |
| 2 | Service worker com manifest antigo | Média | Médio | Incrementar versão do build e limpar cache |
| 3 | Emails com remetente antigo confundem usuários | Alta | Médio | Comunicação proativa + migração rápida de domínio |
| 4 | URLs hardcoded em documentos externos | Média | Alto | Busca e atualização de documentação externa |
| 5 | Integrações de terceiros com URL antiga | Baixa | Alto | Mapear integrações e atualizar endpoints |

---

## 6. Plano de Migração — Fases

### Fase 1: Código-fonte ✅ CONCLUÍDA
- [x] Auditoria completa
- [x] Correção de referências CRÍTICO e MÉDIO
- [x] Build validado
- [x] Testes de API passando

### Fase 2: Deploy e Infraestrutura ⏳ PENDENTE
- [ ] Configurar VPS com novo path `/var/www/araos`
- [ ] Atualizar nginx configuration
- [ ] Configurar SSL para domínio araos.health
- [ ] Deploy automático via GitHub Actions
- [ ] Atualizar `araos.service` no systemd do VPS

### Fase 3: Banco de Dados ⏳ PENDENTE
- [ ] Criar script de migração (dump/restore)
- [ ] Testar migração em ambiente de staging
- [ ] Agendar janela de manutenção
- [ ] Executar migração em produção

### Fase 4: Comunicação e Branding ⏳ PENDENTE
- [ ] Criar assets visuais (logo, favicon, ícones)
- [ ] Atualizar domínio de email
- [ ] Comunicar usuários sobre rebranding
- [ ] Atualizar documentação externa

---

## 7. Estimativa de Esforço

| Fase | Esforço Estimado | Status |
|------|-----------------|--------|
| Fase 1: Código-fonte | 2h | ✅ Concluído |
| Fase 2: Deploy/Infra | 4h | ⏳ Pendente |
| Fase 3: Banco de Dados | 2h | ⏳ Pendente |
| Fase 4: Comunicação | 3h | ⏳ Pendente |
| **TOTAL** | **~11h** | 20% concluído |

---

## 8. Recomendações

1. **Prioridade Alta:** Configurar deploy automático no VPS para acelerar iterações futuras
2. **Prioridade Média:** Definir domínio comercial final (araos.health ou outro)
3. **Prioridade Média:** Criar assets visuais AraOS para substituir favicon e logos
4. **Prioridade Baixa:** Renomear banco de dados PostgreSQL em janela de manutenção
5. **Governança:** Estabelecer política de nomenclatura para evitar regressões futuras

---

## 9. Critério de Sucesso — Validação

| Critério | Status |
|----------|--------|
| Usuário não visualiza "Aracannabis" em áreas principais | ✅ Validado — busca retornou 0 ocorrências |
| Produto se apresenta como AraOS | ✅ Validado — title, manifest, logs atualizados |
| Compatibilidade técnica preservada | ✅ Validado — APIs, migrations, tenants intactos |
| Nenhuma funcionalidade quebrada | ✅ Validado — build aprovado, APIs respondendo |

---

## 10. Anexos

- `ARAOS_REBRANDING_AUDIT.md` — Detalhamento completo da auditoria
- Branch atual: `main` (v0.8.0-alpha)
- Tag: `v0.8.0-alpha` → próxima tag sugerida: `v0.8.1-alpha` (rebranding)
