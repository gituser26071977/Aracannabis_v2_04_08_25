"""E2E — Fluxo 4: CRUD Paciente (criar, editar, excluir)"""
import time

def _login(page, base_url):
    page.goto(f"{base_url}/login")
    page.fill('input[name="identifier"]', "tester.modulos@araos.dev")
    page.fill('input[name="password"]', "Tester@2025")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard", timeout=15000)


def test_paciente_create_edit_delete(page, base_url, screenshots_dir):
    _login(page, base_url)

    # CREATE
    page.goto(f"{base_url}/pacientes/novo")
    page.screenshot(path=str(screenshots_dir / "04_paciente_create_form.png"))

    ts = int(time.time())
    page.fill('input[name="nome"]', f"Paciente E2E {ts}")
    page.fill('input[name="cpf"]', "529.982.247-25")  # CPF válido fake
    page.fill('input[name="data_nascimento"]', "1985-06-15")
    page.fill('input[name="telefone"]', "(11) 98888-7777")
    page.fill('input[name="email"]', f"paciente_{ts}@test.com")
    page.click('button[type="submit"]')
    page.wait_for_url(lambda u: "/pacientes/" in u and "/novo" not in u, timeout=15000)
    paciente_url = page.url
    page.screenshot(path=str(screenshots_dir / "04_paciente_created.png"))

    # EDIT
    page.click('button:has-text("Editar"), a:has-text("Editar")')
    page.wait_for_selector('input[name="nome"]', timeout=10000)
    page.fill('input[name="telefone"]', "(11) 97777-6666")
    page.click('button[type="submit"]')
    page.wait_for_url(paciente_url, timeout=10000)
    page.screenshot(path=str(screenshots_dir / "04_paciente_edited.png"))

    # DELETE
    page.click('button:has-text("Excluir"), button[aria-label="delete"]')
    page.click('button:has-text("Confirmar"), button:has-text("Sim")')
    page.wait_for_url(f"{base_url}/pacientes", timeout=10000)
    page.screenshot(path=str(screenshots_dir / "04_paciente_deleted.png"))
