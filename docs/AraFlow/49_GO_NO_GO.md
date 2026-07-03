# AraFlow RC1.1 — GO / NO-GO

**Versão:** 1.0.0
**Data:** 2026-07-03
**Pergunta única:** A infraestrutura está pronta para receber o deploy do AraFlow RC1?

---

## 🔴 NO GO

**3 bloqueadores impedem o deploy no estado atual. Veja detalhes abaixo.**

---

## Bloqueadores

### 🔴 B1 — Tailscale em `NeedsLogin` (VPS inacessível via SSH externo)

**O quê:** `tailscale status` no VPS retorna `NeedsLogin` (TS_AUTHKEY ausente). Sem Tailscale ativo, não há rota SSH externo para `147.93.33.253`; o operador fica restrito ao console de Hostinger, que torna o runbook inseguro para uma primeira execução de produção.

**Por que bloqueia:** o deploy é 100% manual via SSH. Sem Tailscale, qualquer rollback em janela de 5 min fica comprometido.

**Quem resolve:** Operador (VPS owner).
**Como resolver:**
```bash
sudo tailscale up --authkey=tskey-auth-XXXXXXXXXXXX
tailscale status   # deve mostrar host "online"
```

**Critério de desbloqueio:** `tailscale status` mostra o VPS como `online` e `tailscale ping <seu-ip-local>` retorna pong.

---

### 🔴 B2 — Pacotes GHCR `araflow-api` e `araflow-web` ainda não foram publicados

**O quê:** o workflow `cd-araflow.yml` nunca foi disparado. Sem build+push, as imagens `ghcr.io/gituser26071977/araflow-{api,web}:rc1-latest` não existem. `docker pull` retorna `manifest unknown`.

**Por que bloqueia:** sem imagens, `docker compose pull` falha imediatamente no passo 9 do runbook. O deploy nem chega à fase de up.

**Quem resolve:** Operador (com permissão `packages: write` no GitHub).
**Como resolver:**
1. UI: GitHub → Actions → `CD — AraFlow RC1 (build + push GHCR, no deploy)` → `Run workflow` → branch `main` → `Run`.
2. CLI: `gh workflow run cd-araflow.yml --ref main`.
3. Aguardar 5/5 jobs verdes (≤ 25 min).

**Critério de desbloqueio:** ambos os pacotes visíveis em `https://github.com/gituser26071977?tab=packages` e `docker pull ghcr.io/gituser26071977/araflow-api:rc1-latest` baixa com sucesso.

---

### 🔴 B3 — Pacotes GHCR estão com visibilidade `private` (default)

**O quê:** quando a CI criar os pacotes pela primeira vez, eles herdam visibilidade `private`. O `docker pull` da VPS (sem credencial GHCR persistente) falhará com `requested access to the resource is denied`.

**Por que bloqueia:** deploy sem login GHCR no VPS é parte do design (simplifica operação). Sem tornar público, é necessário configurar `docker login` no VPS e armazenar credencial — adiciona segredo e ponto de falha.

**Quem resolve:** Operador (admin do GitHub Packages).
**Como resolver:**
1. `https://github.com/gituser26071977?tab=packages` → `araflow-api` → `Package settings` → `Danger Zone` → `Change visibility` → `Public` → confirmar.
2. Repetir para `araflow-web`.

**Critério de desbloqueio:** ambos packages mostram badge `Public` e `curl -fsSI https://ghcr.io/v2/gituser26071977/araflow-api/manifests/rc1-latest` retorna 200/401 (não 404).

---

## Pendências NÃO-bloqueantes (mas devem ser resolvidas para produção estável)

| # | Item | Por que não bloqueia | Quando resolver |
|---|---|---|---|
| P1 | DNS `flow.arapath.com.br` A → 147.93.33.253 | Letsencrypt não emite cert sem DNS; mas VPS pode ser acessado via IP direto para smoke inicial | Antes de expor publicamente |
| P2 | Cloudflare Proxy `off` (se a zona estiver lá) | Se proxy estiver `on`, ACME challenge do letsencrypt falha | Antes do primeiro request HTTPS |
| P3 | Versão de produção do `.env.araflow` com `GIT_COMMIT`/`BUILD_TIME` reais | /health retornará `commit: "unknown"` (degradação cosmética) | Após primeiro deploy |

> **Nota:** P1 + P2 juntas formam um "sub-bloqueador" — sem DNS válido com proxy off, **o /health público não responde** (Traefik não consegue emitir cert). O deploy dos containers acontece, mas a URL pública fica 404/502 até o DNS ser resolvido. O smoke interno (passo 11 do runbook) ainda funciona.

---

## Resumo da auditoria técnica (o que ESTÁ pronto)

| Componente | Status | Evidência |
|---|---|---|
| Repositório (22 artefatos) | ✅ | `49_PRE_DEPLOY_AUDIT.md` §2 |
| Compose + Traefik labels | ✅ | Zero colisão com AraOS (9 nomes `siap-*` + 6 nomes `araflow-*`, intersection = 0) |
| Portas livres | ✅ | 5005 e 8080 não usadas por AraOS |
| Dockerfiles hardened | ✅ | non-root + read_only + healthcheck em ambos |
| /health endpoint | ✅ | Retorna JSON correto com `version`, `commit`, `build`, `uptime` |
| CI workflow | ✅ | `workflow_dispatch` only, 0 ssh/scp, build+push GHCR |
| Rollback ≤ 5 min | ✅ | Documentado em `49_DEPLOY_RUNBOOK.md` §5 |
| Smoke test | ✅ | 24 itens verificáveis em `49_SMOKE_TEST.md` |
| AraOS não-impact | ✅ | Gate validado: 10/10 serviços AraOS byte-identical antes/depois do compose AraFlow |

---

## Sequência para destravar

Ordem importa — algumas dependem de outras.

1. **Resolver B1** (Tailscale up) — sem isso, nenhum outro passo pode ser executado via SSH.
2. **Resolver B2** (disparar CI) — pode ser feito em paralelo com B1.
3. **Resolver B3** (tornar GHCR public) — fazer ANTES de B2 terminar (configurar visibilidade antes do primeiro push, ou imediatamente após).
4. **Resolver P1 + P2** (DNS + Cloudflare proxy off) — pode ser feito em paralelo, mas o smoke público só funciona após isso.
5. Re-rodar `49_PRE_DEPLOY_AUDIT.md` §3 (auditoria VPS read-only) para confirmar estado.
6. Iniciar `49_DEPLOY_RUNBOOK.md` passo 1.
7. Executar `49_SMOKE_TEST.md` após deploy.
8. Re-rodar gate de não-impact AraOS (passo 12 do runbook + 6.1 do smoke).

**Tempo total estimado (após desbloqueio dos 3):** ~45 min (20 min para CI, 5 min para DNS, 15 min para deploy + smoke, 5 min de buffer).

---

## Re-decisão

Quando todos os 3 bloqueadores forem resolvidos, este documento deve ser **atualizado** trocando o cabeçalho para:

```markdown
# AraFlow RC1.1 — GO / NO-GO

## 🟢 GO

Todos os 3 bloqueadores foram resolvidos:

- ✅ B1 — Tailscale autenticado (`tailscale status` mostra host online)
- ✅ B2 — Imagens publicadas em GHCR (`docker pull` baixa com sucesso)
- ✅ B3 — Visibilidade `Public` (badge visível nos packages)

A infraestrutura está pronta. Prosseguir com `49_DEPLOY_RUNBOOK.md` passo 1.
```

A re-decisão é responsabilidade do **operador**, não do sistema automatizado.

---

## Anexo — comando único de checagem pré-deploy

O operador pode rodar este one-liner para validar TODOS os 3 bloqueadores de uma vez:

```bash
# Requer: VPS acessível via Tailscale, conta GitHub autenticada, dig instalado
ssh deploy@147.93.33.253 << 'EOF'
  echo "=== B1 Tailscale ==="
  tailscale status 2>&1 | head -3
  echo ""
  echo "=== B2/B3 GHCR (do VPS) ==="
  docker pull ghcr.io/gituser26071977/araflow-api:rc1-latest 2>&1 | head -5
  echo ""
  echo "=== P1 DNS (do VPS, via curl) ==="
  curl -fsS --max-time 5 https://flow.arapath.com.br/health -o /dev/null -w "HTTPS: %{http_code}\n" 2>&1
  curl -fsS --max-time 5 http://flow.arapath.com.br/ -o /dev/null -w "HTTP: %{http_code}\n" 2>&1
EOF
```

**Interpretação:**

| B1 | B2/B3 | P1 | Diagnóstico |
|---|---|---|---|
| `online` | `Downloaded` | `200` | 🟢 **GO** |
| `online` | `Downloaded` | `000` (timeout) | 🟡 DNS pendente — deploy funciona, smoke público falha |
| `online` | `denied` | * | 🟡 B3 pendente — tornar packages public |
| `online` | `manifest unknown` | * | 🟡 B2 pendente — disparar CI |
| `NeedsLogin` | * | * | 🔴 B1 pendente — sem SSH externo, parar aqui |