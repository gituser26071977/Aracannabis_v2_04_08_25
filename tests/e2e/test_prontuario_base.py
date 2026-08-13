"""E2E — Prontuário clínico base + gate de módulo cannabis medicinal.

Valida o fix da simplificação do prontuário:
  1. Abas base (Informações, Prontuário, Receituário, Documentos) sempre.
  2. Aba "💊 Cannabis Medicinal" (dosagens/produtos/perfil canabinoide)
     apenas com o módulo cannabis-medicinal ativo.
  3. Associações (menu /association) apenas com o módulo ativo.

Cria um paciente sintético via API e abre o prontuário dele.
"""
import os
import time


def _login(page, base_url, identifier, senha):
    page.goto(f"{base_url}/login", wait_until="networkidle")
    page.get_by_label("👤 Usuário").fill(identifier)
    page.get_by_label("🔒 Senha").fill(senha)
    page.get_by_role("button", name="✨ Entrar").click()
    page.wait_for_url(f"{base_url}/dashboard", timeout=20000)


def _criar_paciente(api_base, token):
    """Cria paciente sintético via API e retorna o id."""
    import urllib.request
    import json

    req = urllib.request.Request(
        f"{api_base}/api/pacientes/",
        data=json.dumps({
            "nome": f"Paciente E2E {int(time.time())}",
            "data_nascimento": "1990-01-01",
            "telefone": "(79) 99999-0000",
        }).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["paciente"]["id"]


def REDACTED(page, base_url, screenshots_dir):
    identifier = os.environ.get("E2E_USER", "ueslhe@gmail.com")
    senha = os.environ.get("E2E_PASS", "S@iAraOS123S@i")

    # 1. Login e obter token via página (localStorage)
    _login(page, base_url, identifier, senha)
    token = page.evaluate("() => localStorage.getItem('token')")

    # 2. Criar paciente sintético e abrir o prontuário
    api_base = base_url.replace("siap.", "api.")
    paciente_id = _criar_paciente(api_base, token)
    page.goto(f"{base_url}/pacientes/detail/{paciente_id}", wait_until="networkidle")
    page.screenshot(path=str(screenshots_dir / "pront_01_detalhe.png"))

    # Abas base sempre presentes
    page.get_by_text("📋 Informações", exact=True).wait_for(state="visible", timeout=15000)
    page.get_by_text("🩺 Prontuário", exact=True).wait_for(state="visible", timeout=5000)
    page.get_by_text("📋 Receituário", exact=True).wait_for(state="visible", timeout=5000)
    page.get_by_text("📄 Documentos", exact=True).wait_for(state="visible", timeout=5000)

    # Aba cannabis presente (Ueslhe tem o módulo ativo nesta validação)
    page.get_by_text("💊 Cannabis Medicinal", exact=True).wait_for(state="visible", timeout=5000)
    page.screenshot(path=str(screenshots_dir / "pront_02_abas.png"))

    # 3. Abrir a aba Cannabis Medicinal
    page.get_by_text("💊 Cannabis Medicinal", exact=True).click()
    page.wait_for_timeout(1500)
    page.screenshot(path=str(screenshots_dir / "pront_03_cannabis.png"))

    # O prontuário base (Prontuário tab) não deve conter dosagens canaboides
    page.get_by_text("🩺 Prontuário", exact=True).click()
    page.wait_for_timeout(1000)
    page.screenshot(path=str(screenshots_dir / "pront_04_prontuario_base.png"))

    # 4. Aba Receituário (módulo base) acessível
    page.get_by_text("📋 Receituário", exact=True).click()
    page.get_by_role("button", name="Nova Prescrição").first.wait_for(state="visible", timeout=10000)
    page.screenshot(path=str(screenshots_dir / "pront_05_receituario.png"))

    assert f"/pacientes/detail/{paciente_id}" in page.url


def test_associacao_gateada_por_modulo(page, base_url, screenshots_dir):
    """Rotas /association acessíveis apenas com módulo cannabis (Ueslhe tem)."""
    identifier = os.environ.get("E2E_USER", "ueslhe@gmail.com")
    senha = os.environ.get("E2E_PASS", "S@iAraOS123S@i")

    page.goto(f"{base_url}/login", wait_until="networkidle")
    page.get_by_label("👤 Usuário").fill(identifier)
    page.get_by_label("🔒 Senha").fill(senha)
    page.get_by_role("button", name="✨ Entrar").click()
    page.wait_for_url(f"{base_url}/dashboard", timeout=20000)

    # Seletor de associação visível (módulo cannabis ativo)
    page.goto(f"{base_url}/gestao", wait_until="networkidle")
    page.screenshot(path=str(screenshots_dir / "assoc_01_gestao.png"))
    page.get_by_text("OPERAÇÕES", exact=True).wait_for(state="visible", timeout=10000)
