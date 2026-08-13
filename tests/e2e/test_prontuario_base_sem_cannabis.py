"""E2E — Prontuário base sem módulo cannabis.

Valida que um profissional SEM o módulo cannabis-medicinal:
  1. Em /gestao, NÃO vê o grupo OPERAÇÕES (associações/estoque são
     específicos do fluxo canabinoide).
  2. O seletor de associação NÃO aparece no header (association = cannabis).

Usa o profissional medico.base (Vittalis) que não possui o módulo cannabis.
"""
import os


def test_sem_cannabis_sem_associacoes(page, base_url, screenshots_dir):
    identifier = os.environ.get("E2E_USER_SEM_CANNABIS", "medico.base@teste.local")
    senha = os.environ.get("E2E_PASS_SEM_CANNABIS", "Base@123456")

    # 1. Login
    page.goto(f"{base_url}/login", wait_until="networkidle")
    page.get_by_label("👤 Usuário").fill(identifier)
    page.get_by_label("🔒 Senha").fill(senha)
    page.get_by_role("button", name="✨ Entrar").click()
    page.wait_for_url(f"{base_url}/dashboard", timeout=20000)

    # 2. Em /gestao: grupo OPERAÇÕES (associações) não deve aparecer
    page.goto(f"{base_url}/gestao", wait_until="networkidle")
    page.screenshot(path=str(screenshots_dir / "semcannabis_01_gestao.png"))
    operacoes = page.get_by_text("OPERAÇÕES", exact=True)
    assert operacoes.count() == 0, "Grupo OPERAÇÕES (associações) visível sem módulo cannabis"

    # 3. Seletor de associação não deve estar visível no header
    # (AssociationSelector só renderiza com módulo cannabis ativo)
    selector = page.locator("#association-select")
    assert selector.count() == 0, "Seletor de associação visível sem módulo cannabis"
    page.screenshot(path=str(screenshots_dir / "semcannabis_02_sem_associacao.png"))
