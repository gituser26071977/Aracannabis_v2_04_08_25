"""E2E — Smoke test do frontend: navega por todas as rotas autenticadas.

Para cada rota: navega, aguarda render, captura erros de console e
pageerror. Falha se houver crash (pageerror) ou erro de rede/JS fatal.
"""
import os

# Rotas autenticadas principais (navegação real no app)
ROTAS = [
    ("/dashboard", "Dashboard"),
    ("/pacientes", "Lista de Pacientes"),
    ("/consultas", "Consultas"),
    ("/gestao", "Gestão"),
    ("/faturamento", "Financeiro"),
    ("/relatorios-financeiros", "Relatórios Financeiros"),
    ("/modulos", "Módulos"),
    ("/planos", "Planos"),
    ("/configuracao-prescricao", "Config. Receituário"),
    ("/configurar-unidade", "Config. Unidade"),
    ("/catalogo", "Catálogo"),
    ("/association", "Associação"),
    ("/association/stock", "Estoque"),
    ("/association/dispensation", "Dispensação"),
    ("/association/members", "Membros"),
    ("/certificacao-digital", "Certificação Digital"),
    ("/configuracao-ia", "Config. IA SDR"),
    ("/ai-config", "AI Config"),
    ("/ai-dashboard", "AI Dashboard"),
    ("/assistente-ia", "Assistente IA"),
    ("/onboarding-pacientes", "Onboarding Pacientes"),
    ("/admin", "Admin"),
]

# Erros considerados fatais (crash de render, JS throw)
ERROS_IGNORADOS = (
    "favicon",
    "Failed to load resource: the server responded with a status of 404",
    "net::ERR_ABORTED 404",
)


def _coleta_erros(page):
    erros = []
    page.on(
        "pageerror",
        lambda exc: erros.append(f"PAGEERROR: {exc}")
    )
    page.on(
        "console",
        lambda msg: erros.append(f"CONSOLE[{msg.type}]: {msg.text}")
        if msg.type == "error" else None,
    )
    page.on(
        "requestfailed",
        lambda req: erros.append(f"REQFAIL: {req.method} {req.url} :: {req.failure}")
    )
    return erros


def test_smoke_todas_rotas(page, base_url, screenshots_dir):
    identifier = os.environ.get("E2E_USER", "ueslhe@gmail.com")
    senha = os.environ.get("E2E_PASS", "S@iAraOS123S@i")

    # 1. Login
    page.goto(f"{base_url}/login", wait_until="networkidle")
    page.get_by_label("👤 Usuário").fill(identifier)
    page.get_by_label("🔒 Senha").fill(senha)
    page.get_by_role("button", name="✨ Entrar").click()
    page.wait_for_url(f"{base_url}/dashboard", timeout=20000)

    falhas = []

    for rota, nome in ROTAS:
        erros = _coleta_erros(page)
        try:
            page.goto(f"{base_url}{rota}", wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2000)
            page.screenshot(path=str(screenshots_dir / f"smoke_{rota.replace('/', '_') or '_home'}.png"))
        except Exception as e:
            falhas.append(f"{rota} ({nome}): NAVEGACAO -> {e}")
            continue

        # Filtrar erros ignorados (404 de favicon etc.)
        fatais = []
        for e in erros:
            if any(ig in e for ig in ERROS_IGNORADOS):
                continue
            if "net::ERR_CONNECTION_REFUSED" in e:
                fatais.append(e)
            elif e.startswith("PAGEERROR"):
                fatais.append(e)
            elif "CONSOLE[error]" in e and "Failed to load resource" not in e:
                fatais.append(e)

        if fatais:
            falhas.append(f"{rota} ({nome}): {'; '.join(fatais[:4])}")

    if falhas:
        raise AssertionError("\n".join(falhas))

    print(f"✔ {len(ROTAS)} rotas navegadas sem crash")
