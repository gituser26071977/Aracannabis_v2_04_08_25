"""E2E — Fluxo 9: Billing"""

def test_billing_planos(page, base_url, screenshots_dir):
    page.goto(f"{base_url}/login")
    page.fill('input[name="identifier"]', "tester.modulos@araos.dev")
    page.fill('input[name="password"]', "Tester@2025")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard", timeout=15000)

    page.goto(f"{base_url}/billing/plans")
    page.wait_for_selector('text=/plano|plan/i', timeout=10000)
    page.screenshot(path=str(screenshots_dir / "09_billing_plans.png"))

    page.goto(f"{base_url}/billing/history")
    page.wait_for_selector('text=/hist|recibo|invoice|fatura/i', timeout=10000)
    page.screenshot(path=str(screenshots_dir / "09_billing_history.png"))
