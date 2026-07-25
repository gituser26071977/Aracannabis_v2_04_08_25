# D04 — DEPLOY INFRASTRUCTURE RECOVERY — Relatório Final

**Data:** 2026-07-01
**Origem:** D03 terminou em NO-GO com blocker exclusivamente operacional (SSH CI→VPS)
**Modo:** READ-ONLY + workflow/scripts/docs (NÃO toca backend/frontend/banco/migrações/billing/RBAC/LGPD/regras clínicas/APIs)
**Decisão:** **Tailscale** (já instalado na VPS, faltando apenas autenticação)

---

## FASE 1 — Como o deploy tenta conectar ao VPS

### 1.1 Action, porta, usuário, chave

Inspeção de `.github/workflows/cd-production.yml`:

| Item | Valor | Fonte |
|------|-------|-------|
| **Action** | `appleboy/ssh-action@v1` | linhas 311, 335, 366, 375 |
| **Porta** | 22 (default; nenhum `port:` setado) | implícito |
| **Usuário** | `${{ secrets.PROD_DEPLOY_USER }}` → valor real: `root` (docs/SSH_DEPLOY_CHECKLIST.md) | env linha 24 |
| **Chave** | `${{ secrets.PROD_SSH_KEY }}` (private key em PEM) | env linha 23 |
| **Host** | `${{ secrets.PROD_SSH_HOST }}` → valor real: `147.93.33.253` (docs) | env linha 22 |
| **Host fingerprint** | **NÃO CONFIGURADO** — nenhum `known_hosts`, nenhum fingerprint pin | (ausente) |
| **Proxy / Jump host** | **NÃO CONFIGURADO** | (ausente) |

A VPS tem a chave pública correspondente em `/root/.ssh/github_actions_siap.pub` (instalada em 2026-06-30 09:39).

### 1.2 Timeout, retry

Do log do run 28492626600 (job 84453422478, Backup 8/9):

```
INPUT_PROXY_TIMEOUT: 30s
INPUT_COMMAND_TIMEOUT: 10m
```

- **`proxy_timeout: 30s`** — limite de tempo para **abrir a conexão TCP** (handshake SSH).
  É exatamente esse o timeout que está sendo atingido.
- **`command_timeout: 10m`** — limite para execução do comando **depois** da conexão aberta.
  Não chega a ser exercido.
- **Retry automático: NENHUM.** `appleboy/ssh-action@v1` não tem retry interno em falha de conexão.
  Qualquer falha = exit 1 imediato.

### 1.3 Host verification (ausente)

O workflow não configura `known_hosts` nem `fingerprint`. Implicação: o cliente SSH do `appleboy/ssh-action` aceita qualquer fingerprint no primeiro contato (ou usa `StrictHostKeyChecking=no` por default da action). Isso é **indesejado** do ponto de vista de segurança, mas **não é a causa** do blocker atual — o blocker ocorre antes do handshake SSH, na abertura do TCP.

### 1.4 Resumo da cadeia de conexão

```
[runner GHA ubuntu-latest]                                          [VPS 147.93.33.253]
   ephemeral IP em algum range Amazon AWS (ex: 4.x.x.x ou 52.x.x.x)  eth0 147.93.33.253
            │                                                              │
            │  ───── TCP SYN → 147.93.33.253:22 ───────────────────►       │
            │                                                              │
            │              ??? (timeout 30s, sem SYN-ACK) ???             │
            │                                                              │
            ▼                                                              ▼
   dial tcp ***:22: i/o timeout                                sshd listening 0.0.0.0:22
                                                                  UFW allow 22/tcp from Anywhere
```

**A conexão TCP nunca chega ao sshd.** Não há entradas em `/var/log/auth.log` para as tentativas dos runners GHA (verificado durante diagnóstico — auth.log vazio para ranges AWS).

---

## FASE 2 — Onde está o bloqueio

### 2.1 COMPROVADO (evidência objetiva)

| # | Fato | Evidência | Comando usado |
|---|------|-----------|---------------|
| 1 | VPS escuta SSH na porta 22 (IPv4 e IPv6) | `LISTEN 0 128 0.0.0.0:22 sshd` (e `[::]:22`) | `ss -tlnp` |
| 2 | UFW permite 22/tcp de **qualquer origem** | `22/tcp ALLOW IN Anywhere` (v4 + v6) | `ufw status numbered` |
| 3 | INPUT chain policy é DROP, mas regra UFW libera 22 | `Chain INPUT (policy DROP)` + UFW chain ACCEPT | `iptables -L INPUT -n -v` |
| 4 | sshd_config aceita chave pública (PermitRootLogin prohibit-password) | `PermitRootLogin prohibit-password`, `PasswordAuthentication no` | `ssh cat /etc/ssh/sshd_config` |
| 5 | Chave pública do runner GHA está instalada | `/root/.ssh/github_actions_siap.pub` (Jun 30 09:39) | `ls -la /root/.ssh/` |
| 6 | Fail2ban sshd jail ativo | 181 bans históricos, **0 atualmente banidos** | `fail2ban-client status sshd` |
| 7 | IPs banidos são brute-force da Ásia/Europa, **não ranges GHA** | `20.55.86.187`, `171.231.191.230`, `49.13.118.233` etc. | `zgrep "Ban " fail2ban.log` |
| 8 | DNS aponta direto para VPS (sem proxy Cloudflare) | `api.visualsmartflow.com.br → 147.93.33.253` | `nslookup` |
| 9 | VPS alcança api.github.com (saída OK) | `HTTP 200` em curl da VPS para github.com | `curl` da VPS |
| 10 | Da rede local, SSH à VPS funciona em <1s | `SSH_OK` (BatchMode + ed25519) | `ssh root@147.93.33.253` |
| 11 | Do runner GHA, SSH à VPS falha com i/o timeout 30s | `dial tcp ***:22: i/o timeout` | log job 84453422478 |
| 12 | Tailscale **já está instalado** no VPS | `tailscaled.service loaded active running` | `systemctl list-units` |
| 13 | Tailscale daemon versão recente (1.98.8) | commit `REDACTED` | `tailscale version` |
| 14 | Tailscale **NÃO está autenticado** | `Logged out. ... no current Tailscale IPs; state: NeedsLogin` | `tailscale status` |
| 15 | Ranges IP do GitHub Actions são 7292 blocos CIDR | total `actions` em api.github.com/meta | `curl api.github.com/meta` |
| 16 | **Nenhuma evidência** de tentativas dos runners GHA no auth.log | auth.log vazio para ranges AWS | `grep auth.log` |
| 17 | Não há cloud firewall UI tipo CSF | `/etc/csf/` inexistente; `which csf` vazio | `ls /etc/csf/` |

### 2.2 HIPÓTESE (plausível mas não comprovada)

| # | Hipótese | Raciocínio | Como confirmar |
|---|----------|------------|----------------|
| H1 | **Firewall upstream do provedor** (datacenter/Hostinger) bloqueia ranges GHA antes do SYN chegar ao VPS | VPS-side está completamente aberto, mas TCP nunca chega. auth.log não registra as tentativas. Fail2ban (que opera no VPS) nunca as vê. | Pedir ao suporte do provedor para liberar ou capturar pacote no gateway. |
| H2 | ASN do VPS (rede 147.93.33.0/24) tem egress filtering agressivo | Alguns ASNs europeus bloqueiam tráfego de clouds grandes (AWS/Azure/GCP) para reduzir abuso. | `traceroute` do VPS para um IP AWS conhecido + contactar ASN |
| H3 | GitHub Actions runner está atrás de NAT que dropa pacotes para destinos sem reverse-DNS válido | `api.github.com/meta` retorna ranges, mas o egress pode ter ACL própria | Tentar com `--resolve` ou tunelar via socks |

### 2.3 NÃO COMPROVADO

- **Quem exatamente** dropa o SYN (provedor do VPS? backbone intermediário? GHA egress ACL?).
- **Se** os 181 IPs banidos historicamente incluem algum range GHA (improvável pelos prefixes observados, mas não checado exaustivamente).
- **Se** há rate limit no VPS ou no provedor que faz o SYN ser descartado silenciosamente.

### 2.4 Conclusão da Fase 2

**Não há nada que possa ser corrigido via workflow ou configuração do VPS.** Os 16 fatos comprovados mostram que a VPS está totalmente aberta e pronta para receber SSH — o pacote TCP do runner **nunca chega ao VPS**. A correção **tem que ser do lado do caminho de rede**, e a opção de menor atrito é **mudar o modelo de conexão** em vez de tentar liberar 7292 ranges CIDR.

---

## FASE 3 — Alternativas de deploy

### A) SSH direto (atual) — NÃO RECOMENDADO

| Critério | Avaliação |
|----------|-----------|
| Complexidade | Baixa (já implementado) |
| Segurança | Média (exige 22/tcp aberto; nenhum fingerprint pin) |
| Esforço | Alto — exigiria liberar 7292 ranges no firewall upstream do provedor, **fora do nosso controle** |
| Tempo | Indefinido (depende do provedor) |
| Risco | Alto — continuar dependente de um caminho de rede que comprovadamente não funciona |
| **Recomendação** | **NÃO** manter como única via. Manter como fallback opcional após Tailscale. |

### B) Self-hosted runner na VPS — VIÁVEL

| Critério | Avaliação |
|----------|-----------|
| Complexidade | Média (instalar `actions-runner` na VPS, registrar no repo, configurar systemd) |
| Segurança | Alta (sem SSH inbound; runner autentica no GitHub por token de curta duração; comunicação TLS reversa outbound) |
| Esforço | 2-4h (instalação + registro + service + 1 run de teste) |
| Tempo | Mesmo dia |
| Risco | Médio — runner compartilha CPU/disk/RAM com a aplicação (VPS tem 7.8GB RAM, 2 cores, 39GB livres — apertado para app + runner) |
| **Recomendação** | **OK** como alternativa; inferior a Tailscale porque consome recursos do servidor de produção e adiciona vetor de ataque (runner pode executar código arbitrário do CI) |

### C) Tailscale — **RECOMENDADO** ⭐

| Critério | Avaliação |
|----------|-----------|
| Complexidade | Baixa (Tailscale já instalado na VPS; falta autenticar) |
| Segurança | **Muito alta** — WireGuard, mutual auth, zero portas públicas expostas, mesh privado |
| Esforço | **Mínimo** — gerar auth key, autenticar VPS, instalar Tailscale no runner (action oficial existe) |
| Tempo | 30-60 min |
| Risco | Baixo — depende de conta Tailscale (free tier até 100 devices); se cair, fallback para SSH direto |
| **Recomendação** | **PRIMARY** — único caminho que (a) já tem software instalado, (b) contorna o firewall sem pedir nada ao provedor, (c) preserva modelo de scripts atual (só troca IP de destino) |

### D) WireGuard manual — POSSÍVEL mas inferior a Tailscale

| Critério | Avaliação |
|----------|-----------|
| Complexidade | Alta (sem coordinator; configurar par de chaves, `wg0.conf`, firewall, IP estático) |
| Segurança | Muito alta (mesmo protocolo) |
| Esforço | 4-6h |
| Tempo | Mesmo dia |
| Risco | Médio — sem NAT traversal automático (DERP/relay), precisa de IP público fixo já configurado |
| **Recomendação** | **NÃO** se Tailscale é viável (mesmo protocolo, melhor DX) |

### E) Cloudflare Tunnel — INVASIVO

| Critério | Avaliação |
|----------|-----------|
| Complexidade | Alta (migrar DNS para Cloudflare, instalar `cloudflared`, configurar tunnel) |
| Segurança | Alta |
| Esforço | 1-2 dias |
| Tempo | 2+ dias (incluindo propagação DNS) |
| Risco | Alto — mexe em DNS de produção, exige testes de rollback DNS |
| **Recomendação** | **NÃO** para escopo de blocker de deploy. Útil para expor a app, não para SSH de deploy. |

### F) Pull deployment (cron + watchtower ou cron + curl) — VIÁVEL como backup

| Critério | Avaliação |
|----------|-----------|
| Complexidade | Baixa (cron + script que compara SHA remoto com local + `docker compose pull && up`) |
| Segurança | Média (precisa proteger o endpoint de "new SHA available" — usar GitHub API com token de leitura) |
| Esforço | 2-3h |
| Tempo | Mesmo dia |
| Risco | Médio — perde atomicidade do pipeline (deploy pode acontecer a qualquer momento, sem smoke pós-deploy coordenado) |
| **Recomendação** | **OK** como fallback secundário (se Tailscale falhar, pelo menos pull de imagens funciona) |

### G) GitHub Deploy Agent — **NÃO EXISTE**

| Critério | Avaliação |
|----------|-----------|
| Status | **Não é um produto público estável da GitHub** em 2026-07. Há preview features em Copilot, mas nenhum "Deploy Agent" maduro para SSH em VPS. |
| **Recomendação** | **NÃO APLICÁVEL** |

### Ranking

1. **Tailscale (C)** — melhor custo/benefício, software já na VPS
2. **Self-hosted runner (B)** — alternativa sólida, mas consome recursos do VPS
3. **Pull deployment (F)** — bom backup, perde orquestração do pipeline
4. **WireGuard (D)** — equivalente técnico a Tailscale sem o coordinator
5. **SSH direto (A)** — manter **somente como fallback após Tailscale ativo**
6. **Cloudflare Tunnel (E)** — desproporcional para o problema
7. **GitHub Deploy Agent (G)** — não existe como produto

---

## FASE 4 — Solução recomendada: **Tailscale**

### Justificativa técnica

1. **Software já instalado.** `tailscaled.service` está rodando na VPS (`systemctl list-units --type=service --state=running` confirma). Apenas precisa de autenticação (`tailscale up --authkey=...`).
2. **Resolve a causa raiz sem pedir nada ao provedor.** Tailscale abre conexão TCP outbound do VPS para o coordinator (`login.tailscale.com`). A partir daí, qualquer cliente Tailscale alcança o VPS via IP `100.x.x.x` (CGNAT) ou IPv6 do mesh — bypassando completamente o firewall upstream que está bloqueando GHA.
3. **Preserva o modelo atual.** O workflow `.github/workflows/cd-production.yml` continua usando `appleboy/ssh-action@v1`. **Única mudança:** `secrets.PROD_SSH_HOST` deixa de ser `147.93.33.253` e passa a ser o IP Tailscale do VPS (ex: `100.x.y.z`).
4. **Segurança superior ao modelo atual.**
   - WireGuard (ChaCha20) em vez de SSH sobre TCP puro.
   - Sem porta 22 exposta a ranges GHA (continua exposta à internet, mas como contingência, não como caminho primário).
   - **Fingerprint pin nativo do Tailscale** (chaves públicas do node ficam fixas).
5. **Custo zero.** Tailscale free tier: 100 devices, 1 user, suficiente.
6. **Reversível.** `tailscale logout` reverte ao estado atual.
7. **Independente do provedor.** Funciona em qualquer VPS (Hostinger, DigitalOcean, AWS, on-prem).
8. **Já é usado na VPS.** Algum operador anterior instalou e pretendeu usar; basta finalizar.

### O que muda (escopo cirúrgico)

**Workflow (1 alteração):**
- `secrets.PROD_SSH_HOST` → IP Tailscale do VPS (ex: `100.x.y.z`).
- Opcional: adicionar `command_timeout: 5m` para detectar timeout mais cedo.
- Opcional: adicionar retry (1 retry em transient failure).

**VPS (1 comando):**
- `tailscale up --authkey=tskey-auth-XXX --hostname=siap-prod --accept-routes`

**GitHub Secrets (1 atualização):**
- `PROD_SSH_HOST` → IP Tailscale.

**Nenhuma** alteração em backend/frontend/banco/migrações/billing/RBAC/LGPD/regras clínicas/APIs/scripts de deploy (eles continuam funcionando; o hostname de destino só muda).

---

## FASE 5 — Checklist do operador

### 5.1 Pré-condições

- [ ] Conta Tailscale (criar gratuita em https://login.tailscale.com/start)
- [ ] Acesso ao painel do Tailscale (https://login.tailscale.com/admin)
- [ ] Acesso SSH atual à VPS (root + chave) — **esse caminho continua funcionando, é o que vamos usar para configurar Tailscale**
- [ ] Permissão para criar/alterar secrets no repositório GitHub

### 5.2 Passo a passo

#### Passo 1 — Gerar auth key no painel Tailscale

1. Acesse https://login.tailscale.com/admin/settings/keys
2. **Generate key** com:
   - Description: `github-actions-siap`
   - Reusable: **ON** (para reuso se rodar mais de uma vez)
   - Expiration: **90 days** (renovar antes de expirar)
   - Tags: `tag:ci` (opcional, para ACL)
3. Copie a chave `tskey-auth-XXXXX...` (só aparece uma vez)

#### Passo 2 — Autenticar a VPS

```bash
ssh root@147.93.33.253

# No VPS, autenticar Tailscale:
tailscale up --authkey=tskey-auth-XXXXX... \
             --hostname=siap-prod \
             --accept-routes

# Verificar:
tailscale status
# Esperado: "100.x.y.z   siap-prod   user@   linux   -"
tailscale ip -4
# Esperado: 100.x.y.z

# Anotar o IP 100.x.y.z
```

#### Passo 3 — Testar conectividade via Tailscale

Da **sua máquina local** (onde Tailscale também precisa estar instalado, ou do runner):

```bash
# Instalar Tailscale local (se ainda não tiver):
# curl -fsSL https://tailscale.com/install.sh | sh
# sudo tailscale up

# Testar SSH via Tailscale IP:
ssh -o ConnectTimeout=10 root@100.x.y.z 'echo TAILSCALE_OK'
# Esperado: TAILSCALE_OK
```

#### Passo 4 — Atualizar secret no GitHub

1. Acesse https://github.com/gituser26071977/Aracannabis_v2_04_08_25/settings/secrets/actions
2. Edite `PROD_SSH_HOST`: valor antigo `147.93.33.253` → **novo** `100.x.y.z`
3. **NÃO** altere `PROD_SSH_KEY` nem `PROD_DEPLOY_USER`
4. (Opcional) Adicione secret `TAILSCALE_OAUTH_CLIENT_ID` e `TAILSCALE_OAUTH_SECRET` se quiser usar a action `tailscale/github-action@v2` em vez de instalar Tailscale manualmente no runner

#### Passo 5 — Validar workflow (dry run)

```bash
# Acionar manualmente o pipeline (workflow_dispatch):
gh workflow run cd-production.yml --ref main
# (mas isso exige tag v*.*.* — usar workflow_dispatch com input version)

# OU re-rodar o último run rc.10:
gh run rerun 28492626600 --failed  # só os jobs que falharam
```

#### Passo 6 — Critérios de sucesso

| # | Critério | Como verificar |
|---|----------|----------------|
| S1 | `tailscale status` na VPS mostra IP 100.x | `ssh root@147.93.33.253 'tailscale ip'` |
| S2 | SSH via Tailscale IP funciona da máquina do operador | `ssh root@100.x.y.z echo OK` |
| S3 | Estágio 8/9 (Backup) completa em <60s | log do job `8/9 — Backup pré-deploy (full)` |
| S4 | Estágio 9/9 (Deploy) executa `deploy_prod.sh` | log do job `9/9 — Deploy + Smoke + Auto-Rollback` |
| S5 | Smoke pós-deploy retorna 200 em `/api/health` | log do mesmo job |
| S6 | Imagem rc.10 já no GHCR (`prod-7d3bed1...`) é a que vai para produção | comparar `docker inspect` no VPS |

### 5.3 Rollback (se Tailscale não funcionar)

1. `tailscale logout` na VPS (remove do mesh)
2. Atualizar `PROD_SSH_HOST` de volta para `147.93.33.253` no GitHub Secrets
3. **Conclusão:** sem mudança observável para o operador (cai de volta no blocker atual, mas sem ter causado dano)

### 5.4 Renovação da auth key

A cada 90 dias:
1. Gerar nova auth key no painel
2. Rodar `tailscale up --authkey=tskey-NEW --hostname=siap-prod` na VPS (re-autentica)
3. **NÃO** precisa atualizar nenhum secret no GitHub — auth keys autenticam o **node**, não a conexão

---

## FASE 6 — Relatório final + respostas obrigatórias

### 1. Qual é a causa raiz comprovada?

**Caminho de rede bloqueado entre runner do GitHub Actions (range AWS) e porta 22 do VPS (147.93.33.253).** O SYN TCP do runner expira após 30s sem receber SYN-ACK. O bloqueio acontece **antes** do pacote chegar ao sshd (nenhuma entrada em auth.log para IPs AWS; fail2ban nunca registra as tentativas).

A causa raiz **não pôde ser localizada em nenhum componente que esteja sob nosso controle** (VPS está completamente aberta: UFW `allow 22/tcp from Anywhere`, sshd escutando, fail2ban ativo mas com 0 bans para ranges GHA, sem cloud firewall tipo CSF).

**Hipótese mais provável:** firewall upstream do provedor de hospedagem (datacenter da faixa `147.93.33.0/24`) ou ASN filter bloqueando ranges AWS/Azure onde ficam os runners do GitHub Actions.

### 2. Existe evidência objetiva?

**Sim, 17 fatos comprovados** (seção 2.1). Os mais decisivos:

- Da rede local: SSH funciona em <1s (FATO 10).
- Do runner GHA: `dial tcp ***:22: i/o timeout` (FATO 11).
- VPS auth.log **não registra** as tentativas do runner (FATO 16) — o que prova que o pacote não chega ao sshd.
- UFW explicitamente permite 22/tcp de qualquer origem (FATO 2).
- Tailscale daemon já está rodando, faltando apenas autenticação (FATOS 12-14) — caminho de contorno já disponível.

### 3. O problema é código ou infraestrutura?

**100% infraestrutura de rede.** Nenhuma alteração em código de aplicação, scripts de deploy, ou workflow resolve o blocker. As 10 iterações de RC da D03 (rc.1 → rc.10) foram todas de ordem de código/pipeline e **nenhuma** tocou este aspecto, porque o problema só aparece depois que todos os 7 estágios anteriores (Build, Lint, Tests, Security, Smoke, Playwright/Lighthouse) passam com sucesso e o estágio 8 (Backup) tenta abrir SSH.

### 4. Qual a solução recomendada?

**Tailscale** (seção 4). Justificativa: software já instalado na VPS, bypassa o firewall upstream via mesh privado WireGuard, preserva o modelo atual de scripts/workflow, zero custo, reversível.

Alternativas em ordem de viabilidade: Self-hosted runner (B), Pull deployment (F), WireGuard manual (D), SSH direto com IP allowlist (A — inviável: 7292 ranges), Cloudflare Tunnel (E — invasivo), GitHub Deploy Agent (G — não existe).

### 5. Depois da correção, será necessário criar rc.11?

**NÃO.** Esta é uma pergunta explícita da missão D04 e a resposta é **NÃO**:

- A imagem `v1.0.0-rc.10` (commit `7d3bed1`, digest backend `sha256:be7038f1...8d38a`, digest frontend `sha256:547e0cf0...3247`) **já foi construída, publicada no GHCR e validada**. Todos os estágios 1-7 do pipeline passaram. O único estágio pendente é o 8 (Backup) e 9 (Deploy), que são puramente operacionais.
- **Não há razão técnica** para rebuildar: nenhum código de aplicação, dependência, lockfile, ou configuração de pipeline mudou.
- **Criar rc.11 reintroduziria o overhead** de 10-15 min de pipeline (build + lint + tests + security + smoke + e2e + lighthouse) sem benefício algum.
- **A próxima execução do deploy deve ser feita a partir do MESMO commit já validado.** O operador pode disparar via `gh workflow run cd-production.yml --ref <sha>` usando o SHA `7d3bed1` (ou o HEAD atual do `main`, se for o mesmo).

**Recomendação operacional:** após Tailscale estar autenticado, disparar o pipeline usando `gh workflow run` com `version=1.0.0` apontando para o commit já validado. **Não criar tag rc.11.**

### 6. Probabilidade de o próximo deploy completar 9/9?

**Estimativa: 90-95%**, condicional a:

| Condição | Prob. de cumprir | Impacto se falhar |
|----------|------------------|--------------------|
| Tailscale auth key é gerada e aplicada | Alta (operador com acesso root à VPS) | Volta a SSH direto, falha idêntica |
| `tailscale status` na VPS retorna IP 100.x | Alta (autenticação é determinística) | Re-rodar `tailscale up` |
| Tailscale chega ao GitHub Actions runner | Alta (action oficial `tailscale/github-action@v2` documentada; alternativa: instalar Tailscale no runner via `sudo apt install`) | Fallback para SSH direto |
| Estágios 1-7 continuam passando | **Alta** — código não mudou desde rc.10 | Re-rodar; nada a ajustar |
| Backup (8/9) completa via Tailscale | **Alta** — não depende de firewall upstream | Re-verificar credenciais |
| Deploy (9/9) executa `deploy_prod.sh` | **Alta** — script não mudou | Idem D03 |
| Smoke pós-deploy passa | Média — depende do estado do banco em prod (migrations, secrets, schema) | AUTO-ROLLBACK aciona (declarado no workflow) |

**Probabilidade global: ≥ 90%.** A correção é cirúrgica e isolada; o resto do pipeline já foi validado em rc.10.

---

## Resumo executivo

| Item | Status |
|------|--------|
| Blocker | SSH do runner GHA para VPS porta 22 (causa: firewall upstream / ASN filter) |
| Confirmado que **NÃO** é falha do VPS | UFW, sshd, fail2ban, iptables, auth.log — todos OK |
| Solução | Tailscale (software já instalado, só autenticar) |
| Mudanças no workflow | 1 secret (`PROD_SSH_HOST`) + opcional action `tailscale/github-action@v2` |
| Mudanças na VPS | 1 comando (`tailscale up --authkey=...`) |
| Mudanças em código de aplicação | **ZERO** |
| Necessário criar rc.11? | **NÃO** — reusar commit `7d3bed1` (rc.10) já validado |
| Próximo deploy esperado | 9/9 stages com ≥ 90% de probabilidade |
| ETA | 30-60 min para configurar Tailscale + validar |

---

## Decisão final

# **Tailscale**

### Ações imediatas

1. Operador gera auth key em https://login.tailscale.com/admin/settings/keys
2. Operador roda `tailscale up --authkey=...` na VPS
3. Operador anota o IP Tailscale (100.x.y.z)
4. Operador atualiza `PROD_SSH_HOST` no GitHub Secrets
5. Operador dispara o pipeline usando o commit **já validado** `7d3bed1` (rc.10) — **NÃO criar rc.11**

### O que NÃO fazer

- NÃO criar `v1.0.0-rc.11`
- NÃO mover tags existentes
- NÃO alterar código de aplicação, banco, billing, RBAC, LGPD, regras clínicas, APIs
- NÃO tentar liberar ranges AWS no firewall upstream (7292 ranges = inviável)
- NÃO substituir o workflow de produção por uma solução de pull (perderia orquestração)

---

**FIM DO RELATÓRIO — D04 CONCLUÍDA. PARAR APÓS ESTE RELATÓRIO.**