# D05l — Pipeline CI: Tailscale v4 OAuth + URLs de produção

## Contexto

O pipeline `cd-production.yml` falhou no run `28825810720` (tag `v1.0.0-rc.13`):

- 6/9 Playwright E2E → failure (DNS NXDOMAIN em `staging.visualsmartflow.com.br`)
- 7/9 Lighthouse → failure (mesmo motivo)
- **8/9 Backup pré-deploy → failure** (Tailscale `authkey` deprecado) → **9/9 Deploy skipped**

O deploy em produção **não ocorreu** porque o gate `pre-deploy-backup` falhou.

## Mudanças aplicadas

### 1. Tailscale v2 → v4 com OAuth client

A Tailscale deprecou o input `authkey` em favor de OAuth client. Migração:

```yaml
# ANTES (v2 — deprecado)
- uses: tailscale/github-action@v2
  with:
    authkey: ${{ secrets.TS_AUTHKEY }}

# DEPOIS (v4 — recomendado)
- uses: tailscale/github-action@v4
  with:
    oauth-client-id: ${{ secrets.TS_OAUTH_CLIENT_ID }}
    oauth-secret: ${{ secrets.TS_OAUTH_SECRET }}
    tags: tag:ci
```

Aplicado em **4 pontos** do `cd-production.yml`:
- 8/9 Backup pré-deploy
- 9/9 Deploy produção
- 9/9 Post-deploy smoke
- 9/9 Auto-rollback

### 2. URLs staging → produção

`staging.visualsmartflow.com.br` **NÃO EXISTE** (NXDOMAIN). O conftest do Playwright e o `.lighthouserc.json` foram apontados para `visualsmartflow.com.br` (que resolve para 147.93.33.253).

| Arquivo | Antes | Depois |
|---------|-------|--------|
| `tests/e2e/conftest.py` | `BASE_URL = staging.visualsmartflow.com.br` | `BASE_URL = visualsmartflow.com.br` |
| `.github/workflows/cd-production.yml` (Playwright step) | `BASE_URL: https://staging.visualsmartflow.com.br` | `BASE_URL: https://visualsmartflow.com.br` |
| `.lighthouserc.json` (4 URLs) | staging.visualsmartflow.com.br | visualsmartflow.com.br |

### 3. Plano desconto 40% → 20%

`frontend/src/pages/PlanosPage.js`:
- Linha 95: `* 0.6` → `* 0.8` (40% off → 20% off para outros profissionais de saúde)
- Linha 165: `(-40% OFF)` → `(-20% OFF)`

### 4. Redis URL config

`config.Config.REDIS_URL` agora expõe a env var (corrige `/api/health` que caía no fallback `localhost:6379` em prod).

## Ações manuais necessárias no GitHub

**Secrets a criar/atualizar em `Settings → Secrets and variables → Actions`:**

| Secret | Status | Valor |
|--------|--------|-------|
| `TS_OAUTH_CLIENT_ID` | **CRIAR** | OAuth client ID do Tailscale admin (https://login.tailscale.com/admin/oauth) |
| `TS_OAUTH_SECRET` | **CRIAR** | OAuth secret correspondente |
| `TS_AUTHKEY` | Manter (legacy) | Não usado pelo v4, mas pode ficar como backup |

**Como criar OAuth client no Tailscale:**
1. Acesse https://login.tailscale.com/admin/oauth
2. New OAuth client
3. Scopes: `auth_keys` (write)
4. Tags: `tag:ci`
5. Copie `client_id` e `secret` para os secrets do GitHub

## Verificação pós-deploy (após secrets configurados)

1. Commit + push + tag `v1.0.0-rc.14`
2. Acionar `cd-production.yml` (auto via tag push)
3. Validar:
   - 8/9 Backup: Tailscale conecta via OAuth, backup roda em `/var/backups/siap/`
   - 9/9 Deploy: SSH conecta ao VPS via Tailscale IP, `docker-compose pull + up` executa
   - Post-deploy smoke: `./scripts/smoke.sh --env=production` passa
   - Email de cadastro novo menciona "14 dias" e link `/planos`

## Riscos / observações

- **Playwright contra produção** é arriscado (pode interferir com dados reais). Mantido `continue-on-error: true` para não bloquear deploy.
- **Lighthouse contra produção** mede o sistema real; oscilações de CDN podem dar flaky.
- **OAuth client tem escopo limitado** (`auth_keys:write`); não pode ler/modificar outros recursos do tailnet.