"""E2E — Pré-atendimento público por tenant + conferência/pagamento.

Fluxo:
1. Página pública (/pre-atendimento/<slug>) apresenta Instituto Vittalis.
2. Envio cria pré-atendimento pendente (NÃO cria paciente ainda).
3. Sem pagamento confirmado, a conferência NEGA a liberação.
4. Com pagamento confirmado, a conferência LIBERA (cria paciente).
"""
import os
import time


def REDACTED(page, base_url, screenshots_dir):
    """Página pública apresenta chat do Instituto Vittalis."""
    page.goto(f"{base_url}/pre-atendimento/dr.ueslhe", wait_until="networkidle")
    page.screenshot(path=str(screenshots_dir / "pre_01_ueslhe.png"))
    page.get_by_text("Instituto Vittalis", exact=False).first.wait_for(
        state="visible", timeout=15000
    )
    page.get_by_text("qual é o seu nome completo?", exact=False).first.wait_for(
        state="visible", timeout=15000
    )
    page.screenshot(path=str(screenshots_dir / "pre_02_chat.png"))


def REDACTED(page, base_url, screenshots_dir):
    """Página pública do Anderson apresenta Instituto Vittalis."""
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
