"""E2E — Fluxo 7: Cannabis (módulo cannabis)"""

def test_cannabis_modulo(page, base_url, screenshots_dir):
    page.goto(f"{base_url}/login")
    page.fill('input[name="identifier"]', "tester.modulos@araos.dev")
    page.fill('input[name="password"]', "Tester@2025")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard", timeout=15000)

    page.goto(f"{base_url}/cannabis")
    page.wait_for_selector('text=/cannabis|canabin/i', timeout=10000)
    page.screenshot(path=str(screenshots_dir / "07_cannabis_list.png"))

    page.click('a:has-text("Novo perfil"), button:has-text("Novo perfil")', timeout=10000)
    page.wait_for_selector('input[name="paciente_id"]', timeout=10000)
    page.screenshot(path=str(screenshots_dir / "07_cannabis_form.png"))
    page.select_option('select[name="paciente_id"]', index=1)
    page.select_option('select[name="objetivo_terapeutico"]', index=1)
    page.fill('input[name="thc_ratio"]', "0.10")
    page.fill('input[name="cbd_ratio"]', "0.20")
    page.click('button[type="submit"]')
    page.wait_for_url(lambda u: "/cannabis/" in u and "/novo" not in u, timeout=15000)
    page.screenshot(path=str(screenshots_dir / "07_cannabis_ok.png"))
