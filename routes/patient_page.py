"""Página do Paciente — dashboard servido em /paciente.

Acesso por código (OTP) no WhatsApp. O HTML/JS vive em
`static/paciente.html` (mesmo padrão do /agendar) e consome apenas a API do
próprio SIAP (mesma origem):

  * Início        — resumo, indicadores, próximas consultas, últimos exames/evoluções
  * Prontuário    — linha do tempo curada (consultas, evoluções, prescrições)
  * Exames        — resultados laboratoriais, imagens/laudos e gráfico de tendência
  * Documentos    — documentos, laudos e relatórios para download seguro
  * Medicações    — prescrições ativas e históricas
  * Escalas       — PHQ-9, GAD-7, Beck, SNAP-IV
  * Como estou hoje — check-in de sintomas + observação por áudio
"""

import secrets
from pathlib import Path

from flask import Blueprint, Response, current_app, g

patient_page_bp = Blueprint("patient_page", __name__)


@patient_page_bp.route("/paciente", methods=["GET"])
def patient_page():
    arquivo = Path(current_app.root_path) / "static" / "paciente.html"
    try:
        html = arquivo.read_text(encoding="utf-8")
    except OSError:
        current_app.logger.exception("patient_page: falha ao ler %s", arquivo)
        return Response(
            "Página do paciente indisponível no momento.",
            status=503,
            mimetype="text/plain; charset=utf-8",
        )

    # CSP (P0-05) sem 'unsafe-inline': o HTML é estático, então geramos o
    # nonce aqui e o aplicamos a todos os <script>. O mesmo valor vai para o
    # header via `g.csp_nonce` (security_config.add_security_headers).
    nonce = secrets.token_urlsafe(16)
    g.csp_nonce = nonce
    html = html.replace("<script", f'<script nonce="{nonce}"')

    resp = Response(html, mimetype="text/html")
    resp.headers["Cache-Control"] = "no-store"
    return resp
