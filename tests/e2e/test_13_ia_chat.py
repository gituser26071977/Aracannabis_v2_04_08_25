"""E2E — Fluxo 13: IA Chat + LGPD"""

def test_ia_chat(page, base_url, screenshots_dir):
    page.goto(f"{base_url}/login")
    page.fill('input[name="identifier"]', "tester.modulos@araos.dev")
    page.fill('input[name="password"]', "Tester@2025")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard", timeout=15000)

    page.goto(f"{base_url}/ai-chat")
    page.wait_for_selector('input[placeholder*="mensagem" i], textarea[placeholder*="mensagem" i]', timeout=10000)
    page.screenshot(path=str(screenshots_dir / "13_ia_chat_open.png"))
    page.fill('input[placeholder*="mensagem" i], textarea[placeholder*="mensagem" i]', "Quais sintomas posso monitorar para enxaqueca?")
    page.click('button[aria-label*="send" i], button:has-text("Enviar")')
    page.wait_for_selector('text=/resposta|sintomas|enxaqueca/i', timeout=15000)
    page.screenshot(path=str(screenshots_dir / "13_ia_chat_response.png"))


def test_lgpd_consentimento(page, base_url, screenshots_dir):
    """LGPD — verificar termos de consentimento estão presentes em alguma área."""
    page.goto(f"{base_url}/cadastro")
    page.wait_for_selector('text=/termo|consentimento|lgpd|privacidade/i', timeout=10000)
    page.screenshot(path=str(screenshots_dir / "13_lgpd_consent.png"))
