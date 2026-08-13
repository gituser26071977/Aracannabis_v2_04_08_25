"""E2E — Regressão: módulo Financeiro visível na página de Gestão (admin).

Valida o fix do bug em que admin/superadmin eram tratados como perfil
assistencial quando `perfil_efetivo` ainda não havia sido carregado após o
login, ocultando o grupo FINANCEIRO em /gestao.

Fluxo:
  1. Login (Ueslhe, admin)
  2. Navegar para /gestao
  3. Assert grupo FINANCEIRO visível (Financeiro / Convênios & Tabela /
     Relatórios Financeiros)
  4. Clicar em "Relatórios Financeiros" -> /relatorios-financeiros
"""
import os


def test_admin_ve_financeiro_em_gestao(page, base_url, screenshots_dir):
    identifier = os.environ.get("E2E_USER", "ueslhe@gmail.com")
    senha = os.environ.get("E2E_PASS", "S@iAraOS123S@i")

    # 1. Login
    page.goto(f"{base_url}/login", wait_until="networkidle")
    page.get_by_label("👤 Usuário").fill(identifier)
    page.get_by_label("🔒 Senha").fill(senha)
    page.get_by_role("button", name="✨ Entrar").click()
    page.wait_for_url(f"{base_url}/dashboard", timeout=20000)
    page.screenshot(path=str(screenshots_dir / "fin_01_dashboard.png"))

    # 2. Navegar para Gestão
    page.goto(f"{base_url}/gestao", wait_until="networkidle")
    page.screenshot(path=str(screenshots_dir / "fin_02_gestao.png"))

    # 3. Grupo FINANCEIRO visível
    page.get_by_text("FINANCEIRO", exact=True).wait_for(state="visible", timeout=10000)
    page.get_by_text("Financeiro", exact=True).wait_for(state="visible", timeout=5000)
    page.get_by_text("Convênios & Tabela", exact=True).wait_for(state="visible", timeout=5000)
    relatorios = page.get_by_text("Relatórios Financeiros", exact=True)
    relatorios.wait_for(state="visible", timeout=5000)
    page.screenshot(path=str(screenshots_dir / "fin_03_financeiro_visivel.png"))

    # 4. Navegar até a tela de relatórios financeiros
    page.get_by_text("Relatórios Financeiros", exact=True).click()
    page.wait_for_url(f"{base_url}/relatorios-financeiros", timeout=15000)
    page.screenshot(path=str(screenshots_dir / "fin_04_relatorios.png"))

    assert "/relatorios-financeiros" in page.url
