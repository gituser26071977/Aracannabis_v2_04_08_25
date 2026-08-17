"""E2E — Chat do pré-atendimento com agente."""
import os


def test_chat_pre_atendimento_abre(page, base_url, screenshots_dir):
    """Página de pré-atendimento abre como chat com agente."""
    page.goto(f"{base_url}/pre-atendimento/dr.ueslhe", wait_until="networkidle")
    page.screenshot(path=str(screenshots_dir / "chat_01_abre.png"))

    # Header do instituto + saudação do agente
    page.get_by_text("Instituto Vittalis", exact=False).first.wait_for(
        state="visible", timeout=15000
    )
    page.get_by_text("qual é o seu nome completo?", exact=False).first.wait_for(
        state="visible", timeout=15000
    )
    page.screenshot(path=str(screenshots_dir / "chat_02_saudacao.png"))

    # Enviar o nome
    page.get_by_placeholder("Digite sua resposta...").fill("E2E Chat Nome")
    page.get_by_role("button").filter(has=page.locator("svg")).last.click()
    page.wait_for_timeout(5000)
    page.screenshot(path=str(screenshots_dir / "chat_03_resposta.png"))
