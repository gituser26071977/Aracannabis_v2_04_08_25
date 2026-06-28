"""E2E — Fluxo 2: Logout"""
import pytest

def test_logout(page, base_url, screenshots_dir):
    # Setup: login
    page.goto(f"{base_url}/login")
    page.fill('input[name="identifier"]', "tester.modulos@araos.dev")
    page.fill('input[name="password"]', "Tester@2025")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard")

    # Act: logout
    page.click('button[aria-label="logout"], button:has-text("Sair"), a:has-text("Sair")')
    page.wait_for_url(f"{base_url}/login", timeout=10000)
    page.screenshot(path=str(screenshots_dir / "02_logout_ok.png"))
    assert "/login" in page.url
