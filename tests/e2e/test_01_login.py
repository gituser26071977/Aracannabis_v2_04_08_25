"""E2E — Fluxo 1: Login"""
import pytest

def test_login_sucesso(page, base_url, screenshots_dir):
    page.goto(f"{base_url}/login")
    page.screenshot(path=str(screenshots_dir / "01_login_form.png"))
    page.fill('input[name="identifier"]', "tester.modulos@araos.dev")
    page.fill('input[name="password"]', "Tester@2025")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard", timeout=15000)
    page.screenshot(path=str(screenshots_dir / "01_login_ok.png"))
    assert "dashboard" in page.url


def test_login_invalido(page, base_url, screenshots_dir):
    page.goto(f"{base_url}/login")
    page.fill('input[name="identifier"]', "tester.modulos@araos.dev")
    page.fill('input[name="password"]', "WRONG_PASSWORD")
    page.click('button[type="submit"]')
    page.wait_for_selector('text=/inválid|incorret|erro/i', timeout=10000)
    page.screenshot(path=str(screenshots_dir / "01_login_fail.png"))
    assert "dashboard" not in page.url
