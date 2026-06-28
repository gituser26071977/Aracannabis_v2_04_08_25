"""
FASE 5A — Benchmark comparativo de rate limit (BEFORE vs AFTER).

Como o código já está implantado (FASE 5A), usamos uma abordagem de 2 fases:
  PHASE A (BEFORE): app Flask com rate limit DESATIVADO (memory://, sem limits aplicados)
  PHASE B (AFTER):  app Flask com rate limit ATIVADO (Redis + hybrid key + decorators)

Simula carga de 50 / 200 / 100 usuários simultâneos e mede:
  - Total requests
  - Total failures (429 + 500)
  - Failure %
  - p50/p95/p99 latência
  - RPS sustentado

Uso:
    PYTHONPATH=/tmp/test_pkgs .venv_arac/bin/python tests/security/benchmark_rate_limit.py
"""
import os
import sys
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

# Adicionar raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Forçar uso de Redis local em db=14 (não conflita com testes de db=13)
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["RATE_LIMIT_REDIS_DB"] = "14"
os.environ.pop("RATELIMIT_STORAGE_URL", None)

from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required


def build_app(mode="after"):
    """
    Constrói um app Flask com rate limit em modo BEFORE ou AFTER.

    BEFORE (simula estado pré-FASE 5A):
      - storage_uri=memory://
      - key_func=IP
      - default_limits="60 per minute"
      - SEM decorators @limiter.limit
      - SEM @limiter.exempt

    AFTER (estado pós-FASE 5A):
      - storage_uri=Redis
      - key_func=híbrida
      - default_limits="200 per minute, 5000 per hour"
      - DECORATORS aplicados (LOGIN_RATE_LIMIT, SENSITIVE_RATE_LIMIT)
      - Webhooks @limiter.exempt
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "bench-secret"
    app.config["JWT_SECRET_KEY"] = "bench-jwt-secret"
    jwt = JWTManager(app)

    if mode == "before":
        # ANTES: rate limit precário
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address

        limiter_obj = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["60 per minute"],
            storage_uri="memory://",
            strategy="fixed-window",
        )
        # SEM decorators aplicados nas rotas (simula estado pré-FASE 5A)

        @app.route("/bench/dashboard", methods=["GET"])
        @jwt_required()
        def dashboard():
            return jsonify({"data": list(range(50))})

        @app.route("/bench/login", methods=["POST"])
        def login():
            return jsonify({"ok": True})

        @app.route("/bench/webhook", methods=["POST"])
        def webhook():
            return jsonify({"ok": True})

    else:  # after
        # DEPOIS: rate limit FASE 5A
        from security_config import (
            init_limiter,
            get_hybrid_key,
            LOGIN_RATE_LIMIT,
            SENSITIVE_ENDPOINTS_RATE_LIMIT,
        )
        limiter_obj = init_limiter(app)

        def dashboard():
            return jsonify({"data": list(range(50))})

        def login():
            return jsonify({"ok": True})

        def webhook():
            return jsonify({"ok": True, "webhook": True})

        # Aplicar decorators (padrão FASE 5A)
        dashboard = jwt_required()(dashboard)
        dashboard = limiter_obj.limit(SENSITIVE_ENDPOINTS_RATE_LIMIT)(dashboard)
        login = limiter_obj.limit(LOGIN_RATE_LIMIT)(login)
        webhook = limiter_obj.exempt(webhook)

        app.add_url_rule("/bench/dashboard", view_func=dashboard, methods=["GET"])
        app.add_url_rule("/bench/login", view_func=login, methods=["POST"])
        app.add_url_rule("/bench/webhook", view_func=webhook, methods=["POST"])

    return app


# ============================================================================
# Benchmark runner
# ============================================================================

def run_benchmark(app, scenario_name, n_users, n_requests_per_user, token=None, unique_tokens=False):
    """
    Roda cenário: N usuários fazem M requests cada, em paralelo.

    Se unique_tokens=True, cada usuário recebe um JWT com profissional_id distinto
    (simula 50 profissionais diferentes fazendo requisições). Isso ativa o isolamento
    real da hybrid key.
    """
    client = app.test_client()

    # Limpar Redis se for modo AFTER (db=14)
    import redis as redis_lib
    r = redis_lib.Redis(host="localhost", port=6379, db=14)
    r.flushdb()

    # Gerar tokens por usuário (se unique_tokens)
    tokens = {}
    with app.app_context():
        from flask_jwt_extended import create_access_token
        for u in range(n_users):
            if unique_tokens:
                tokens[u] = create_access_token(identity=f"prof-{u}")
            else:
                tokens[u] = token

    results = []
    results_lock = threading.Lock()

    def user_worker(user_id):
        latencies = []
        status_codes = []
        headers = {"Authorization": f"Bearer {tokens[user_id]}"} if tokens.get(user_id) else {}
        for i in range(n_requests_per_user):
            t0 = time.perf_counter()
            # Simular comportamento misto:
            # 70% dashboard, 20% login (não autenticado), 10% webhook
            if i % 10 < 7:
                resp = client.get("/bench/dashboard", headers=headers)
            elif i % 10 < 9:
                resp = client.post("/bench/login", json={"x": i})
            else:
                resp = client.post("/bench/webhook", json={"x": i})

            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000)  # ms
            status_codes.append(resp.status_code)

        with results_lock:
            results.append({
                "user": user_id,
                "latencies": latencies,
                "status_codes": status_codes,
            })

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=n_users) as executor:
        futures = [
            executor.submit(user_worker, u)
            for u in range(n_users)
        ]
        for f in as_completed(futures):
            f.result()  # levantar exceção se houver
    elapsed = time.perf_counter() - start

    # Agregar métricas
    all_latencies = [l for r in results for l in r["latencies"]]
    all_status = [s for r in results for s in r["status_codes"]]
    total = len(all_status)
    failures = sum(1 for s in all_status if s >= 400)
    failures_429 = sum(1 for s in all_status if s == 429)

    return {
        "scenario": scenario_name,
        "users": n_users,
        "requests_per_user": n_requests_per_user,
        "total_requests": total,
        "failures": failures,
        "failures_429": failures_429,
        "failure_pct": failures / total * 100 if total else 0,
        "rps": total / elapsed if elapsed else 0,
        "elapsed_sec": elapsed,
        "p50_ms": statistics.median(all_latencies) if all_latencies else 0,
        "p95_ms": (
            sorted(all_latencies)[int(len(all_latencies) * 0.95)]
            if all_latencies else 0
        ),
        "p99_ms": (
            sorted(all_latencies)[int(len(all_latencies) * 0.99)]
            if all_latencies else 0
        ),
    }


def print_metrics(m):
    print(f"\n  Cenário: {m['scenario']}")
    print(f"    users={m['users']} req/user={m['requests_per_user']}")
    print(f"    total={m['total_requests']} failures={m['failures']} (429s={m['failures_429']})")
    print(f"    failure_pct={m['failure_pct']:.2f}%")
    print(f"    elapsed={m['elapsed_sec']:.2f}s rps={m['rps']:.2f}")
    print(f"    p50={m['p50_ms']:.2f}ms p95={m['p95_ms']:.2f}ms p99={m['p99_ms']:.2f}ms")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("FASE 5A — BENCHMARK COMPARATIVO (BEFORE vs AFTER)")
    print("=" * 70)

    # Emitir token válido para uso em testes autenticados
    with build_app("after").app_context():
        token = create_access_token(identity="bench-user-1")

    scenarios = [
        ("baseline-50", 50, 20),    # 50 users × 20 req = 1000 req
        ("peak-200", 200, 10),      # 200 users × 10 req = 2000 req
        ("soak-100", 100, 30),      # 100 users × 30 req = 3000 req
    ]

    results_before = []
    results_after = []

    for name, n_users, n_req in scenarios:
        print(f"\n[BEFORE] Cenário {name} — {n_users} users × {n_req} req")
        app_before = build_app("before")
        # Em BEFORE (IP-based), unique_tokens=False é equivalente — todos compartilham IP
        m_before = run_benchmark(app_before, name, n_users, n_req, token=token, unique_tokens=False)
        results_before.append(m_before)
        print_metrics(m_before)

        print(f"\n[AFTER]  Cenário {name} — {n_users} users × {n_req} req (tokens únicos)")
        app_after = build_app("after")
        # Em AFTER, cada usuário = profissional_id distinto = bucket separado (híbrido)
        m_after = run_benchmark(app_after, name, n_users, n_req, token=token, unique_tokens=True)
        results_after.append(m_after)
        print_metrics(m_after)

        # Comparação
        reduction = (
            (m_before["failure_pct"] - m_after["failure_pct"])
            / m_before["failure_pct"] * 100
            if m_before["failure_pct"] > 0 else 0
        )
        rps_gain = (
            (m_after["rps"] - m_before["rps"]) / m_before["rps"] * 100
            if m_before["rps"] > 0 else 0
        )
        print(f"\n  >> Redução de falha: {reduction:.1f}%")
        print(f"  >> Variação de RPS: {rps_gain:+.1f}%")

    # ============================================================================
    # CSV output para report
    # ============================================================================
    out_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "reports", "rate_limit_benchmark.csv"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write("scenario,phase,users,requests_per_user,total_requests,failures,failures_429,failure_pct,rps,elapsed_sec,p50_ms,p95_ms,p99_ms\n")
        for m in results_before:
            f.write(f"{m['scenario']},BEFORE,{m['users']},{m['requests_per_user']},{m['total_requests']},{m['failures']},{m['failures_429']},{m['failure_pct']:.2f},{m['rps']:.2f},{m['elapsed_sec']:.2f},{m['p50_ms']:.2f},{m['p95_ms']:.2f},{m['p99_ms']:.2f}\n")
        for m in results_after:
            f.write(f"{m['scenario']},AFTER,{m['users']},{m['requests_per_user']},{m['total_requests']},{m['failures']},{m['failures_429']},{m['failure_pct']:.2f},{m['rps']:.2f},{m['elapsed_sec']:.2f},{m['p50_ms']:.2f},{m['p95_ms']:.2f},{m['p99_ms']:.2f}\n")

    print(f"\n\nCSV gravado em: {out_path}")
    print("=" * 70)
