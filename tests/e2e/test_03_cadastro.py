"""E2E — Fluxo 3: Cadastro de profissional"""
import time

def test_cadastro_profissional(page, base_url, screenshots_dir):
    ts = int(time.time())
    email = f"e2e_prof_{ts}@araos.dev"
    page.goto(f"{base_url}/cadastro")
    page.screenshot(path=str(screenshots_dir / "03_cadastro_form.png"))

    page.fill('input[name="nome"]', "Dr. E2E Test")
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', "E2ETeste@2026")
    page.fill('input[name="confirmar_password"]', "E2ETeste@2026")
    page.fill('input[name="cpf"]', "123.456.789-00")
    page.fill('input[name="telefone"]', "(11) 99999-9999")
    page.click('input[name="termos"]')
    page.click('button[type="submit"]')

    # Após cadastro, redireciona para verificação de email ou login
    page.wait_for_url(lambda url: "/login" in url or "/verificar" in url or "/dashboard" in url, timeout=15000)
    page.screenshot(path=str(screenshots_dir / "03_cadastro_ok.png"))
