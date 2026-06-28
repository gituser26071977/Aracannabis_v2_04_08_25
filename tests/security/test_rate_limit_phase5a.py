"""
FASE 5A — Testes automatizados do rate limit (Redis + hybrid key + exempts).

Valida:
- TEST 1: storage_uri resolvido para Redis quando REDIS_URL definido
- TEST 2: login com limite 10/min — passa 10, falha no 11
- TEST 3: mudança de chave — chave baseada em JWT (profissional_id), não em IP
- TEST 4: rota com @limiter.exempt não é contabilizada
- TEST 5: Redis é compartilhado entre "workers" (storage_uri='redis://...')
- TEST 6: anonymous user usa IP como chave
- TEST 7: SENSITIVE_ENDPOINTS_RATE_LIMIT aplicado a POSTs críticos
- TEST 8: contador Redis é decrementado / expirado após janela
- TEST 9: isolamento entre profissionais (bucket separado)
- TEST 10: webhook funciona mesmo após login saturado

NÃO importa o app Flask inteiro. Usa Flask mínimo + limiter + decorators para
isolar a lógica de rate limit (sem dependência de DB / blueprints completos).

NOTA TÉCNICA: Flask-Limiter exige que decorators sejam aplicados DEPOIS de
init_limiter(app) — caso contrário `limiter` ainda é None no momento da decoração.
"""
import os
import sys

# Adicionar raiz do projeto ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Forçar uso de Redis local em db=13 (não conflita com nada)
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["RATE_LIMIT_REDIS_DB"] = "13"
# Limpar override se existir
os.environ.pop("RATELIMIT_STORAGE_URL", None)


from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

import security_config
from security_config import (
    init_limiter,
    get_hybrid_key,
    _resolve_storage_uri,
    LOGIN_RATE_LIMIT,
    SENSITIVE_ENDPOINTS_RATE_LIMIT,
)

# Limpar db Redis 13 antes dos testes
import redis as redis_lib
r = redis_lib.Redis(host="localhost", port=6379, db=13)
r.flushdb()


# ============================================================================
# App Flask mínimo + init_limiter (ANTES dos decorators)
# ============================================================================

app = Flask(__name__)
app.config["SECRET_KEY"] = "REDACTED"
app.config["JWT_SECRET_KEY"] = "REDACTED"

jwt = JWTManager(app)
limiter_instance = init_limiter(app)
# A partir de agora, security_config.limiter está inicializado


# ============================================================================
# Definir handlers como funções e aplicar decorators AGORA (após init_limiter)
# ============================================================================

def public_endpoint():
    """Endpoint público (sem auth) — usa IP como chave."""
    return jsonify({"key": get_hybrid_key(), "endpoint": "public"})


def protected_endpoint():
    """Endpoint autenticado — usa profissional_id como chave."""
    return jsonify({"key": get_hybrid_key(), "endpoint": "protected"})


def login_endpoint():
    """Simula /api/auth/login com LOGIN_RATE_LIMIT = 10/min."""
    return jsonify({"ok": True})


def sensitive_endpoint():
    """Simula POST sensível (cadastro_profissionais, change-password, etc)."""
    return jsonify({"ok": True})


def webhook_endpoint():
    """Simula webhook W1-W5 — isento de rate limit."""
    return jsonify({"ok": True, "webhook": True})


def issue_token():
    """Emite JWT para um profissional_id arbitrário (test helper)."""
    prof_id = request.json.get("prof_id", 1)
    token = create_access_token(identity=str(prof_id))
    return jsonify({"access_token": token})


# Aplicar decorators DEPOIS do init_limiter (limiter já está atribuído)
protected_endpoint = jwt_required()(protected_endpoint)
login_endpoint = limiter_instance.limit(LOGIN_RATE_LIMIT)(login_endpoint)
sensitive_endpoint = limiter_instance.limit(SENSITIVE_ENDPOINTS_RATE_LIMIT)(sensitive_endpoint)
# webhook_endpoint NÃO recebe limit() decorator — vamos testar @exempt
# (criamos wrapper exempt)

from security_config import limiter as limiter_global


@app.route("/test/public", methods=["GET"])
def route_public():
    return public_endpoint()


@app.route("/test/protected", methods=["GET"])
def route_protected():
    return protected_endpoint()


@app.route("/test/login", methods=["POST"])
def route_login():
    return login_endpoint()


@app.route("/test/sensitive", methods=["POST"])
def route_sensitive():
    return sensitive_endpoint()


@app.route("/test/webhook", methods=["POST"])
@limiter_global.exempt
def route_webhook():
    return webhook_endpoint()


@app.route("/test/issue-token", methods=["POST"])
def route_issue_token():
    return issue_token()


# ============================================================================
# Test runner
# ============================================================================

RESULTS = []


def record(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    icon = "PASS" if ok else "FAIL"
    print(f"  [{icon}] {name}: {detail}")


def reset_redis():
    """Limpa contadores Redis entre testes."""
    r.flushdb()


def get_token_for(prof_id):
    """Emite JWT para profissional_id (não requer DB, mock-only)."""
    with app.app_context():
        return create_access_token(identity=str(prof_id))


# ============================================================================
# TESTES
# ============================================================================

print("=" * 70)
print("FASE 5A — TESTES RATE LIMIT (Redis + hybrid key + exempts)")
print("=" * 70)


# ----- TEST 1: storage_uri resolution -----
print("\n[TEST 1] Storage URI resolvido para Redis")
storage = _resolve_storage_uri()
record(
    "storage_uri_redis",
    storage == "redis://localhost:6379/13",
    f"storage={storage} (expected redis://localhost:6379/13)",
)


# ----- TEST 2: LOGIN_RATE_LIMIT (10/min) -----
print("\n[TEST 2] LOGIN_RATE_LIMIT (10/min) — passa 10, bloqueia 11")
reset_redis()
client = app.test_client()
status_codes = []
for i in range(12):
    resp = client.post("/test/login", json={"x": i})
    status_codes.append(resp.status_code)

passed_count = sum(1 for s in status_codes if s == 200)
blocked_count = sum(1 for s in status_codes if s == 429)
ok = passed_count == 10 and blocked_count == 2
record(
    "login_10_per_minute",
    ok,
    f"passed={passed_count} blocked={blocked_count} (esperado: 10+2)",
)


# ----- TEST 3: Hybrid key — JWT profissional_id -----
print("\n[TEST 3] Hybrid key — JWT profissional_id (não IP)")
reset_redis()
client = app.test_client()

token_42 = get_token_for(42)
resp = client.get(
    "/test/protected",
    headers={"Authorization": f"Bearer {token_42}"},
)
body = resp.get_json() or {}
key_42 = body.get("key")
ok = key_42 == "prof:42"
record(
    "hybrid_key_jwt",
    ok,
    f"key para prof_id=42 = {key_42!r} (expected 'prof:42')",
)

token_99 = get_token_for(99)
resp = client.get(
    "/test/protected",
    headers={"Authorization": f"Bearer {token_99}"},
)
body = resp.get_json() or {}
key_99 = body.get("key")
ok = key_99 == "prof:99" and key_42 != key_99
record(
    "hybrid_key_isolates_professionals",
    ok,
    f"prof:42 != prof:99 → {key_42!r} != {key_99!r}",
)


# ----- TEST 4: Webhook exempt — não conta no rate limit -----
print("\n[TEST 4] Webhook @limiter.exempt não é contabilizado")
reset_redis()
client = app.test_client()

status_codes = []
for i in range(30):
    resp = client.post("/test/webhook", json={"x": i})
    status_codes.append(resp.status_code)

ok = all(s == 200 for s in status_codes)
record(
    "webhook_exempt",
    ok,
    f"30 webhooks, todos 200={all(s == 200 for s in status_codes)} (esperado: 30 × 200)",
)


# ----- TEST 5: Redis storage é compartilhado (chave aparece em Redis) -----
print("\n[TEST 5] Redis storage — chave de rate limit aparece em Redis")
reset_redis()
client = app.test_client()

# 1 POST em /test/login deve criar chave no Redis
client.post("/test/login", json={"x": 1})

# Verificar se há chaves do Flask-Limiter no Redis db=13
all_keys = r.keys("*")
ok = len(all_keys) > 0
record(
    "redis_storage_used",
    ok,
    f"chaves no Redis db=13: {len(all_keys)} (sample={all_keys[:3]})",
)


# ----- TEST 6: Anonymous user — IP como chave -----
print("\n[TEST 6] Anonymous user — IP como chave")
reset_redis()
client = app.test_client()

resp = client.get("/test/public")
body = resp.get_json() or {}
key = body.get("key")
ok = key is not None and key.startswith("ip:")
record(
    "anonymous_uses_ip",
    ok,
    f"key anônima = {key!r} (esperado: 'ip:...')",
)


# ----- TEST 7: SENSITIVE_ENDPOINTS_RATE_LIMIT aplicado -----
print("\n[TEST 7] SENSITIVE_ENDPOINTS_RATE_LIMIT (100/min) — passa 100, bloqueia 101")
reset_redis()
client = app.test_client()

status_codes = []
for i in range(101):
    resp = client.post("/test/sensitive", json={"x": i})
    status_codes.append(resp.status_code)

passed_count = sum(1 for s in status_codes if s == 200)
blocked_count = sum(1 for s in status_codes if s == 429)
ok = passed_count == 100 and blocked_count == 1
record(
    "sensitive_100_per_minute",
    ok,
    f"passed={passed_count} blocked={blocked_count} (esperado: 100+1)",
)


# ----- TEST 8: Isolamento entre profissionais -----
print("\n[TEST 8] Isolamento — prof 1 e prof 2 NÃO compartilham bucket")
reset_redis()
client = app.test_client()

token_1 = get_token_for(1)
for _ in range(50):
    client.post(
        "/test/sensitive",
        json={"x": 1},
        headers={"Authorization": f"Bearer {token_1}"},
    )

token_2 = get_token_for(2)
blocked_for_prof2 = 0
for _ in range(50):
    resp = client.post(
        "/test/sensitive",
        json={"x": 2},
        headers={"Authorization": f"Bearer {token_2}"},
    )
    if resp.status_code == 429:
        blocked_for_prof2 += 1

ok = blocked_for_prof2 == 0
record(
    "isolation_per_professional",
    ok,
    f"prof_2 bloqueado={blocked_for_prof2}/50 (esperado: 0 — bucket separado)",
)


# ----- TEST 9: Webhook continua funcionando após exceder LOGIN_RATE_LIMIT -----
print("\n[TEST 9] Webhook funciona mesmo após login bloqueado")
reset_redis()
client = app.test_client()

# Saturar /test/login (11 requests — 10 + 1 block)
for _ in range(11):
    client.post("/test/login", json={"x": 1})

# Webhook DEVE continuar funcionando (exempt)
resp = client.post("/test/webhook", json={"x": 1})
ok = resp.status_code == 200
record(
    "REDACTED",
    ok,
    f"webhook após login saturado: status={resp.status_code} (esperado: 200)",
)


# ----- TEST 10: contador Redis expira após janela (moving-window) -----
print("\n[TEST 10] Moving-window — verificação básica de TTL no Redis")
reset_redis()
client = app.test_client()

# 1 request em /test/login
client.post("/test/login", json={"x": 1})

# Verificar TTL — chaves de moving-window devem ter TTL próximo de 60s (1 minuto)
all_keys = r.keys("*")
ttls = [r.ttl(k) for k in all_keys if r.type(k) == b"string" or r.type(k).decode() in ("hash", "zset", "list", "stream")]
# Pegar alguns TTLs para mostrar
sample_ttls = [r.ttl(k) for k in all_keys[:3]]
ok = len(all_keys) > 0 and any(0 < t <= 120 for t in ttls if t > 0)
record(
    "moving_window_ttl_set",
    ok,
    f"chaves={len(all_keys)}, TTLs sample={sample_ttls} (esperado: TTL entre 1-120s)",
)


# ============================================================================
# Resultado final
# ============================================================================

print("\n" + "=" * 70)
print("RESUMO FINAL — FASE 5A RATE LIMIT TESTS")
print("=" * 70)

total = len(RESULTS)
passed = sum(1 for _, ok, _ in RESULTS if ok)
failed = total - passed

for name, ok, detail in RESULTS:
    icon = "[PASS]" if ok else "[FAIL]"
    print(f"  {icon} {name}")

print(f"\nTotal: {total} | Passou: {passed} | Falhou: {failed}")
print("=" * 70)

sys.exit(0 if failed == 0 else 1)
