# DEPLOY_RUNBOOK — MISSÃO 22

**Data:** 2026-06-25
**Modo:** EXECUTE
**Objetivo:** roteiro de comandos na ordem correta, do `git pull` à validação final

---

## Pré-requisitos

- Acesso SSH ao VPS de produção
- Acesso ao registry Docker (se houver)
- Acesso ao GitHub (para merge)
- `~/.ssh/id_rsa` cadastrado no VPS
- Vault de secrets acessível
- Janela de manutenção autorizada

---

## 1. Pré-deploy (D-7 a H-1)

```bash
# Validar P0 tests (arquivo específico, conforme deploy_prod.sh:25)
.venv-test/bin/python -m pytest tests/security/test_p0_remediation_m18.py -q

# Validar env
python3 scripts/validate_env.py

# Verificar árvore git limpa
git fetch && git status
```

> **Correção M22.2:** `deploy_prod.sh` (linha 25) roda **apenas** `tests/security/test_p0_remediation_m18.py`, não todo o diretório. Documentação alinhada.

## 2. Backup pré-deploy (H-2)

```bash
./scripts/backup.sh --env=production
```

**Critério OK:** arquivo em `/var/backups/siap/db_*.sql.gz` com tamanho > 0 e timestamp recente.

## 3. Checkout da tag (H-0)

```bash
git fetch --tags
git checkout v*.*.*    # ex: v1.2.3
```

## 4. Build das imagens

```bash
cd /opt/araos
docker-compose -f docker-compose.prod.yml --env-file .env.production build --pull
```

**Critério OK:** `Successfully built` para backend e frontend.

## 5. Aplicar migrações (se houver)

```bash
docker exec siap-backend flask db upgrade
```

> **Correção M22.2:** migrações usam **Flask-Migrate** (`app_cors_livre.py:82-83`), não Alembic standalone.
> Não há diretório `alembic/` no repo — diretório correto é `migrations/` com `alembic.ini` apenas como metadado.

**Critério OK:** sem erro; verificar tabela `alembic_version` (ou `migrations`) no banco.

## 6. Rolling restart do backend

```bash
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d --no-deps siap-backend
```

**Aguardar healthcheck:** `docker ps | grep siap-backend` → status `(healthy)`.

## 7. Smoke test do backend

```bash
./scripts/smoke.sh --env=production
```

**Critério OK:** 6 endpoints retornam 200/4xx esperado.

## 8. Restart do frontend

```bash
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d --no-deps siap-frontend
```

## 9. Smoke test do frontend

```bash
curl -sk -o /dev/null -w "%{http_code}" https://visualsmartflow.com.br/
```

**Critério OK:** 200.

## 10. Validar workers

```bash
docker exec siap-backend ps aux | grep gunicorn | wc -l
# Esperado: 4-6 (1 master + 3 workers + threads)
```

## 11. Validar Redis

```bash
docker exec siap-redis redis-cli ping
# Esperado: PONG
docker exec siap-redis redis-cli info clients | grep connected_clients
# Esperado: ≥1
```

## 12. Validar PostgreSQL

```bash
docker exec siap-db pg_isready -U siap_user -d aracannabis
docker exec siap-db psql -U siap_user -d aracannabis -c "SELECT 1;"
```

**Critério OK:** "accepting connections" e "1" como retorno.

## 13. Healthcheck endpoint

```bash
curl -sk https://api.visualsmartflow.com.br/api/health | jq .
```

**Critério OK:** `"status": "ok"`.

> **Correção M22.2:** em prod, conforme M21/M21.5, este endpoint **NÃO está deployado** (curl retorna 404). É BLOQUEADOR #4 documentado em `DEPLOY_BLOCKERS.md`. Operador **NÃO deve considerar 404 como falha** — está documentado como estado conhecido.

## 14. Validação de tenant isolation (smoke)

```bash
# Login usuário de teste (tester.modulos@araos.dev criado em seeds)
TOKEN_A=$(curl -sk -X POST https://api.visualsmartflow.com.br/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"tester.modulos@araos.dev","password":"Tester@2025"}' | jq -r .access_token)

# Listar pacientes
curl -sk https://api.visualsmartflow.com.br/api/pacientes \
  -H "Authorization: Bearer $TOKEN_A" | jq '.[] | .associacao_id' | sort -u

# Esperado: 1 único associacao_id
```

> **Correção M22.2:** usuário de teste confirmado é `tester.modulos@araos.dev` (não `medico.a@araos.dev`).
> Credenciais documentadas em `tests/load/locustfile.py:34-36` e `tests/e2e/test_01_login.py:7`.

## 15. Validação de webhook

```bash
# Disparar webhook de teste (somente se ALLOW_WEBHOOK_SIMULATION=1)
curl -sk -X POST https://api.visualsmartflow.com.br/api/mercadopago/webhook \
  -H "Content-Type: application/json" \
  -d '{"type":"payment","data":{"id":"test_deploy_001"}}'
```

**Critério OK:** resposta 200 ou 4xx (nunca 500).

## 16. Métricas de saúde (H+15)

```bash
./scripts/healthcheck.sh --env=production
```

**Critério OK:** todos os checks `ok`.

## 17. Comunicação final

```bash
# Slack
echo ":white_check_mark: Deploy $(git describe --tags) em produção OK" | \
  curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"$(cat -)\"}" \
  $SLACK_WEBHOOK_URL
```

---

## Rollback completo (se algum passo falhar)

```bash
./scripts/rollback.sh --env=production
```

Restaura o backup mais recente pré-deploy e reinicia serviços.

---

## Pós-deploy (D+1, D+7)

```bash
# D+1
./scripts/healthcheck.sh --env=production
./scripts/backup.sh --env=production

# D+7
./scripts/healthcheck.sh --env=production
ls -lt /var/backups/siap/ | head -7   # 7 backups
```
