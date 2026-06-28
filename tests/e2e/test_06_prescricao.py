"""E2E — Fluxo 6: Prescrição"""

def test_prescricao_criar(page, base_url, screenshots_dir):
    page.goto(f"{base_url}/login")
    page.fill('input[name="identifier"]', "tester.modulos@araos.dev")
    page.fill('input[name="password"]', "Tester@2025")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard", timeout=15000)

    # Ir direto para módulo de prescrições
    page.goto(f"{base_url}/prescricoes/nova")
    page.screenshot(path=str(screenshots_dir / "06_prescricao_form.png"))
    page.select_option('select[name="paciente_id"]', index=1)
    page.select_option('select[name="produto_id"]', index=1)
    page.fill('input[name="dose_mg"]', "5.0")
    page.fill('input[name="frequencia"]', "2x ao dia")
    page.fill('input[name="duracao_dias"]', "30")
    page.click('button[type="submit"]')
    page.wait_for_url(lambda u: "/prescricoes/" in u and "/nova" not in u, timeout=15000)
    page.screenshot(path=str(screenshots_dir / "06_prescricao_ok.png"))
