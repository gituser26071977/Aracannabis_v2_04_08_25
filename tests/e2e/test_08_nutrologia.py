"""E2E — Fluxo 8: Nutrologia"""

def test_nutrologia_avaliar(page, base_url, screenshots_dir):
    page.goto(f"{base_url}/login")
    page.fill('input[name="identifier"]', "tester.modulos@araos.dev")
    page.fill('input[name="password"]', "Tester@2025")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard", timeout=15000)

    page.goto(f"{base_url}/nutrologia")
    page.screenshot(path=str(screenshots_dir / "08_nutrologia_list.png"))
    page.click('a:has-text("Nova avaliação"), button:has-text("Nova avaliação")', timeout=10000)
    page.wait_for_selector('input[name="peso_kg"]', timeout=10000)
    page.screenshot(path=str(screenshots_dir / "08_nutrologia_form.png"))
    page.select_option('select[name="paciente_id"]', index=1)
    page.fill('input[name="peso_kg"]', "72.5")
    page.fill('input[name="altura_cm"]', "175")
    page.fill('input[name="imc"]', "23.7")
    page.fill('textarea[name="observacoes"]', "Dieta balanceada; suplementar vitamina D")
    page.click('button[type="submit"]')
    page.wait_for_url(lambda u: "/nutrologia/" in u and "/nova" not in u, timeout=15000)
    page.screenshot(path=str(screenshots_dir / "08_nutrologia_ok.png"))
