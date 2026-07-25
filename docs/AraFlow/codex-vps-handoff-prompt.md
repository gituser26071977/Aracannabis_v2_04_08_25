## CONTEXTO — copie e cole no Codex do VPS

Você é um assistente operacional. Estamos no meio de um deploy de um produto novo (AraFlow RC1) no VPS `147.93.33.253` (hostname `aracannabis`, Tailscale `100.123.121.22`). Você está rodando direto no VPS via console Hostinger.

**O que é AraFlow:**
- App standalone de saúde mental baseado em respiração guiada (3 protocolos: Diaphragmatic, Box 4-4-4-4, Physiological Sigh).
- Stack: Fastify (Node 20) + nginx unprivileged + react-native-web bundle.
- Vai rodar em **subdomínio separado**: `https://flow.arapath.com.br` — **NÃO TOCA** nos containers AraOS existentes (`siap-backend`, `siap-frontend`, `siap-db`, `siap-redis`, `siap-anonymization`).
- Imagens Docker já estão publicadas em `ghcr.io/gituser26071977/araflow-api:rc1-latest` e `ghcr.io/gituser26071977/araflow-web:rc1-latest`.

**O que falta fazer NESTE VPS, em ordem:**
1. Confirmar que o DNS `flow.arapath.com.br` propaga (precisa resolver pro IP `147.93.33.253`)
2. Confirmar que os 2 packages GHCR estão com visibilidade `public` (essa parte NÃO depende de você — o operador está fazendo via UI do GitHub, mas se quiser validar, `curl -sIo /dev/null -w "%{http_code}\n" https://ghcr.io/v2/gituser26071977/araflow-api/manifests/rc1-latest` deve retornar **200**, não 401)
3. Subir os containers AraFlow via `docker compose -f docker-compose.araflow.yml --env-file .env.araflow up -d`
4. Confirmar que Traefik detectou os routers `araflow-*` (deve aparecer 3 routers: `araflow-api-health@docker`, `araflow-flow@docker`, `araflow-flow-http@docker`)
5. Rodar smoke test (24 itens) em `docs/AraFlow/49_SMOKE_TEST.md` se você tiver acesso, OU validar minimamente que `curl -H "Host: flow.arapath.com.br" http://127.0.0.1/health` retorna JSON com `status: ok`

**Estado atual conhecido:**
- ✅ ufw permite 22/80/443
- ✅ sshd ouvindo em 0.0.0.0:22
- ✅ Traefik rodando e respondendo em 80/443
- ✅ DNS `flow.arapath.com.br` criado no painel Hostinger, **MAS não propaga ainda** no resolver local do VPS (`dig +short flow.arapath.com.br A` retorna vazio)
- ✅ IPv4 do VPS: `147.93.33.253`, IPv6: `2a02:4780:14:2341::1`
- ⚠️ SSH porta 22 inacessível de fora (bloqueio externo da Hostinger — irrelevant aqui, você está no console)

**Recursos que você tem disponíveis:**
- `/root/.ssh/authorized_keys` com 8 chaves
- Diretório do projeto: precisa confirmar onde está. Pode ser `/root/Aracannabis_v2_04_08_25`, `/opt/araflow`, ou outro. Rode `pwd`, `ls`, `find / -name docker-compose.araflow.yml -not -path "*/node_modules/*" 2>/dev/null | head -5` pra localizar.
- Doc do runbook: `docs/AraFlow/49_DEPLOY_RUNBOOK.md` no repo (você pode `cat` se achar o repo)

---

## COMANDOS QUE EU PRECISO QUE VOCÊ RODE E COLE O OUTPUT

### BLOCO A — Diagnóstico DNS + rede

Cole e rode **cada bloco separadamente**, e cole o output completo de volta.

**A.1 — Onde está o código?**

```bash
pwd
echo "---"
ls -la /root/ 2>&1 | head -20
echo "---"
find / -name "docker-compose.araflow.yml" -not -path "*/node_modules/*" -not -path "*/proc/*" 2>/dev/null | head -5
echo "---"
find / -name ".env.araflow*" -not -path "*/proc/*" 2>/dev/null | head -5
echo "---"
find / -name "49_DEPLOY_RUNBOOK.md" -not -path "*/proc/*" 2>/dev/null | head -5
```

**A.2 — DNS propagação + simulação via Host header**

```bash
echo "=== DNS local (resolver do VPS) ==="
dig +short flow.arapath.com.br A 2>&1
echo ""
echo "=== DNS via Google (8.8.8.8) ==="
dig @8.8.8.8 +short flow.arapath.com.br A 2>&1
echo ""
echo "=== DNS via Cloudflare (1.1.1.1) ==="
dig @1.1.1.1 +short flow.arapath.com.br A 2>&1
echo ""
echo "=== Nameservers da zona arapath.com.br ==="
dig +short arapath.com.br NS 2>&1
echo ""
echo "=== SOA ==="
dig +short arapath.com.br SOA 2>&1
echo ""
echo "=== curl simulando Host header (sem DNS) ==="
curl -fsS --max-time 5 -H "Host: flow.arapath.com.br" \
  -o /tmp/health.json -w "HTTP: %{http_code}\n" \
  http://127.0.0.1/health 2>&1
echo "--- body se houve ---"
cat /tmp/health.json 2>/dev/null
echo ""
echo "=== curl via IP direto sem Host header (esperado 404) ==="
curl -sS --max-time 5 -o /dev/null -w "HTTP: %{http_code}\n" http://147.93.33.253/health 2>&1
echo ""
echo "=== Traefik routers existentes (sem AraFlow ainda) ==="
TRAEFIK=$(docker ps -q -f name=traefik 2>/dev/null | head -1)
echo "Traefik container: $TRAEFIK"
if [ -n "$TRAEFIK" ]; then
  docker exec "$TRAEFIK" wget -qO- http://127.0.0.1:8082/api/http/routers 2>/dev/null > /tmp/routers.json
  echo "Total routers: $(python3 -c 'import json; print(len(json.load(open("/tmp/routers.json"))))' 2>/dev/null || echo 'parse-failed')"
  echo ""
  echo "AraFlow routers:"
  python3 -c "
import json
rs = json.load(open('/tmp/routers.json'))
for r in rs:
    if 'araflow' in r.get('name','').lower():
        print(f\"  {r['name']:35s} status={r.get('status','?')}\")
print('(empty list above = AraFlow NOT deployed yet — expected)')
" 2>&1
fi
```

**A.3 — Containers AraOS (NÃO MEXER, mas confirmar que existem)**

```bash
docker ps --format '{{.Names}}\t{{.Status}}' | grep -E "^(siap-|traefik)" | head -20
```

### BLOCO B — Validação GHCR público

```bash
for pkg in araflow-api araflow-web; do
  echo "--- $pkg ---"
  HTTP=$(curl -sIo /dev/null -w "%{http_code}\n" "https://ghcr.io/v2/gituser26071977/$pkg/manifests/rc1-latest" 2>&1)
  echo "Anon pull manifest HTTP: $HTTP (esperado 200 = público, 401 = ainda privado, 404 = não existe)"
done
```

---

## APÓS EU TER SEUS OUTPUTS

Vou analisar e decidir:
- Se DNS propagou + GHCR público → você roda o **BLOCO C** (deploy)
- Se DNS ainda não propagou → espero + tento de novo
- Se GHCR ainda privado → falo pro operador fechar B3 via UI
- Se Traefik detecta `flow.arapath.com.br` routers sem DNS → DNS pode estar ok mas cache local

### BLOCO C — Deploy (SÓ RODE APÓS EU AUTORIZAR)

```bash
# 1. Ir pro diretório do projeto (ajuste o path conforme A.1)
cd /root/Aracannabis_v2_04_08_25 2>/dev/null || cd /opt/araflow 2>/dev/null || cd /path/you/found

# 2. Confirmar arquivos
ls -la docker-compose.araflow.yml .env.araflow 2>&1 | head -10
echo "---"
grep -E "^(FLOW_DOMAIN|GIT_COMMIT|BUILD_TIME|ARAFLOW_VERSION|IMAGE_TAG)=" .env.araflow

# 3. Pull das imagens
docker compose -f docker-compose.araflow.yml --env-file .env.araflow pull 2>&1 | tail -20

# 4. Subir
docker compose -f docker-compose.araflow.yml --env-file .env.araflow up -d 2>&1 | tail -20

# 5. Validar que subiram
docker ps --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' | grep araflow

# 6. Logs das APIs por 30s pra ver se há erro fatal
docker logs --tail 50 araflow-api 2>&1 | tail -30
echo "---"
docker logs --tail 50 araflow-web 2>&1 | tail -10

# 7. Confirmar Traefik detectou
sleep 5
TRAEFIK=$(docker ps -q -f name=traefik 2>/dev/null | head -1)
docker exec "$TRAEFIK" wget -qO- http://127.0.0.1:8082/api/http/routers 2>/dev/null > /tmp/routers.json
python3 -c "
import json
rs = json.load(open('/tmp/routers.json'))
araflow = [r for r in rs if 'araflow' in r.get('name','').lower()]
print(f'AraFlow routers: {len(araflow)}')
for r in araflow:
    print(f\"  {r['name']:35s} status={r.get('status','?')}\")
"
echo ""
echo "--- services ---"
docker exec "$TRAEFIK" wget -qO- http://127.0.0.1:8082/api/http/services 2>/dev/null > /tmp/services.json
python3 -c "
import json
ss = json.load(open('/tmp/services.json'))
araflow = [s for s in ss if 'araflow' in s.get('name','').lower()]
print(f'AraFlow services: {len(araflow)}')
for s in araflow:
    print(f\"  {s['name']:35s} status={s.get('status','?')}\")
"

# 8. Smoke test mínimo (3 calls chave)
echo ""
echo "=== /health direto no container ==="
docker exec araflow-api wget -qO- http://127.0.0.1:5005/health 2>&1
echo ""
echo "=== /health via Host header (porta 80 do Traefik) ==="
curl -fsS --max-time 5 -H "Host: flow.arapath.com.br" \
  -o /tmp/h.json -w "HTTP: %{http_code}\n" \
  http://127.0.0.1/health 2>&1
cat /tmp/h.json 2>/dev/null
echo ""
echo "=== /health via Host header (porta 443) ==="
curl -fsk --max-time 5 -H "Host: flow.arapath.com.br" \
  -o /tmp/h2.json -w "HTTP: %{http_code}\n" \
  https://127.0.0.1/health 2>&1
cat /tmp/h2.json 2>/dev/null
echo ""
echo "=== /health via DNS (se propagou) ==="
curl -fsS --max-time 5 https://flow.arapath.com.br/health 2>&1 | head -10
```

---

## COMO ME ENVIAR OS OUTPUTS

Cole cada output com um marcador tipo:

```
=== A.1 OUTPUT ===
<seu output aqui>
=== A.2 OUTPUT ===
<seu output aqui>
```

---

## REGRAS PRA VOCÊ (Codex)

- **NÃO modifique** nada do AraOS (`siap-*` containers, `docker-compose.prod.yml`, `/etc/nginx/`, `nginx_arapath_cf.conf` legado).
- **NÃO altere** DNS, Cloudflare, Traefik config global.
- Se algum comando falhar, cole o erro exato e PARE — me deixe decidir.
- Se `docker compose pull` reclamar de `manifest unknown` ou `requested access denied`, é porque B3 (GHCR público) ainda não fechou — me avise, NÃO tente login GHCR nem force.
- Se Traefik mostrar routers AraFlow com `status=error` ou `status=disabled`, cole a config completa e me mande.

---

**TL;DR pra você, Codex:** rode BLOCO A e BLOCO B, cole os outputs, **ESPERE** antes de rodar BLOCO C até eu autorizar.
