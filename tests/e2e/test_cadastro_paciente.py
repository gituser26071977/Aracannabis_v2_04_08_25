"""E2E — Cadastro de paciente: corrigir 404 no botão 'Cadastrar paciente'.

Valida que, com a lista vazia, o EmptyState "Cadastrar paciente" abre o
formulário (aba Novo Paciente) sem navegar para rota inexistente.
"""
import os


def test_cadastrar_paciente_sem_404(page, base_url, screenshots_dir):
    identifier = os.environ.get("E2E_USER", "ueslhe@gmail.com")
    senha = os.environ.get("E2E_PASS", "S@iAraOS123S@i")

    page.goto(f"{base_url}/login", wait_until="networkidle")
    page.get_by_label("👤 Usuário").fill(identifier)
    page.get_by_label("🔒 Senha").fill(senha)
    page.get_by_role("button", name="✨ Entrar").click()
    page.wait_for_url(f"{base_url}/dashboard", timeout=20000)

    page.goto(f"{base_url}/pacientes", wait_until="networkidle")
    page.get_by_text("Nenhum paciente cadastrado", exact=True).wait_for(state="visible", timeout=15000)
    page.screenshot(path=str(screenshots_dir / "cad_01_lista.png"))

    # Clicar no botão "Cadastrar paciente" (EmptyState) — não deve dar 404
    page.get_by_role("button", name="Cadastrar paciente").click()
    page.wait_for_timeout(1500)
    page.screenshot(path=str(screenshots_dir / "cad_02_formulario.png"))

    # Não deve estar em rota inexistente
    assert "pacientes/novo" not in page.url, f"Redirecionou para rota inexistente: {page.url}"
    # A aba "Novo Paciente" deve estar ativa com o formulário
    page.get_by_text("Novo Paciente", exact=True).first.wait_for(state="visible", timeout=5000)
    assert "/pacientes" in page.url
