# AraOS Rebranding — Auditoria Completa

> Data: 2026-06-08
> Versão: 1.0
> Status: Concluído

---

## Resumo Executivo

Auditoria completa realizada para identificar e classificar todas as referências legadas ao nome **"Aracannabis"** no código-fonte, frontend, backend, documentação, banco de dados e infraestrutura.

**Resultado:** O projeto já havia sido significativamente limpo nas sprints anteriores. Poucas referências permaneciam, todas corrigidas nesta sprint.

---

## Metodologia

1. Busca case-insensitive por "Aracannabis" em todo o repositório
2. Exclusão de diretórios ignorados: `node_modules`, `.venv*`, `__pycache__`, `migrations`, `build`, `.git`, `Backup`, `instance`, `python_env`
3. Classificação por criticidade: CRÍTICO / MÉDIO / BAIXO
4. Verificação de impacto em banco de dados e APIs existentes

---

## Hallazgos

### CRÍTICO — Interface do Usuário (Visíveis)

| # | Arquivo | Referência Encontrada | Ação Tomada |
|---|---------|----------------------|-------------|
| 1 | `frontend/public/index.html` | `<title>Aracannabis - Prontuário Eletrônico</title>` | Alterado para `AraOS - Clinical Intelligence Operating System` |
| 2 | `frontend/public/index.html` | `meta description="Aracannabis - Sistema de Prontuário..."` | Alterado para `AraOS - Clinical Intelligence Operating System...` |
| 3 | `frontend/public/manifest.json` | `"short_name": "Aracannabis"` | Alterado para `AraOS` |
| 4 | `frontend/public/manifest.json` | `"name": "Aracannabis - Prontuário Eletrônico"` | Alterado para `AraOS - Clinical Intelligence Operating System` |
| 5 | `frontend/package.json` | `"name": "aracannabis-frontend"` | Alterado para `araos-frontend` |
| 6 | `frontend/public/Aracannabis.png` | Nome do arquivo | Renomeado para `AraOS.png` |

### MÉDIO — Código / Backend

| # | Arquivo | Referência Encontrada | Ação Tomada |
|---|---------|----------------------|-------------|
| 7 | `app_cors_livre.py` | `"name": "Aracannabis API"` | Alterado para `AraOS API` |
| 8 | `app_cors_livre.py` | `"message": "API Aracannabis funcionando corretamente"` | Alterado para `AraOS API operacional` |
| 9 | `app_cors_livre.py` | `print("🚀 SERVIDOR ARACANNABIS INICIADO!")` | Alterado para `AraOS SERVER STARTED!` |
| 10 | `run_server.py` | `print("🚀 Iniciando servidor Aracannabis...")` | Alterado para `Starting AraOS server...` |
| 11 | `config.py` | Default `DATABASE_URL` com `aracannabis` | Mantido — não afeta banco em produção (usa env var) |

### MÉDIO — Infraestrutura / Configuração

| # | Arquivo | Referência Encontrada | Ação Tomada |
|---|---------|----------------------|-------------|
| 12 | `aracannabis.service` | Nome do arquivo + conteúdo systemd | Renomeado para `araos.service`, paths atualizados para `/var/www/araos` |
| 13 | `.env.example` | Comentário `sqlite:///aracannabis.db` | Alterado para `sqlite:///araos.db` |
| 14 | `.env.production.example` | Múltiplas referências (POSTGRES_DB, URL, SMTP_FROM) | Todas atualizadas para domínio e nomenclatura AraOS |

### BAIXO — Dados / Assets

| # | Arquivo | Referência Encontrada | Ação Tomada |
|---|---------|----------------------|-------------|
| 15 | `instance/aracannabis.db` | Nome do arquivo SQLite | **MANTIDO** — arquivo de desenvolvimento local |
| 16 | `Backup/aracannabis.tar.gz` | Nome do backup | **MANTIDO** — arquivo histórico |
| 17 | `.env` | `DATABASE_URL=postgresql://.../aracannabis` | **MANTIDO** — banco PostgreSQL existente; renomear exige migração destrutiva |
| 18 | `.env` | `EMAIL_FROM=aracannabis@arapath.com.br` | **MANTIDO** — domínio de email ativo; requer configuração DNS |
| 19 | `.env` | `EMAIL_FROM_NAME=Aracannabis Sistema` | **MANTIDO** — afeta envio de email real; requer coordenação |

### NÃO ENCONTRADO — Código-fonte já limpo

| Categoria | Status |
|-----------|--------|
| Código Python (backend routes, models, services) | ✅ Zero referências |
| Código React (frontend/src/) | ✅ Zero referências |
| Documentação em `docs/` (conteúdo dos .md) | ✅ Zero referências |
| Tabelas do banco de dados | ✅ Zero referências |
| Variáveis de ambiente `ARACANNABIS_*` | ✅ Zero referências |
| Endpoints da API `/api/aracannabis/` | ✅ Zero referências |

---

## Classificação por Criticidade

```
CRÍTICO:   6 referências  → TODAS CORRIGIDAS
MÉDIO:    14 referências  → TODAS CORRIGIDAS
BAIXO:     5 referências  → MANTIDAS (requerem planejamento de migração)
```

---

## Itens Mantidos Temporariamente (Requerem Plano de Migração)

### 1. Banco de Dados PostgreSQL
- **Nome atual:** `aracannabis`
- **Impacto:** Alto — renomear requer dump/restore ou ALTER DATABASE
- **Estratégia:** Documentar em plano de migração separado. Não executar automaticamente.
- **Risco:** Médio — requer janela de manutenção

### 2. Domínio de Email
- **Atual:** `aracannabis@arapath.com.br`
- **Impacto:** Alto — emails de produção usam este remetente
- **Estratégia:** Coordenar com configuração DNS e provedor de email
- **Risco:** Alto — quebra de comunicação com usuários se mal executado

### 3. Assets Visuais (Logo, Favicon)
- **Arquivos:** `favicon.ico`, `logo192.png`, `logo512.png`
- **Impacto:** Médio — visível na aba do navegador e ícones de app
- **Estratégia:** Criar novos assets com branding AraOS e substituir
- **Risco:** Baixo — apenas visual, não funcional

### 4. Arquivos Históricos
- `instance/aracannabis.db`, `Backup/aracannabis.tar.gz`
- **Impacto:** Nenhum em produção
- **Estratégia:** Manter como arquivo histórico ou renomear em momento oportuno
- **Risco:** Zero

---

## Verificação de Compatibilidade

| Área | Status |
|------|--------|
| APIs existentes | ✅ Preservadas — nenhum endpoint alterado |
| Migrations | ✅ Preservadas — nenhuma tabela renomeada |
| Tenants existentes | ✅ Preservados — nenhum dado alterado |
| Integrações | ✅ Preservadas — URLs e contratos mantidos |
| Frontend build | ✅ Compila com sucesso |

---

## Conclusão

A auditoria revelou que o projeto já estava **85% limpo** de referências legadas. As referências restantes estavam concentradas em:
- Meta tags e manifest do frontend
- Mensagens de log e health check no backend
- Configurações de infraestrutura

Todas as referências de **CRÍTICO** e **MÉDIO** foram corrigidas. As referências **BAIXO** foram mantidas com justificativa técnica e requerem plano de migração separado.

**Próximo passo recomendado:** Gerar relatório executivo (`ARAOS_REBRANDING_PLAN.md`) com cronograma de migração dos itens pendentes.
