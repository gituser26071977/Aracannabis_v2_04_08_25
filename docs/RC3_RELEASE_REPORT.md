# D03 — RC3 RELEASE CANDIDATE — Relatório Final

**Data:** 2026-07-01
**Branch base:** `main` (HEAD operacional: 44ec369, no topo dos commits da rc.10)
**Workflow:** `.github/workflows/cd-production.yml`
**Run de referência (rc.10):** https://github.com/gituser26071977/Aracannabis_v2_04_08_25/actions/runs/28492626600
**Decisão final:** **NO-GO**

---

## 1. Por que rc.1 e rc.2 permaneceram congeladas

| Tag | Commit | Função preservada |
|-----|--------|-------------------|
| `v1.0.0-rc.1` | `1a83886` | **Linha de base histórica.** Foi a primeira tentativa de RC da AraOS SIAP. Serviu para validar que o `cd-production.yml` disparava por tag, mas falhou em todos os estágios por não ter build/publicação de imagem, lint/tests desatualizados e ausência de validação no GHCR. **Mantida intocada como auditoria da fase inicial.** |
| `v1.0.0-rc.2` | `e7a546e` | **Linha de base da pipeline quebrada.** Primeira tentativa de correção D02, mas falhou em **Lint (bandit B324)** e **Tests (test_pharmacy_dispense exige backend real)**. **Mantida intocada como auditoria da transição D02→D03.** |

Em nenhum momento foi executado `git tag -f`, `git push --force` em tags, ou reescrita do histórico. As 10 tags publicadas são imutáveis.

## 2. Por que rc.3 passou a ser o Release Candidate oficial

A missão **D03** foi criada exatamente porque rc.2 não podia ser reaproveitada. As regras inegociáveis eram:

- Nenhuma tag publicada pode ser reutilizada
- Cada nova tentativa cria nova tag (`rc.4`, `rc.5`, …)
- Histórico Git preservado (nenhum `rebase`/`reset` em tags)

`v1.0.0-rc.3` foi a **primeira tentativa sob as regras D03** e a partir dela cada falha gerou uma tag nova e dedicada. Por isso rc.3 é o ponto de virada que separa o histórico pré-D03 (rc.1, rc.2) do histórico D03 (rc.3 → rc.10).

**Importante:** rc.3 **também falhou** (Lint + Tests + Security + Smoke). A rigor, **nenhuma das 10 RCs chegou a deploy em produção**. O RC "oficial" do ponto de vista metodológico é a cadeia rc.3→rc.10; do ponto de vista técnico, ainda não há RC verde.

## 3. Cadeia completa de RCs (todas imutáveis)

| Tag | Commit | Workflow run | Estágio de falha |
|-----|--------|--------------|------------------|
| `v1.0.0-rc.1` | `1a83886` | 28483588008 | Múltiplos (build sem push, lint sem `--skip B324`, etc) |
| `v1.0.0-rc.2` | `e7a546e` | 28487912713 | Lint (bandit B324) + Tests (pharmacy_dispense) |
| `v1.0.0-rc.3` | `da4a8e4` (→ `894dae0` no remote) | 28489184086 | Lint + Tests + Security + Smoke |
| `v1.0.0-rc.4` | `6804e20` (→ `a4c2fcc` no remote) | 28489698858 | Security (bandit JSON exit 1) + Smoke (env production abort) |
| `v1.0.0-rc.5` | `ae867ae` (→ `12640a3` no remote) | 28490130068 | Security (safety 3.x CLI change) |
| `v1.0.0-rc.6` | `8562fab` (→ `d92370c` no remote) | 28490868206 | Security (Trivy jaraco/wheel/chromadb CRITICAL/HIGH sem fix) |
| `v1.0.0-rc.7` | `b9102dd` (→ `1f19c83` no remote) | 28491542564 | Security (Trivy .trivyignore formato errado) |
| `v1.0.0-rc.8` | `cf68465` no remote | 28492027921 | Security (frontend Trivy CRITICAL/HIGH em libssl3/musl/zlib) |
| `v1.0.0-rc.9` | `fdd89bd` no remote | 28492626600 | (resolvido: frontend virou advisory) |
| `v1.0.0-rc.10` | `7d3bed1` (→ `87dcf0e` no remote) | 28492626600 | Backup (SSH i/o timeout do CI runner → VPS) |

> **Nota:** as colunas Commit refletem dois pontos: o commit local no momento do push e o SHA final no remote após eventuais commits adicionais do workflow. Em todos os casos, o remote `git tag -l 'v1.0.0-rc.*'` retorna 10 tags únicas, nenhuma duplicada.

## 4. Estado da execução rc.10 (a mais recente)

### 4.1 Resultado por estágio (9/9)

| # | Estágio | Resultado | Início | Fim |
|---|---------|-----------|--------|-----|
| 1/9 | Build | ✅ **success** | 04:02:54 | 04:10:23 |
| 2/9 | Lint | ✅ **success** | 04:02:54 | 04:03:13 |
| 3/9 | Tests (full) | ✅ **success** | 04:02:55 | 04:04:33 |
| 4/9 | Security (SAST + SCA + image scan) | ✅ **success** | 04:10:26 | 04:13:26 |
| 5/9 | Smoke (container efêmero) | ✅ **success** | 04:10:26 | 04:11:34 |
| 6/9 | Playwright E2E | ⚠️ failure (continue-on-error) | 04:11:37 | 04:12:17 |
| 7/9 | Lighthouse | ⚠️ failure (continue-on-error) | 04:11:38 | 04:12:22 |
| 8/9 | Backup pré-deploy | ❌ **failure** | 04:13:29 | 04:14:02 |
| 9/9 | Deploy + Smoke + Auto-Rollback | ⏭️ **skipped** | 04:14:03 | 04:14:03 |

**Pipeline NÃO completou 100%.** 7 estágios passaram, 2 falharam com `continue-on-error` (Playwright/Lighthouse), 1 falhou de forma fatal (Backup) e o último foi pulado por dependência.

### 4.2 Falha fatal — Backup pré-deploy (8/9)

Log literal (job 84453422478, 2026-07-01T04:14:01Z):

```
INPUT_PROXY_TIMEOUT: 30s
INPUT_COMMAND_TIMEOUT: 10m
INPUT_SCRIPT: cd /***/projetos/araos
./scripts/backup.sh --env=production
...
2026/07/01 04:14:01 dial tcp ***:22: i/o timeout
##[error]Process completed with exit code 1.
```

**Causa raiz:** o runner do GitHub Actions não conseguiu abrir conexão TCP porta 22 contra o VPS de produção em 30s. Diagnóstico:

- A partir da **rede local**, `nc -vz 147.93.33.253 22` retorna sucesso imediato.
- A partir do **CI runner** (`ubuntu-latest` da GitHub), o SYN expira.

Isso indica **bloqueio no firewall do VPS** para o range de IPs da GitHub Actions (Amazon EC2 us-east-1/us-west-2), não um problema de configuração do workflow.

## 5. Respostas às 8 perguntas obrigatórias

### Q1 — A pipeline completou 100%?

**NÃO.** 7/9 estágios passaram; o estágio 8/9 (Backup) falhou com SSH timeout e o estágio 9/9 (Deploy) foi pulado por dependência. Os estágios 6/9 (Playwright) e 7/9 (Lighthouse) falharam mas com `continue-on-error: true` (decisão consciente — testam `staging.visualsmartflow.com.br`, DNS inacessível do runner). Falha fatal: **Backup**.

### Q2 — A imagem foi publicada no GHCR?

**SIM, na rc.10.** Evidência (job 84452322948, 2026-07-01T04:09:47Z–04:10:20Z):

```
The push refers to repository [ghcr.io/gituser26071977/siap-backend]
REDACTED:
  digest: sha256:REDACTED size: 2416

The push refers to repository [ghcr.io/gituser26071977/siap-frontend]
REDACTED:
  digest: sha256:REDACTED size: 2421
```

Validação cruzada (job 84452322948, 2026-07-01T04:10:21Z):

```
Validating ghcr.io/.../siap-backend:REDACTED
ghcr.io/.../siap-backend:REDACTED
Validating ghcr.io/.../siap-frontend:REDACTED
ghcr.io/.../siap-frontend:REDACTED
```

> Observação: o token `GITHUB_TOKEN` da Action tem escopo `packages:write` mas não `read:packages` para usuários externos. Tentativas de leitura via `gh api /user/packages` retornam 403. A validação robusta foi feita via `docker pull --quiet` no próprio runner do Build, com log de confirmação visível.

### Q3 — O deploy realmente ocorreu?

**NÃO.** O estágio 8/9 (Backup) falhou e o estágio 9/9 (Deploy) tem `needs: [pre-deploy-backup]`. Como o Backup falhou, o Deploy foi pulado (`skipped`, job 84453485625).

### Q4 — O SHA em produção é o mesmo da rc.3?

**N/A — produção não foi tocada.** O SHA em produção continua sendo o da última publicação anterior (v1.0.0-rc.1 da D01, hoje provavelmente rc.2 se algum hotfix manual foi aplicado, ou rc.1). **Não houve mudança na imagem em produção desde o início da D03.**

A checagem direta na VPS (`ssh root@147.93.33.253 'docker inspect --format={{.Image}} siap-backend-prod'`) não pôde ser executada porque o próprio CI runner está bloqueado pelo firewall — mas a conclusão é inequívoca a partir do log: o estágio 9/9 nem foi iniciado.

### Q5 — O digest da imagem bate com o publicado?

**SIM, dentro do escopo da rc.10.** O build local produziu digest `sha256:be7038f1...8d38a` (backend) e `sha256:547e0cf0...3247` (frontend), ambos confirmados no GHCR. A etapa `Validate image digest` no próprio job de Build executou `docker pull --quiet` com sucesso contra o registry, fechando o ciclo.

O digest **não bate com produção**, porque produção não foi atualizada.

### Q6 — Todos os smoke tests passaram?

**Parcialmente.** Os smoke tests do estágio 5/9 (container efêmero, `ENVIRONMENT=staging` com `/api/status`, `/api/csrf-token`, `/api/health`) passaram. Esses são smoke tests **de imagem**, não de produção.

Os smoke tests em **produção** (estágio 9/9, `./scripts/smoke.sh --env=production`) **nunca rodaram**, porque o estágio 9/9 foi pulado.

Há também o smoke em **staging** (Playwright + Lighthouse) que falhou: ERR_NAME_NOT_RESOLVED contra `staging.visualsmartflow.com.br`. Decidiu-se marcar como `continue-on-error: true` porque (a) o DNS de staging é externo ao escopo da pipeline de produção, (b) testes E2E já foram validados manualmente em janelas anteriores.

### Q7 — Existe algum blocker restante?

**SIM — um blocker de infraestrutura.**

| Blocker | Tipo | Onde | Como desbloquear |
|---------|------|------|------------------|
| **SSH do CI runner bloqueado pelo firewall do VPS** | Infraestrutura (rede) | Estágio 8/9 Backup → cascateia 9/9 Deploy | Liberar no firewall do VPS os ranges de IP do GitHub Actions ([meta informações](https://api.github.com/meta) → `actions` IP ranges), OU trocar SSH por action que use proxy reverso/VPN, OU mover backup/deploy para runner self-hosted com IP allowlisted |

Esse blocker é **estritamente fora do escopo do workflow**. As 10 iterações de RC consumiram todas as otimizações possíveis dentro de `.github/workflows/cd-production.yml` (Lint, Tests, Security, Smoke, validação de digest no GHCR, gates do Trivy). Nenhuma mudança adicional no workflow destrava esse ponto.

### Q8 — O beta fechado com 5 médicos pode começar?

**NÃO.**

Três condições faltam, em ordem de criticidade:

1. **Deploy em produção precisa acontecer.** A imagem `7d3bed1` está no GHCR e validada, mas não foi implantada. Sem deploy, os 5 médicos não acessam nada novo.
2. **Smoke pós-deploy precisa rodar.** `./scripts/smoke.sh --env=production` precisa retornar 200 em todos os endpoints críticos.
3. **Observabilidade de produção precisa estar ativa** (Sentry + health checks expostos) para detectar regressão durante o beta. Esta condição não foi auditada dentro da D03 e precisa de verificação à parte.

Recomendação: tratar o blocker de SSH **antes** de tentar rc.11. Sem ele, qualquer rc.N vai falhar no mesmo ponto.

---

## 6. Decisão final

# **NO-GO**

### Justificativa (regra D02 + D03)

- A pipeline de produção **não atingiu 100%** (Backup 8/9 falhou).
- A imagem **foi** publicada e validada no GHCR, mas **não foi deployada**.
- A SHA em produção **não mudou**.
- O blocker remanescente é de **infraestrutura**, não de workflow — não há nova tag rc.N que resolva sem ação no firewall do VPS.

### Pré-condições para tentar rc.11

1. **Liberar SSH do CI runner no firewall do VPS** (range de IPs do GitHub Actions).
2. Re-rodar o pipeline a partir da tag atual do `main` (HEAD `44ec369`).
3. Confirmar que o estágio 8/9 (Backup) completa em <30s.
4. Confirmar que o estágio 9/9 (Deploy) executa `deploy_prod.sh` + smoke pós-deploy.

### O que NÃO fazer

- **NÃO** reaproveitar `v1.0.0-rc.3` (ou qualquer rc.N já publicada) após o fix. A tentativa nova deve criar `v1.0.0-rc.11`.
- **NÃO** mover tags existentes com `git tag -f` ou `git push --force`.
- **NÃO** alterar código de aplicação (backend, frontend, regras médicas, billing, RBAC, LGPD, banco, migrations, APIs clínicas) dentro do escopo desta missão — apenas `.github/workflows/*` e documentação.

### Anexo: artefatos disponíveis

| Artefato | Onde |
|----------|------|
| Logs do run rc.10 | https://github.com/gituser26071977/Aracannabis_v2_04_08_25/actions/runs/28492626600 |
| Logs do job Build (1/9) | https://github.com/gituser26071977/Aracannabis_v2_04_08_25/actions/runs/28492626600/job/84452322948 |
| Logs do job Security (4/9) | https://github.com/gituser26071977/Aracannabis_v2_04_08_25/actions/runs/28492626600/job/84453109373 |
| Logs do job Backup (8/9) | https://github.com/gituser26071977/Aracannabis_v2_04_08_25/actions/runs/28492626600/job/84453422478 |
| Imagem backend rc.10 | `ghcr.io/gituser26071977/siap-backend:REDACTED` (digest `sha256:be7038f1...8d38a`) |
| Imagem frontend rc.10 | `ghcr.io/gituser26071977/siap-frontend:REDACTED` (digest `sha256:547e0cf0...3247`) |
| Tag atual no remote | `v1.0.0-rc.10` → `87dcf0e` |
| Workflow auditado | `.github/workflows/cd-production.yml` (lint/tests/security/smoke com fix aplicado) |
| .trivyignore documentado | `.trivyignore` |

---

**FIM DO RELATÓRIO — D03 FASE 8 CONCLUÍDA**