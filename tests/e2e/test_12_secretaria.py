"""E2E — Fluxo 12: Secretária Virtual (Dr. Anderson)"""

def test_secretaria_dr_anderson(page, base_url, screenshots_dir):
    page.goto(f"{base_url}/login")
    page.fill('input[name="identifier"]', "tester.modulos@araos.dev")
    page.fill('input[name="password"]', "Tester@2025")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard", timeout=15000)

    page.goto(f"{base_url}/secretaria")
    page.wait_for_selector('text=/secretária|dr\\. anderson|anderson/i', timeout=10000)
    page.screenshot(path=str(screenshots_dir / "12_secretaria_home.png"))

    page.fill('textarea[name="mensagem"]', "Quero reagendar consulta de Maria Silva para próxima terça")
    page.click('button[type="submit"]')
    page.wait_for_selector('text=/anderson|resposta/i', timeout=15000)
    page.screenshot(path=str(screenshots_dir / "12_secretaria_chat.png"))
