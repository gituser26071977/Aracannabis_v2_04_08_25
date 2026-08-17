"""E2E — Tela de conferência de pré-atendimentos."""
import os
import time
import urllib.request
import json


def _criar_pre_atendimento(base_url, nome):
    """Cria um pré-atendimento público via API (pendente de pagamento)."""
    api_base = base_url.replace("siap.", "api.")
    req = urllib.request.Request(
        f"{api_base}/api/public/pre-atendimento/dr.ueslhe",
        data=json.dumps({"nome": nome, "telefone": "79999990077", "queixa_principal": "Teste conferencia"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def REDACTED(page, base_url, screenshots_dir):
    nome = f"Conferencia E2E {int(time.time())}"
    _criar_pre_atendimento(base_url, nome)

    page.goto(f"{base_url}/login", wait_until="networkidle")
    page.get_by_label("👤 Usuário").fill("ueslhe@gmail.com")
    page.get_by_label("🔒 Senha").fill("S@iAraOS123S@i")
    page.get_by_role("button", name="✨ Entrar").click()
    page.wait_for_url(f"{base_url}/dashboard", timeout=20000)

    page.goto(f"{base_url}/pre-atendimento-conferencia", wait_until="networkidle")
    page.get_by_text("🧾 Pré-atendimentos", exact=True).wait_for(state="visible", timeout=15000)
    page.screenshot(path=str(screenshots_dir / "conf_01_tela.png"))

    # Aba "Pendentes de pagamento" deve listar o item criado
    page.get_by_text(nome, exact=False).first.wait_for(state="visible", timeout=15000)
    page.screenshot(path=str(screenshots_dir / "conf_02_lista.png"))

    # Clicar em "Ver" para abrir os detalhes
    row = page.get_by_role("row").filter(has_text=nome)
    row.get_by_role("button", name="Ver").click()
    page.wait_for_timeout(500)
    page.screenshot(path=str(screenshots_dir / "conf_03_detalhe.png"))
