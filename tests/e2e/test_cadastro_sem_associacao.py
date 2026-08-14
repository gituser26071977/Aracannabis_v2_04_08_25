"""E2E — Cadastro de paciente sem campo 'Associação de Pacientes'."""
import os

def test_paciente_sem_associacao(page, base_url, screenshots_dir):
    page.goto(f"{base_url}/login", wait_until="networkidle")
    page.get_by_label("👤 Usuário").fill("ueslhe@gmail.com")
    page.get_by_label("🔒 Senha").fill("S@iAraOS123S@i")
    page.get_by_role("button", name="✨ Entrar").click()
    page.wait_for_url(f"{base_url}/dashboard", timeout=20000)

    page.goto(f"{base_url}/pacientes", wait_until="networkidle")
    page.get_by_text("Novo Paciente", exact=True).first.click()
    page.wait_for_timeout(1500)
    page.screenshot(path=str(screenshots_dir / "cad_sem_assoc.png"))

    campo = page.get_by_text("Associação de Pacientes (opcional)", exact=True)
    assert campo.count() == 0, "Campo 'Associação de Pacientes' ainda visível"
