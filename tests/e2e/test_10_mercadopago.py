"""E2E — Fluxo 10: MercadoPago (sandbox)"""

def test_mercadopago_checkout_init(page, base_url, screenshots_dir):
    page.goto(f"{base_url}/login")
    page.fill('input[name="identifier"]', "tester.modulos@araos.dev")
    page.fill('input[name="password"]', "Tester@2025")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard", timeout=15000)

    page.goto(f"{base_url}/billing/checkout?plan=premium")
    page.wait_for_selector('text=/mercadopago|mp|checkout|pagamento/i', timeout=15000)
    page.screenshot(path=str(screenshots_dir / "10_mp_init.png"))
