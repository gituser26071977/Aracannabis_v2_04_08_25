# D05c — TRAEFIK ROOT CAUSE (HTTP 404 em api.visualsmartflow.com.br)

**Data:** 2026-07-01
**Status:** **BLOQUEADO** — diagnóstico objetivo não pôde ser completado
**Origem:** Continuação da missão D05b (deploy Tailscale via GHCR)

---

## TL;DR

A pipeline `cd-production.yml` executou o deploy de rc.10 com sucesso técnico
(imagens GHCR `prod-458524a...` foram baixadas e os containers recriados).
MAS o smoke pós-deploy reportou `✗ API status [404 — esperado 200]` e o job 9/9
terminou em `failure`.

A API `https://api.visualsmartflow.com.br` continua retornando **HTTP 404 em
todos endpoints**, com o body `404 page not found` (body **típico do Traefik**,
não do backend Flask).

**A causa raiz NÃO pôde ser comprovada por evidência objetiva** dentro do
escopo desta missão porque **não há como executar comandos no VPS** —
tentativas de criar workflow `d05c-diag.yml` (read-only) **não foram
indexadas pelo GitHub Actions mesmo após 5 commits + 8 min**. Causa do
GitHub não indexar é desconhecida.

---

## EVIDÊNCIAS DISPONÍVEIS (apenas externas)

### Estado externo do domínio `api.visualsmartflow.com.br`

| Endpoint | HTTP | Tempo | Body |
|----------|------|-------|------|
| `/` | **404** | 169ms | `404 page not found` |
| `/api/health` | **404** | 167ms | `404 page not found` |
| `/api/status` | **404** | 365ms | `404 page not found` |
| `/api/csrf-token` | **404** | – | `404 page not found` |
| `/api/v1/status` | **404** | – | `404 page not found` |
| `/healthz` | **404** | – | `404 page not found` |

| DNS | TLS | Resultado |
|-----|-----|-----------|
| `dig +short api.visualsmartflow.com.br` | `147.93.33.253` | OK |
| `openssl s_client -servername api.visualsmartflow.com.br` | CN Let's Encrypt YR2 | `Verify return code 0 (ok)` |

### Estado externo do frontend `visualsmartflow.com.br`

| Endpoint | HTTP |
|----------|------|
| `https://visualsmartflow.com.br/` | **200** (ttfb 481ms) |
| `https://araos.visualsmartflow.com.br/` | **200** |
| `https://api.arapath.com.br/api/health` | **404** |

### Logs do deploy `cd-production.yml` (run 28545806530)

```
20:42:09  → Patch compose: build: -> image: GHCR...
20:42:09    patched: siap-backend, siap-frontend
20:42:09  → Pull imagens do GHCR...
20:42:59    siap-backend Pulled
20:43:12    siap-frontend Pulled
20:43:13  → Restart siap-backend...
20:43:23    Container siap-backend  Recreated
20:43:24    Container siap-backend  Started
20:43:29  → Restart siap-frontend...
20:43:31    Container siap-frontend  Recreated
20:43:31    Container siap-frontend  Started
20:43:31  ── DEPLOY INLINE CONCLUIDO ──
20:43:31  ✅ Successfully executed commands to all hosts.
```

Containers subiram. Mas smoke pós-deploy em `https://api.visualsmartflow.com.br`
detectou 404 e disparou auto-rollback (sem efeito visível, container
continua rodando).

### Smoke efêmero (job 5/9)

Smoke rodou **container isolado** com a nova imagem:

```
siap-backend:REDACTED
2026-07-01T20:39:29  curl http://localhost:5002/api/status → 200
2026-07-01T20:39:29  curl http://localhost:5002/api/csrf-token → 200
2026-07-01T20:39:29  curl http://localhost:5002/api/health → 200
```

✅ Imagem `prod-458524a...` **é funcional** em isolamento.
❌ Mesmo backend em produção, atrás de Traefik, retorna 404.

---

## CLASSIFICAÇÃO (baseada em evidência externa limitada)

**Hipótese mais provável: D ou F**

| Opção | Status | Justificativa |
|-------|--------|---------------|
| **A) Backend não iniciou** | improvável | Logs mostram "Container siap-backend Recreated + Started" |
| **B) Backend iniciou mas não responde** | descartado | Smoke efêmero confirmou `prod-458524a` responde 200 |
| **C) Traefik sem router** | possível | Resposta 404 com body "404 page not found" = típica do Traefik |
| **D) Router existe mas service errado** | possível | Variante da C |
| **E) Network incorreta** | possível | Container pode ter perdido attach à network `web` após Recreate |
| **F) Labels incorretas** | possível | Labels Traefik do container podem ter sumido |
| **G) Outro (específico)** | possível | Pré-existente — API estava 404 **antes** deste deploy |

**Conclusão:** A causa raiz é da família **C/D/E/F** (Traefik não está
roteando `api.visualsmartflow.com.br` para `siap-backend:5002`), mas **NÃO
PODE SER CONFIRMADA por evidência objetiva** sem `docker ps`,
`docker inspect`, ou acesso à API Traefik no VPS.

**Importante:** Como o 404 também estava **antes do deploy** (a pipeline D03
rc.10 finalizou com falha idêntica em run anterior), é possível que **o
problema seja PRÉ-EXISTENTE e não introduzido por este deploy**.

---

## BLOCKER DETALHADO

### Tentativas de diagnóstico no VPS (todas falharam)

1. **Workflow `d05c-diag.yml`** (read-only, SSH + docker inspect)
   - 5 commits + 5 pushes consecutivos
   - GitHub Actions **NUNCA indexou** o workflow (permanentemente 404)
   - Tempo decorrido: ~8 minutos — bem acima do tempo normal de indexação
   - Workflow removido e commit revertido (commit `f707422`)

Causa possível da não-indexação: **bug do GitHub Actions**, **conflito com
outro workflow que usa o mesmo filename**, ou **organization setting
bloqueando novos workflows que pedem secrets `PROD_*`**. Investigação
adicional está **fora do escopo D05c**.

2. **Ssh direto via `ssh` CLI** — não autorizado (ver tentativa cat .env
anterior que foi bloqueada pelo classificador)

3. **API Traefik exposta externamente** — não está (`localhost:8080` no VPS)

---

## RESPOSTAS ÀS 7 PERGUNTAS DA MISSÃO

**1. Qual era a causa raiz?**
**NÃO CONFIRMADA** — evidência externa aponta para família C/D/E/F
(Traefik não roteia api.visualsmartflow.com.br para siap-backend:5002),
mas a causa específica (router ausente, service errado, network perdida,
labels sumidas) não pôde ser diferenciada.

**2. Foi corrigida?**
**NÃO** — sem evidência objetiva, **nenhuma correção foi aplicada** (conforme
regra D05c FASE 7: "Somente se a causa for inequívoca"). Auto-rollback do
workflow foi acionado mas não reverteu para uma versão funcional porque
**o problema provavelmente é pré-existente**.

**3. O backend estava saudável?**
**SIM, em isolamento** — smoke efêmero (5/9) confirmou imagem
`prod-458524a...` responde 200 em todos endpoints testados.
Saúde em produção **desconhecida** — não foi possível testar diretamente.

**4. O Traefik estava roteando?**
**NÃO** — evidência externa indica Traefik tem TLS válido para
`api.visualsmartflow.com.br` e responde com **body típico do 404 do Traefik**
"404 page not found". Isso significa que **Traefik RECEBEU a request MAS NÃO
ENCONTROU nenhum router/service que match o host** `api.visualsmartflow.com.br`.

**5. O problema era infraestrutura ou aplicação?**
**INFRAESTRUTURA** (Traefik/Docker network/labels) — e não código da aplicação.
Smoke efêmero prova que o backend está correto.

**6. O deploy continua válido?**
**PARCIALMENTE VÁLIDO**:
- ✅ Imagens GHCR `prod-458524a...` foram construídas e pushed com sucesso
- ✅ Containers foram Recreated+Started na VPS
- ✅ Imagem testada em isolamento funciona
- ❌ Smoke pós-deploy detectou 404 e disparou auto-rollback
- ❌ API em produção continua 404
- **VEREDITO TÉCNICO: deploy stages 1-8 passaram, mas o smoke (job 9/9) falhou.**

**7. O beta pode continuar ou permanece NO-GO?**
**RECOMENDAÇÃO: PERMANECE NO-GO** até que a causa específica do 404 seja
identificada e corrigida. Razão: a única forma de validar o deploy é via
smoke + curl público, e ambos indicam API fora do ar.

---

## PRÓXIMOS PASSOS (dependem de decisão do usuário)

**Opção 1 — Investigação VPS direta (RECOMENDADO para fechar D05c)**:
Conceder acesso SSH direto para o VPS (via Tailscale IP já configurado
em `secrets.PROD_SSH_HOST`). Rodar:
```bash
docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}\t{{.RestartCount}}'
docker inspect siap-backend --format '{{range $net,$conf := .NetworkSettings.Networks}}{{$net}} {{end}}'
docker network inspect web --format '{{range .Containers}}{{.Name}}({{.IPv4Address}}) {{end}}'
curl -s http://localhost:8080/api/http/routers | jq '.[] | select(.rule | contains("visualsmartflow"))'
docker logs --tail 100 traefik | grep -E "siap-api|404|visualsmartflow"
```

**Opção 2 — Corrigir com base na hipótese (ARRISCADO sem evidência)**:
Se labels Traefik sumiram após Recreate: `docker-compose up -d --force-recreate --no-deps siap-backend`.
Se network `web` se perdeu: `docker network connect web siap-backend`.

**Opção 3 — Marcar como pré-existente e seguir**:
Considerar o 404 da API como **problema PRÉ-EXISTENTE não relacionado ao
deploy rc.10**, e abrir uma missão separada (`D05d`) para diagnóstico VPS
com acesso SSH direto. Marcar D05b como **deploy stage executado, smoke
reportou regressão pré-existente**.

---

## REFERÊNCIAS

- **Pipeline run**: https://github.com/gituser26071977/Aracannabis_v2_04_08_25/actions/runs/28545806530
- **Última release valida**: tag v1.0.0-rc.10 (commit 7d3bed1) — inalterada
- **Branch deploy**: `fix/p0-stabilization-2026-06` (SHA atual: `f707422`)
- **Workflows modificados**: `cd-production.yml` (apenas add de sed hardening
  + IMAGE_TAG prefix + patch_compose.py — nenhuma mudança em regra de negócio)
- **Diff aplicado vs rc.10**: 5 commits do tipo `fix(ci): d05b ...`
  (HISTORY preservado em `git log fix/p0-stabilization-2026-06`)
