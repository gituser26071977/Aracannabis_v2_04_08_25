"""E2E — Tela de conferência de pré-atendimentos."""
import os


def REDACTED(page, base_url, screenshots_dir):
    page.goto(f"{base_url}/login", wait_until="networkidle")
    page.get_by_label("👤 Usuário").fill("ueslhe@gmail.com")
    page.get_by_label("🔒 Senha").fill("S@iAraOS123S@i")
    page.get_by_role("button", name="✨ Entrar").click()
    page.wait_for_url(f"{base_url}/dashboard", timeout=20000)

    page.goto(f"{base_url}/pre-atendimento-conferencia", wait_until="networkidle")
    page.get_by_text("🧾 Pré-atendimentos", exact=True).wait_for(state="visible", timeout=15000)
    page.screenshot(path=str(screenshots_dir / "conf_01_tela.png"))

    # Aba "Pendentes de pagamento" deve listar o item criado
    page.get_by_text("Conferencia UI Teste", exact=False).first.wait_for(
        state="visible", timeout=15000
    )
    page.screenshot(path=str(screenshots_dir / "conf_02_lista.png"))

    # Clicar em "Ver" para abrir os detalhes
    row = page.get_by_role("row").filter(has_text="Conferencia UI Teste")
    row.get_by_role("button", name="Ver").click()
    page.wait_for_timeout(500)
    page.screenshot(path=str(screenshots_dir / "conf_03_detalhe.png"))

    # Confirmar pagamento e liberar
    page.get_by_role("button", name="Confirmar pagamento e liberar").click()
    page.wait_for_timeout(1500)
    page.screenshot(path=str(screenshots_dir / "conf_04_liberado.png"))
