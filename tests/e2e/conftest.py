"""
AraOS — Playwright E2E conftest (MISSÃO 20 FASE 4)
Configuração comum para 13 fluxos.
"""
import os
import pytest
from pathlib import Path

BASE_URL = os.environ.get("BASE_URL", "https://staging.visualsmartflow.com.br")
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Credenciais de teste (já criadas em staging)
TEST_USER = {
    "identifier": "tester.modulos@araos.dev",
    "password": "Tester@2025",
}


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture(scope="session")
def screenshots_dir() -> Path:
    return SCREENSHOTS_DIR


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Força viewport desktop + aceita storage state."""
    return {**browser_context_args, "viewport": {"width": 1366, "height": 768}}


@pytest.fixture(autouse=True)
def _screenshot_on_failure(request, page, screenshots_dir):
    """Tira screenshot em caso de falha."""
    yield
    if request.node.rep_call.failed:
        name = request.node.name.replace("/", "_") + "_FAIL.png"
        page.screenshot(path=str(screenshots_dir / name), full_page=True)


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
