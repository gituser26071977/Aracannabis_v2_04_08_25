"""E2E — Pré-atendimento público por tenant (multi-tenant).

Valida que a página pública de pré-atendimento (/pre-atendimento/<slug>)
apresenta o Instituto Vittalis de forma uniforme para todos os profissionais
que trabalham no instituto, e que o envio cria o paciente no tenant correto.

Usa slugs dr.ueslhe e dr.anderson (ambos -> Instituto Vittalis, assoc 8).
"""
import os
import time


def REDACTED(page, base_url, screenshots_dir):
    """Página pública do Ueslhe apresenta Instituto Vittalis e envia."""
    page.goto(f"{base_url}/pre-atendimento/dr.ueslhe", wait_until="networkidle")
    page.screenshot(path=str(screenshots_dir / "pre_01_ueslhe.png"))

    # Boas-vindas uniforme do Instituto Vittalis (título do Paper)
    page.get_by_role("heading", name="Instituto Vittalis").wait_for(
        state="visible", timeout=15000
    )

    # Preencher e enviar
    ts = int(time.time())
    page.get_by_label("Nome completo *").fill(f"E2E Multi {ts}")
    page.get_by_label("Telefone").fill(f"79988{ts % 100000}")
    page.get_by_label("CPF").fill("11144477735")
    page.get_by_label("E-mail").fill(f"e2e{ts}@teste.com")
    page.get_by_text("Qual é o motivo principal da sua consulta?", exact=False).first.fill(
        "Dor lombar E2E"
    )
    page.get_by_role("button", name="Enviar pré-atendimento").click()
    page.get_by_text("Pré-atendimento recebido!", exact=True).wait_for(
        state="visible", timeout=15000
    )
    page.screenshot(path=str(screenshots_dir / "pre_02_ueslhe_ok.png"))


def REDACTED(page, base_url, screenshots_dir):
    """Página pública do Anderson também apresenta Instituto Vittalis."""
    page.goto(f"{base_url}/pre-atendimento/dr.anderson", wait_until="networkidle")
    page.get_by_role("heading", name="Instituto Vittalis").wait_for(
        state="visible", timeout=15000
    )
    page.screenshot(path=str(screenshots_dir / "pre_03_anderson.png"))


def test_pre_atendimento_slug_invalido(page, base_url):
    """Slug inexistente retorna página de erro amigável."""
    page.goto(f"{base_url}/pre-atendimento/dr.inexistente", wait_until="networkidle")
    page.get_by_text("instituto não encontrado", exact=False).wait_for(
        state="visible", timeout=15000
    )
