"""
locustfile.py — Teste de carga do AraOS contra o VPS público.

Simula uso realista de uma clínica média (1 profissional fazendo
operações de prontuário + dashboard + IA + módulos).

Uso:
    # baseline (50 usuários, 5min)
    locust -f tests/load/locustfile.py --headless -u 50 -r 5 -t 5m \
        --host=https://api.visualsmartflow.com.br \
        --html reports/load_baseline.html --csv reports/load_baseline

    # peak (200 usuários, 3min)
    locust -f tests/load/locustfile.py --headless -u 200 -r 20 -t 3m \
        --host=https://api.visualsmartflow.com.br \
        --html reports/load_peak.html --csv reports/load_peak

    # soak (100 usuários, 15min)
    locust -f tests/load/locustfile.py --headless -u 100 -r 10 -t 15m \
        --host=https://api.visualsmartflow.com.br \
        --html reports/load_soak.html --csv reports/load_soak

IMPORTANTE: usa o usuário tester.modulos@araos.dev já criado no banco
para não gerar lixo. Para testes destrutivos, criar usuário dedicado.
"""
import os
import random
import logging
from locust import HttpUser, task, between, events

logger = logging.getLogger(__name__)

# Credenciais (pode ser sobrescrito via env)
EMAIL = os.getenv("LOAD_TEST_EMAIL", "tester.modulos@araos.dev")
PASSWORD = os.getenv("LOAD_TEST_PASSWORD", "Tester@2025")


class AraOSUser(HttpUser):
    """
    Simula 1 profissional logado fazendo operações típicas de consultório.
    Pesa mais em GETs (listagens/dashboard) e menos em POSTs (criar paciente).
    """

    # Espera entre 1 e 3 segundos entre tasks (think time humano)
    wait_time = between(1, 3)

    # ===== Lifecycle =====
    def on_start(self):
        """Login inicial — falha fatal se não autenticar."""
        self.token = None
        self.headers = {}
        self.pacientes_ids = []
        self.modulos_ids = []

        try:
            with self.client.post(
                "/api/auth/login",
                json={"email": EMAIL, "senha": PASSWORD},
                name="POST /api/auth/login (setup)",
                catch_response=True,
                timeout=10,
            ) as r:
                if r.status_code == 200:
                    body = r.json()
                    self.token = body.get("access_token")
                    self.headers = {
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                    }
                    r.success()
                    logger.info(f"login_ok token_len={len(self.token or '')}")
                else:
                    r.failure(f"login_failed status={r.status_code} body={r.text[:200]}")
        except Exception as e:
            logger.exception(f"on_start_failed: {e}")

        # Pré-carrega IDs para usar nas tasks (1 chamada de cada)
        if self.token:
            self._warmup_ids()

    def _warmup_ids(self):
        """Cache local de IDs de pacientes e módulos (1 request por usuário)."""
        try:
            r = self.client.get(
                "/api/pacientes?limit=20",
                headers=self.headers,
                name="WARMUP /api/pacientes",
                timeout=10,
            )
            if r.status_code == 200:
                body = r.json()
                pacientes = body.get("pacientes") or body.get("data") or body.get("items") or []
                self.pacientes_ids = [p.get("id") for p in pacientes if p.get("id")][:20]
        except Exception:
            pass

        try:
            r = self.client.get(
                "/api/modulos",
                headers=self.headers,
                name="WARMUP /api/modulos",
                timeout=10,
            )
            if r.status_code == 200:
                body = r.json()
                mods = body.get("modulos") or []
                self.modulos_ids = [m.get("slug") for m in mods if m.get("slug")]
        except Exception:
            pass

    # ===== Tasks (ponderadas por @task(N)) =====

    @task(20)  # mais comum: dashboard
    def ver_dashboard(self):
        # NOTA: este endpoint está retornando 500 em produção (bug column data_revogacao).
        # Mantido no teste para detectar regressões após fix.
        with self.client.get(
            "/api/dashboard/stats",
            headers=self.headers,
            name="GET /api/dashboard/stats",
            timeout=15,
            catch_response=True,
        ) as r:
            if r.status_code == 500:
                r.failure("known_bug: column pacientes.data_revogacao does not exist")

    @task(15)
    def listar_pacientes(self):
        # NOTA: também quebrado pelo mesmo bug (column data_revogacao).
        with self.client.get(
            "/api/pacientes?limit=50",
            headers=self.headers,
            name="GET /api/pacientes",
            timeout=15,
            catch_response=True,
        ) as r:
            if r.status_code == 500:
                r.failure("known_bug: column pacientes.data_revogacao does not exist")

    @task(10)
    def detalhe_paciente(self):
        if not self.pacientes_ids:
            return
        pid = random.choice(self.pacientes_ids)
        self.client.get(
            f"/api/pacientes/{pid}",
            headers=self.headers,
            name="GET /api/pacientes/<id>",
            timeout=10,
        )

    @task(8)
    def listar_consultas(self):
        self.client.get(
            "/api/consultas",
            headers=self.headers,
            name="GET /api/consultas",
            timeout=10,
        )

    @task(7)
    def listar_modulos(self):
        self.client.get(
            "/api/modulos",
            headers=self.headers,
            name="GET /api/modulos",
            timeout=10,
        )

    @task(6)
    def listar_planos(self):
        self.client.get(
            "/api/planos",
            headers=self.headers,
            name="GET /api/planos",
            timeout=10,
        )

    @task(5)
    def status_api(self):
        # endpoint público, sem auth — mede latência mínima
        self.client.get(
            "/api/status",
            name="GET /api/status (public)",
            timeout=5,
        )

    @task(4)
    def catalogo_produtos(self):
        self.client.get(
            "/api/catalogo/produtos",
            headers=self.headers,
            name="GET /api/catalogo/produtos",
            timeout=10,
        )

    @task(3)
    def listar_prescricoes_paciente(self):
        """Lista prescrições do primeiro paciente do warmup (precisa de id)."""
        if not self.pacientes_ids:
            return
        pid = self.pacientes_ids[0]
        self.client.get(
            f"/api/prescricoes/paciente/{pid}",
            headers=self.headers,
            name="GET /api/prescricoes/paciente/<id>",
            timeout=10,
        )

    @task(2)
    def billing_plans(self):
        self.client.get(
            "/api/billing/plans",
            headers=self.headers,
            name="GET /api/billing/plans",
            timeout=10,
        )

    @task(1)
    def modulos_detalhe(self):
        """Puxa detalhe de cada módulo — gera carga no /api/meus-modulos/<slug>."""
        if not self.modulos_ids:
            return
        slug = random.choice(self.modulos_ids)
        self.client.get(
            f"/api/meus-modulos/{slug}",
            headers=self.headers,
            name="GET /api/meus-modulos/<slug>",
            timeout=10,
        )


# ===== Hooks para logging/métricas customizadas =====

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("=" * 70)
    logger.info("LOAD TEST START")
    logger.info(f"  host={environment.host}")
    logger.info(f"  users={environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else '?'}")
    logger.info("=" * 70)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("=" * 70)
    logger.info("LOAD TEST STOP")
    stats = environment.stats
    logger.info(f"  total_requests={stats.total.num_requests}")
    logger.info(f"  total_failures={stats.total.num_failures}")
    logger.info(f"  failure_pct={stats.total.fail_ratio * 100:.2f}%")
    logger.info(f"  median_response_ms={stats.total.median_response_time:.1f}")
    logger.info(f"  p95_response_ms={stats.total.get_response_time_percentile(0.95):.1f}")
    logger.info(f"  p99_response_ms={stats.total.get_response_time_percentile(0.99):.1f}")
    logger.info(f"  max_response_ms={stats.total.max_response_time}")
    logger.info(f"  current_rps={stats.total.current_rps:.2f}")
    logger.info("=" * 70)
