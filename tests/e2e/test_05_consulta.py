"""E2E — Fluxo 5: Consulta"""
import time

def test_consulta_criar(page, base_url, screenshots_dir):
    page.goto(f"{base_url}/login")
    page.fill('input[name="identifier"]', "tester.modulos@araos.dev")
    page.fill('input[name="password"]', "Tester@2025")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard", timeout=15000)

    page.goto(f"{base_url}/pacientes")
    page.click('a:has-text("Ver"), tr:first-child a', timeout=10000)
    page.wait_for_url(lambda u: "/pacientes/" in u, timeout=10000)

    page.goto(page.url + "/consultas/nova")
    page.screenshot(path=str(screenshots_dir / "05_consulta_form.png"))
    page.fill('textarea[name="queixa_principal"]', "Dor lombar crônica há 6 meses")
    page.fill('textarea[name="historia_doenca"]', "Piora progressiva, sem trauma")
    page.fill('input[name="data_consulta"]', "2026-06-25T14:30")
    page.click('button[type="submit"]')
    page.wait_for_url(lambda u: "/consultas/" in u and "/nova" not in u, timeout=15000)
    page.screenshot(path=str(screenshots_dir / "05_consulta_ok.png"))
