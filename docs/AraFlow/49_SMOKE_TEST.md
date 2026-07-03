# AraFlow RC1.1 — Smoke Test

**Versão:** 1.0.0
**Data:** 2026-07-03
**Audiência:** operador validando o primeiro deploy público.

> **Modo de uso:** rode cada item em ordem. Marque ✅/❌. Se ❌, anote o output exato e vá para `49_DEPLOY_RUNBOOK.md` §5 (rollback).
>
> **Pré-requisito:** deploy concluído conforme `49_DEPLOY_RUNBOOK.md` passos 1-13.

---

## Legenda

| Símbolo | Significado |
|---|---|
| ✅ | Comportamento esperado observado |
| ❌ | Comportamento divergente — **PARAR** e investigar |
| ⚠️ | Aceitável mas merece nota (ex: latência alta) |

---

## 1. Infraestrutura & TLS

### 1.1 — Página raiz carrega (HTTPS)

**Comando:**
```bash
curl -fsSI https://flow.arapath.com.br/
```

**Esperado:**
```
HTTP/2 200
content-type: text/html
strict-transport-security: max-age=63072000
x-frame-options: DENY
x-content-type-options: nosniff
content-security-policy: default-src 'self'; ...
cache-control: no-cache
```

**Como validar manualmente:** abrir `https://flow.arapath.com.br/` em janela anônima — HTML renderiza.

---

### 1.2 — HTTP redireciona para HTTPS

**Comando:**
```bash
curl -fsSI http://flow.arapath.com.br/
```

**Esperado:**
```
HTTP/1.1 301 Moved Permanently
location: https://flow.arapath.com.br/
```

---

### 1.3 — /health retorna JSON válido

**Comando:**
```bash
curl -fsS https://flow.arapath.com.br/health | python3 -m json.tool
```

**Esperado:**
```json
{
    "status": "ok",
    "version": "1.0.0",
    "commit": "abc12345...",
    "build": "2026-07-03T...",
    "uptime": 42.123
}
```

**Validações:**
- [ ] `status == "ok"`
- [ ] `version == "1.0.0"`
- [ ] `commit` não é `"unknown"` (deve ser o SHA da CI)
- [ ] `build` é ISO-8601 UTC
- [ ] `uptime` numérico e > 0

---

## 2. Assets & bundle

### 2.1 — Bundle JS principal baixa

**Comando:**
```bash
# Descobrir nome real do asset do index.html
ASSET=$(curl -fsS https://flow.arapath.com.br/ \
  | grep -oE 'assets/main\.[a-f0-9]+\.js' \
  | head -1)
echo "Asset: $ASSET"
curl -fsSI "https://flow.arapath.com.br/$ASSET" | head -3
```

**Esperado:**
```
HTTP/2 200
content-type: application/javascript
cache-control: public, immutable
```

**Validações:**
- [ ] `Content-Type: application/javascript`
- [ ] `Cache-Control: public, immutable`
- [ ] Tamanho do body: 200 KB – 1 MB (RNW bundle minified)

---

### 2.2 — Source map opcional baixa (se habilitado)

**Comando:**
```bash
curl -fsSI "https://flow.arapath.com.br/$ASSET.map" | head -1
```

**Esperado:** 200 (produção inclui source map) OU 404 (se stripped). Ambos OK.

---

### 2.3 — index.html serve fallback SPA

**Comando:**
```bash
curl -fsSI https://flow.arapath.com.br/qualquer-rota-inexistente
```

**Esperado:** `HTTP/2 200`, `content-type: text/html` (nginx `try_files` fallback).

---

## 3. Aplicação (browser manual)

> **Atenção:** este bloco requer interação humana. Use janela anônima para evitar cache.

### 3.1 — Tela de seleção de protocolo aparece

**Como validar:**
- [ ] Página carrega em < 3s.
- [ ] Logo AraFlow visível.
- [ ] 3 cards de protocolo visíveis: **Diaphragmatic**, **Box 4-4-4-4**, **Physiological Sigh**.

---

### 3.2 — Iniciar sessão (Diaphragmatic)

**Como validar:**
- [ ] Clicar em "Diaphragmatic" → tela de sessão carrega.
- [ ] Animação de respiração (círculo/anel) visível.
- [ ] Contador de tempo incrementando.
- [ ] Botões visíveis: **Pause**, **Stop**.

---

### 3.3 — Pause

**Como validar:**
- [ ] Clicar em **Pause** → animação para, contador congela.
- [ ] Botão muda para **Resume**.

---

### 3.4 — Resume

**Como validar:**
- [ ] Clicar em **Resume** → animação volta do ponto exato, contador continua.
- [ ] Não há reset de tempo.

---

### 3.5 — Stop (fim prematuro)

**Como validar:**
- [ ] Clicar em **Stop** → tela de feedback aparece.
- [ ] Campos de feedback (rating 1-5, comentário opcional) visíveis.

---

### 3.6 — Fim natural da sessão

**Como validar:**
- [ ] Aguardar protocolo completar (tempo varia: 2-5 min).
- [ ] Tela de feedback aparece automaticamente.

---

### 3.7 — Submeter feedback

**Como validar:**
- [ ] Preencher rating (1-5).
- [ ] (Opcional) Preencher comentário.
- [ ] Clicar em **Submit** → confirmação visual (toast/modal).
- [ ] Botão **Voltar** leva à seleção de protocolo.

---

### 3.8 — Feedback persiste (localStorage)

**Como validar:**
- [ ] Submeter feedback.
- [ ] Recarregar a página (F5).
- [ ] Navegar para qualquer rota que liste histórico (se houver).
- [ ] Feedback submetido ainda aparece.

> **Nota técnica:** o shim `async-storage.web.ts` persiste em `localStorage` com chave `araflow:feedback:*`. Para inspecionar via DevTools:
> ```js
> JSON.parse(localStorage.getItem('araflow:feedback:list') || '[]')
> ```

---

## 4. Logs e observabilidade

### 4.1 — Logs da API sem erros

**Comando (no VPS):**
```bash
docker logs --since 5m araflow-api 2>&1 | grep -iE "error|panic|fatal" || echo "✅ sem erros"
```

**Esperado:** "✅ sem erros".

---

### 4.2 — Logs do nginx sem 5xx

**Comando:**
```bash
docker logs --since 5m araflow-web 2>&1 | grep -E " [5][0-9][0-9] " || echo "✅ sem 5xx"
```

**Esperado:** "✅ sem 5xx".

> **Nota:** o nginx-unprivileged não loga por padrão (logs vão para stdout se `access_log off` estiver setado em algumas locations). O comando acima cobre o erro_log se habilitado.

---

### 4.3 — Traefik reconhece os 2 routers araflow

**Comando:**
```bash
# Encontrar container Traefik
TRAEFIK=$(docker ps -q -f name=traefik)
docker exec $TRAEFIK wget -qO- http://127.0.0.1:8082/api/http/routers 2>/dev/null \
  | python3 -c "
import json, sys
routers = json.load(sys.stdin)
araflow = [r for r in routers if r['name'].startswith('araflow-')]
for r in araflow:
    print(f\"  {r['name']:30s} status={r.get('status','?')} rule={r['rule']}\")
print(f'Total araflow routers: {len(araflow)}')
"
```

**Esperado:** 3 routers listados:
- `araflow-api-health@docker`
- `araflow-flow@docker`
- `araflow-flow-http@docker`

---

### 4.4 — Traefik reconhece os 2 services araflow

**Comando:**
```bash
TRAEFIK=$(docker ps -q -f name=traefik)
docker exec $TRAEFIK wget -qO- http://127.0.0.1:8082/api/http/services 2>/dev/null \
  | python3 -c "
import json, sys
services = json.load(sys.stdin)
araflow = [s for s in services if s['name'].startswith('araflow-')]
for s in araflow:
    print(f\"  {s['name']:30s} status={s.get('status','?')}\")
print(f'Total araflow services: {len(araflow)}')
"
```

**Esperado:** 2 services: `araflow-api@docker`, `araflow-flow@docker`, ambos `status=enabled`.

---

## 5. Recursos (memória, CPU, disco)

### 5.1 — Memória por container

**Comando (no VPS):**
```bash
docker stats --no-stream --format \
  "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}" \
  | grep -E "araflow-|siap-(backend|frontend)"
```

**Limites esperados:**

| Container | Memória esperada | ❌ Falha se |
|---|---|---|
| `araflow-api` | 30-80 MB | > 150 MB |
| `araflow-web` | 5-15 MB | > 30 MB |
| `siap-backend` (baseline) | (não muda) | > baseline + 10% |
| `siap-frontend` (baseline) | (não muda) | > baseline + 10% |

**Como validar:** AraOS não pode crescer mais que 10% após deploy AraFlow (princípio de não-impact).

---

### 5.2 — CPU em repouso

**Comando:**
```bash
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}" | grep -E "araflow-"
```

**Esperado:** ambos < 1% CPU em repouso (sem requests ativos).

---

### 5.3 — Disco das imagens

**Comando:**
```bash
docker images | grep -E "araflow-(api|web)\s+rc1"
```

**Esperado:**
```
araflow-api    rc1-latest    <id>    350-360 MB
araflow-web    rc1-latest    <id>    50-60 MB
```

---

## 6. AraOS não-impact (gate final)

### 6.1 — Containers AraOS inalterados

**Comando:**
```bash
docker ps --format '{{.Names}}\t{{.Status}}' \
  | grep -E "^(siap-backend|siap-frontend|siap-db|siap-redis|siap-anonymization)"
```

**Esperado:** mesmos uptimes de antes do deploy (Up 7+ days, etc.).

---

### 6.2 — API AraOS responde

**Comando:**
```bash
curl -fsS https://api.visualsmartflow.com.br/api/health -o /dev/null -w "%{http_code}\n"
```

**Esperado:** `200`.

---

### 6.3 — Frontend AraOS carrega

**Comando:**
```bash
curl -fsSI https://visualsmartflow.com.br/ | head -1
```

**Esperado:** `HTTP/2 200`.

---

## 7. Resumo do smoke test

| # | Item | Resultado |
|---|---|---|
| 1.1 | Página HTTPS | ☐ |
| 1.2 | HTTP→HTTPS redirect | ☐ |
| 1.3 | /health JSON | ☐ |
| 2.1 | Bundle JS | ☐ |
| 2.2 | Source map (opcional) | ☐ |
| 2.3 | SPA fallback | ☐ |
| 3.1 | Tela protocolos | ☐ |
| 3.2 | Iniciar sessão | ☐ |
| 3.3 | Pause | ☐ |
| 3.4 | Resume | ☐ |
| 3.5 | Stop | ☐ |
| 3.6 | Fim natural | ☐ |
| 3.7 | Submit feedback | ☐ |
| 3.8 | Feedback persiste | ☐ |
| 4.1 | API sem erros | ☐ |
| 4.2 | Nginx sem 5xx | ☐ |
| 4.3 | Traefik routers | ☐ |
| 4.4 | Traefik services | ☐ |
| 5.1 | Memória containers | ☐ |
| 5.2 | CPU em repouso | ☐ |
| 5.3 | Disco imagens | ☐ |
| 6.1 | AraOS inalterado | ☐ |
| 6.2 | AraOS /health | ☐ |
| 6.3 | AraOS frontend | ☐ |

**Total: 24 itens.**

---

## 8. Decisão

| Critério | Resultado | Ação |
|---|---|---|
| 24/24 ✅ | **PASS** | Anunciar RC1 live. |
| Qualquer 4.x ❌ (Traefik) | **FAIL** | Logs detalhados + rollback. |
| Qualquer 3.x ❌ (UX) | **FAIL** | Bloqueia anúncio; investigar bundle/session/feedback. |
| Qualquer 6.x ❌ (AraOS) | **CRITICAL FAIL** | **Rollback imediato** (`49_DEPLOY_RUNBOOK.md` §5.3). Investigar antes de re-tentar. |
| Qualquer 5.x ❌ (recursos) | **WARN** | Aceitável se próximo do limite. Re-rodar 5.1 em 5 min para confirmar tendência. |