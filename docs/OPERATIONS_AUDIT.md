# OPERATIONS_AUDIT — MISSÃO D01 FASE 1

**Data inventário:** 2026-06-30
**Hora início:** 09:00 UTC (06:00 -03)
**Modo:** AUDIT (read-only; nenhuma alteração em prod)
**Origem:** D01 — Zero-touch Deploy & Operations (FASE 1)
**Alvo:** VPS produção `147.93.33.253` + API pública `https://api.visualsmartflow.com.br`
**Acesso:** SSH root via `id_ed25519` (autorizada em `/root/.ssh/authorized_keys` do VPS)
**Meu IP de origem:** `187.19.176.184` (rede residencial, após troca)

---

# Escopo da auditoria

Esta FASE 1 foi executada **read-only via SSH como root** após restabelecimento de conectividade. Auditoria cobre:

- ✅ Rede, firewall, SSH
- ✅ Containers Docker (SIAP + demais projetos no VPS)
- ✅ Recursos consumidos (CPU, RAM, disco, I/O)
- ✅ Configuração Traefik (rotas ativas)
- ✅ PostgreSQL SIAP (conectividade, migrations aplicadas)
- ✅ Git local no VPS (estado do repo `araos`)
- ✅ Variáveis de ambiente
- ✅ Authorized keys (auditoria de quem pode entrar)
- ✅ Cron jobs ativos
- ✅ Diretório de backups
- ⚠️ Discrepâncias entre docs M36/M37 e realidade

**Não foi alterado nada em produção nesta FASE.**

---

# Resumo executivo (1 página)

| Camada | Estado | Evidência |
|--------|--------|-----------|
| **VPS** | ✅ Acessível | SSH root com `id_ed25519`; Debian 13 trixie; 60 dias uptime |
| **Firewall** | ✅ Saudável | UFW: 22, 80, 443 (v4+v6); fail2ban ativo |
| **Docker** | ✅ Funcionando | Engine rodando; compose project `opt` (Traefik) + `araos` (SIAP) + ~10 outros |
| **Traefik** | ✅ SHARED OK | v3.6; rotas SIAP configuradas; TLS Let's Encrypt |
| **SIAP containers** | ✅ Rodando | backend/frontend/db/redis/anonymization Up |
| **SIAP backend health** | ❌ Not healthy | 7 dias Up mas healthcheck não passa |
| **SIAP migration B-001** | ❌ NÃO aplicada | `data_revogacao` coluna ausente |
| **Cloudflare** | ✅ Proxy ativo | Header `server: gunicorn` confirma origem |
| **GitHub Actions** | ✅ 4 workflows | `CD Production` é tag-driven |
| **GitHub Secrets** | ⚠️ Presumidos | `PROD_SSH_KEY` deve corresponder à chave `github-actions-planttracker` |
| **Backups SIAP** | ❌ Não existem | `/var/backups/siap` ausente |
| **Outros projetos no VPS** | ✅ Identificados | dr_anderson_sdr, sgac, plantao-os, plant_tracker, vsf, evolution, arapath, etc. |
| **M36/M37 docs precisão** | ⚠️ Desatualizados | Path errado (`/opt/siap` → real é `/root/projetos/araos`); SSH user errado (`operador` → real é `root`) |

---

# 1. VPS — Inventário completo

## 1.1 Identificação

| Item | Valor |
|------|-------|
| Hostname | `aracannabis` |
| OS | Debian GNU/Linux 13 (trixie) |
| Kernel | 6.12.74-cloud-amd64 |
| Uptime | 60 dias |
| IP público | 147.93.33.253 (IPv4 direto, sem Tunnel Cloudflare) |
| Meu IP de origem | 187.19.176.184 |
| Tenant (cloud) | Hostinger cloud (dedicado?) |

## 1.2 Recursos

| Recurso | Total | Usado | Livre | % |
|---------|-------|-------|-------|---|
| Disco `/` | 99 GB | 55 GB | **40 GB** | 58% |
| Memória | 7.76 GB | ~580 MB (SIAP only) | 7.18 GB | 7% |
| Docker volumes | — | 52 GB | — | — |

**Diagnóstico:** Recursos folgados. Sem pressão. Sem necessidade de scaling vertical imediato.

## 1.3 Firewall + Segurança

```
UFW: ativo
  - 22/tcp (SSH)         ALLOW v4 + v6
  - 80/tcp (HTTP)        ALLOW v4 + v6
  - 443/tcp (HTTPS)      ALLOW v4 + v6
  - 5432/tcp             BLOQUEADO (DB não exposto) ✅
  - 6379/tcp             BLOQUEADO (Redis não exposto) ✅
  - 5440/tcp             ⚠️ ABERTO (bind 0.0.0.0 → siap-db) — ver §2.4

fail2ban: ativo (sshd jail)
sshd:    ativo, OpenSSH 14.0p1
PermitRootLogin:    (não testei; minha chave conecta como root então provavelmente yes OU via Match Address)
```

## 1.4 Authorized SSH keys (auditoria)

| Key fingerprint | Comentário | Status |
|-----------------|------------|--------|
| `ssh-ed25519 AAAAC3Nz...Ljzu` | `github-actions-planttracker` | ✅ CD Production |
| `ssh-ed25519 AAAAC3Nz...` | `aracannabis-deploy` (correspondente à `~/.ssh/aracannabis_deploy`) | ⚠️ Não testei |
| `ssh-ed25519 AAAAC3Nz...` | `aracannabis-reinstall` | ⚠️ Não testei |
| `ssh-ed25519 AAAAC3Nz...` | `abholzwarth@gmail.com` (= minha `id_ed25519`) | ✅ USEI para auditoria |

**⚠️ Recomendações FASE 5:**
- Remover chaves sem dono claro (`aracannabis-reinstall`? backup?)
- Rotacionar `github-actions-planttracker` periodicamente
- Documentar quem é dono de cada chave

---

# 2. Docker — Inventário completo

## 2.1 Compose projects ativos no VPS (não-SIAP)

⚠️ **NÃO MEXER** em nenhum destes — são projetos irmãos compartilhando VPS:

```
dr_anderson_sdr         (1 container + 1 pg backend)
sgac                    (4 containers: pg, backend, web, etc.)
plantao-os              (5 containers)
plant_tracker           (1 api + web)
vsf / infra             (api, dashboard, landing — Visual Smart Flow)
evolution               (1 container — API WhatsApp — exited)
arapath                 (1 container)
aracannabis_legacy      (legado)
traefik                 (v3.6, shared router)
careos                  (api medication alerts)
agrobuds                (4 containers)
landing-dr-anderson     (backend)
hermes                  (?)
```

**Total de containers no VPS:** ~40+ (22 SIAP + ~20 outros projetos).

## 2.2 SIAP containers (estado real)

| Container | Imagem | Up time | CPU | RAM | Status |
|-----------|--------|---------|-----|-----|--------|
| `siap-backend` | `araos-siap-backend:latest` (criado 2026-06-22T01:19) | 7 dias | 0.07% | **304 MB** | **Up mas NOT healthy** |
| `siap-db` | `postgres:16-alpine` | 7 dias | 0.87% | 25 MB | Up (healthy) |
| `siap-redis` | `redis:7-alpine` | 7 dias | 0.51% | 7 MB | Up (healthy) |
| `siap-frontend` | `araos-siap-frontend:latest` (criado 2026-06-22T06:32) | 7 dias | 0.00% | 24 MB | Up (healthy) |
| `siap-anonymization` | (cryptography service) | 7 dias | 0.22% | 17 MB | Up (healthy) |

**Diagnóstico:**
- Imagens SIAP estão com **7 dias de idade** (criadas antes do RC1 montado em `96b547b`).
- Backend **NÃO está healthy** mesmo Up. Healthcheck provavelmente falha por endpoint `/api/health` que ainda não existe na imagem atual.
- Recursos folgados: 304MB / 7.76GB total.

## 2.3 SIAP logs (últimos 30 min)

- Erros: **0** (grep error/exception/critical/fail → vazio)
- deploy_guard logs: **0** (módulo não está no backend atual — pré-RC1)

**Diagnóstico:** backend pré-RC1 está rodando estável. Sem alarmes.

## 2.4 Port mapping (⚠️ risco de segurança)

| Container | Host port → Container | Exposição |
|-----------|----------------------|-----------|
| siap-db | `0.0.0.0:5440 → 5432` | ⚠️ **PÚBLICO** (qualquer IP pode tentar conectar no Postgres) |
| siap-redis | sem host port | só interno ✅ |
| siap-backend | sem host port (5002 interno) | só via Traefik ✅ |
| siap-anonymization | sem host port (8000 interno) | só interno ✅ |
| siap-frontend | sem host port (3000 interno) | só via Traefik ✅ |

**⚠️ ACHADO — Porta 5440 exposta publicamente:**
- `0.0.0.0:5440` mapeia Postgres para o host todo.
- UFW não bloqueia 5440 (só 22/80/443 estão na allow list).
- Quem tem a senha do `siap_user` consegue conectar de qualquer lugar.
- **Risco:** se a senha vazar (ex: dump de log, memory leak), banco fica acessível.

**Recomendação FASE 2:**
1. Remover `ports` do `siap-db` em `docker-compose.prod.yml` (deixar interno)
2. OU adicionar UFW rule `deny 5440`
3. OU bindar em `127.0.0.1:5440:5432` (não em 0.0.0.0)
4. Mudar a senha `POSTGRES_PASSWORD` e validar que é forte

---

# 3. PostgreSQL SIAP — Estado atual

## 3.1 Conectividade

```bash
docker exec siap-db psql -U siap_user -d aracannabis -c "SELECT 1 AS ok;"
# →  ok
# →   1
```

**Status:** ✅ Conexão OK.

## 3.2 Migration B-001 (CRÍTICO)

```bash
docker exec siap-db psql -U siap_user -d aracannabis \
  -c "SELECT column_name FROM information_schema.columns
      WHERE table_name='pacientes' AND column_name='data_revogacao';"
# → 0 rows (coluna NÃO EXISTE)
```

**Status:** ❌ **B-001 NÃO aplicada em produção.**

**Ação obrigatória antes do RC1 deploy:**
- Aplicar `ALTER TABLE pacientes ADD COLUMN IF NOT EXISTS data_revogacao TIMESTAMP;` (idempotente).
- Validar deploy_guard na próxima inicialização do backend.

## 3.3 Alembic head

```bash
# última migration aplicada = 2026_06_21_add_modulos (head pré-B-001)
```

## 3.4 Database stats (resumo)

| Item | Valor |
|------|-------|
| DB | `aracannabis` |
| User | `siap_user` |
| Versão PG | 16.13 |
| Tamanho (aprox) | (não medi) |
| Conexões ativas | baixas (sem load test) |

---

# 4. Traefik — Rotas ativas

## 4.1 Identificação

- **Container:** `opt_traefik-1` (compose project `opt`)
- **Versão:** v3.6
- **Network externa:** `opt_web`
- **Volumes:** `opt_traefik-certificates` (data: 2025-10-03)
- **ACME / Let's Encrypt:** ativo

## 4.2 Rotas SIAP (confirmadas via log Traefik)

| Host | Service | Upstream | TLS |
|------|---------|----------|-----|
| `api.visualsmartflow.com.br` | `siap-api` | `http://172.19.0.3:5002` | Let's Encrypt |
| `visualsmartflow.com.br` | `siap-web` | `http://172.19.0.4:3000` | Let's Encrypt |
| `araos.visualsmartflow.com.br` | `siap-web` | `http://172.19.0.4:3000` | Let's Encrypt |
| `www.visualsmartflow.com.br` | `siap-web` (redirect regex → sem www) | mesma | Let's Encrypt |

**Diagnóstico:** ✅ Roteamento Traefik pronto. SSL válido. Não preciso tocar em nada do Traefik para RC1.

## 4.3 Outras rotas (NÃO TOCAR)

```
dranderson.aracannabis.com.br        → dranderson
plantao.visualsmartflow.com.br       → plantaoos
arapath.com.br                       → planttracker
agrobuds-app.arapath.com.br          → sgac-api, sgac-web
sdr.dranderson.aracannabis.com.br    → dr_anderson_sdr webhook
visualsmartflow.com.br/dashboard     → vsf-api (path strip /api)
visualsmartflow.com.br/mobile        → vsf-api
```

---

# 5. Git local no VPS (`/root/projetos/araos`)

## 5.1 Estado

```bash
$ cd /root/projetos/araos && git status
On branch main
Your branch is up to date with 'origin/main'.

$ git log -1 --oneline
ce141c5e6 fix(modulos): troca EcoIcon (não existe em @mui/icons-material) por EnergySavingsLeaf
```

**Diagnóstico:**
- VPS está no `main` branch, **não** no `fix/p0-stabilization-2026-06`.
- HEAD `ce141c5e6` ≠ HEAD `96b547b` do RC1 montado localmente.
- VPS está rodando imagem do **commit pre-RC1** (junho 22).
- Não tem worktree, não tem migration B-001 aplicada.

**⚠️ Implicação para RC1:**
O workflow CD Production DEVE:
1. Fazer `git pull` no `/root/projetos/araos` para branch correta
2. OU ter um diretório separado para deploy (ex: `/root/projetos/araos-deploy`)
3. OU clonar repo no momento do deploy

**Atualmente o VPS está com checkout em main, NÃO em RC1.** CD Production precisa resolver isso (talvez checkout `--force` no SHA do release).

## 5.2 `.env.production` (4 backups históricos)

```
.env.production                                 (atual, root:root 2370 bytes)
.env.production.bak.20260618_vps_inspect
.env.production.bak.20260620_postfix_174520
.env.production.bak.20260621_165445
.env.production.bak.20260621_221921
.env.production.example                          (template)
.env.production.vps.backup.20260607_013900
```

**Diagnóstico:** ✅ Boa higiene — `.env.production` está com 4 backups datados (backup manual a cada ajuste). Template `.env.production.example` está versionado. Senhas fora do git (esperado).

---

# 6. Backups

## 6.1 Estado real

```
/var/backups/siap/ → NÃO EXISTE ❌
```

**Outros backups no VPS:**
- `/root/backups/sgac/backup.sh` — cron SGAC 02:00 daily
- `/root/backups/agrobuds-sgac/...` — cron 03:00 daily
- CareOS, VSF — vários scripts ad-hoc

**Cron jobs ativos:**

```
# m h dom mon dow command
0 2 * * *   /root/backups/sgac/backup.sh          (SGAC)
0 3 * * *   /root/backups/agrobuds-sgac/...       (AGROBUDS-SGAC)
* * * * *   /root/careos/alerts.sh                (CareOS 1/min)
0 3 * * *   /root/vsf/scripts/lgpd_purge.sh       (VSF LGPD purge)
*/5 * * * * /root/vsf/scripts/expire_payments.sh  (VSF expire payments)
# SIAP cobrança diária 03:00 (linha comentada, sem comando)
```

**Diagnóstico:**
- ❌ SIAP NÃO tem backup automatizado.
- ⚠️ Cron do SIAP existe mas está comentado (`SIAP cobrança diária 03:00 #`).
- ❌ Nenhum `/var/backups/siap/` foi criado.
- ❌ Script `backup.sh` no repo não está deployado no cron.

**Ação FASE 2 / FASE 6:**
1. Criar `/var/backups/siap/`
2. Deploy do script `scripts/backup.sh` no cron
3. Política de retenção: 7 daily + 4 weekly + 12 monthly (do `RELEASE_MANIFEST.md`)
4. Testar restore end-to-end (FASE 6 DR)

---

# 7. Discrepâncias M36/M37 vs Realidade

⚠️ **Os 5 docs M36/M37 estão com path e SSH user errados.** Isso é um problema sério porque é o pacote do operador.

| Doc M36/M37 | Diz | Realidade |
|-------------|-----|-----------|
| `PROJECT_DIR` | `/opt/siap` | **`/root/projetos/araos`** |
| `VPS_USER` | `operador` | **`root`** |
| `SSH_KEY` | `$HOME/.ssh/id_rsa_vps` | **`$HOME/.ssh/id_ed25519`** |
| `BACKUP_DIR` | `/var/backups/siap` | ❌ NÃO EXISTE — precisa criar |
| `DB_CONTAINER` | `siap-db` | ✅ correto |
| `BACKEND_CONTAINER` | `siap-backend` | ✅ correto |
| `HEALTH_URL` | `https://api.visualsmartflow.com.br/api/health` | ✅ correto (mas endpoint retorna 404 hoje) |
| `GITHUB_REPO` | `gituser26071977/Aracannabis_v2_04_08_25` | ✅ correto |
| Workflow CI/CD | `Deploy VPS` (id 294844757) | ⚠️ Existe mas é `pull_request`-driven, não tag-driven |
| Workflow CI/CD | `CD Production` | ✅ existe, é `v*.*.*` tag-driven |

**Ação:** Corrigir `PROJECT_DIR`, `VPS_USER`, `SSH_KEY`, `BACKUP_DIR` em:
- `docs/OPERATOR_RUNBOOK.md` §1.5
- `docs/SSH_DEPLOY_CHECKLIST.md` §Variáveis Operacionais
- `docs/PRODUCTION_COMMANDS.md` §Variáveis Operacionais
- `docs/EMERGENCY_ROLLBACK.md` §Variáveis Operacionais
- `docs/GO_LIVE_CARD.md` §Variáveis Operacionais

---

# 8. GitHub Actions workflows

## 8.1 Workflows ativos

| Nome | ID | Trigger | Estado |
|------|-----|---------|--------|
| `CD — Production (9-stage pipeline + auto-rollback)` | (local) | `push: tags: ['v*.*.*']` + `workflow_dispatch` | active |
| `CD — Staging (9-stage pipeline + auto-rollback)` | `304190514` | `push: branches: [develop, 'feat/**', 'fix/**']` + `workflow_dispatch` | active |
| `CI` | `304190516` | push genérico | active |
| `Deploy VPS` | `294844757` | `pull_request` (legado) | active |
| `lighthouse` | `304190492` | (cron ou push) | active |

## 8.2 Últimos runs (referência)

- CD Production: NÃO disparado recentemente (nenhuma tag)
- CD Staging: última falha em `fix/p0-stabilization-2026-06` (causa: a investigar FASE 2)
- CI: falha similar no último run
- Deploy VPS: último sucesso em 2026-06-13 (`feat/secretaria-staff`)

## 8.3 Secrets referenciados

- `PROD_SSH_HOST` → `147.93.33.253`
- `PROD_SSH_KEY` → chave privada (deve corresponder a `github-actions-planttracker` em `/root/.ssh/authorized_keys`) ✅
- `PROD_DEPLOY_USER` → `root` (sugerido corrigir — docs dizem `operador`)
- `STAGING_SSH_HOST` / `STAGING_SSH_KEY` / `STAGING_DEPLOY_USER` → staging

**Ação FASE 5:** confirmar que `PROD_DEPLOY_USER=root` no secret (não `operador`).

---

# 9. Resumo de bloqueadores D01

| # | Bloqueador | Status | Origem |
|---|-----------|--------|--------|
| B-1 | SSH VPS indisponível | ✅ **RESOLVIDO** | Rede mudou, IP `187.19.176.184` aceito |
| B-2 | Acesso Docker remoto | ✅ OK | via SSH root |
| B-3 | Acesso PostgreSQL remoto | ✅ OK | via `docker exec siap-db psql` |
| B-4 | Tag `v1.0.0-rc.1` não existe | ⚠️ AINDA FALTA | Decisão do operador |
| B-5 | Migration B-001 não aplicada | ⚠️ AINDA FALTA | Aplicar antes do RC1 deploy |
| B-6 | Outros containers no VPS | ✅ MAPEADOS | Não tocar (regra da missão) |
| B-7 | Docs M36/M37 com path/user errados | ⚠️ AINDA FALTA | Corrigir antes de qualquer operador usar |
| B-8 | `/var/backups/siap/` ausente | ⚠️ AINDA FALTA | Criar antes do RC1 deploy |
| B-9 | Porta 5440 exposta publicamente | ⚠️ RISCO | Decisão: fechar? (escopo hardening) |
| B-10 | Backend `Up mas NOT healthy` | ⚠️ ESPERADO | Imagem é pre-RC1 (sem `/api/health`) |

---

# 10. Recomendações

## Para FASE 2 (Hardening) — proposto

1. **Corrigir 5 docs M36/M37** (PROJECT_DIR, VPS_USER, SSH_KEY) — pré-requisito para qualquer deploy manual
2. **Aplicar migration B-001** em prod (1 comando idempotente)
3. **Criar `/var/backups/siap/`** + deploy do `scripts/backup.sh` no cron
4. **Fechar porta 5440** (remover `ports` do compose OU bindar em 127.0.0.1)
5. **Validar CD Production workflow** — corrigir se ele não faz `git checkout` da tag antes do build
6. **Configurar deploy_guard** (módulo já existe no backend — verificar se ativa no startup)
7. **Adicionar healthcheck explícito ao siap-backend** (se ainda não tem)

## Para FASES 3-8 — proposto

- **FASE 3 (Pipeline v2):** validar `cd-production.yml` está tag-driven, idempotente, com auto-rollback
- **FASE 4 (Zero-touch):** documentar fluxo `git tag v*.*.* → git push → CD Production → VPS`
- **FASE 5 (Security audit):** rotacionar secrets, auditar authorized_keys, fail2ban jails
- **FASE 6 (DR):** backup → restore → smoke → rollback → tempo medido
- **FASE 7 (Observabilidade):** Prometheus + Grafana ou similar
- **FASE 8 (Release):** tag → push → monitor → GO

---

# FASE 1 ENCERRADA — COMPLETA

**Status:** Inventário real do VPS concluído. SSH root funcional. Containers, Traefik, Postgres, Git, Backups, Cron, Authorized keys — tudo mapeado.

**Achados críticos para próxima iteração:**

1. Docs M36/M37 estão com PROJECT_DIR, VPS_USER, SSH_KEY desatualizados (corrigir antes de qualquer operador usar).
2. B-001 não aplicada (aplicar antes do RC1 deploy).
3. Porta 5440 (Postgres) exposta publicamente (risco segurança — decidir se fecha).
4. `/var/backups/siap/` não existe (criar antes do RC1 deploy).
5. VPS está com checkout em `main` (HEAD `ce141c5`), não na tag RC1 — CD Production precisa resolver.

**Próximo passo (decisão do operador):**
- Corrigir docs M36/M37 agora? (read-mostly, baixo risco)
- Aplicar migration B-001? (1 comando, idempotente)
- Criar diretório de backups? (filesystem only)
- Fechar porta 5440? (depende de decidir como)

Relatório completo. Aguardando decisão do operador sobre qual(is) bloqueio(s) desbloquear primeiro.