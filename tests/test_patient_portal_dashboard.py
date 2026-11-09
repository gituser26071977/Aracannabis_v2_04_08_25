"""Testes do dashboard do paciente (agregação, exames/documentos e downloads).

Cobrem:
  * endpoints agregados do portal respondendo 200 com JWT de paciente;
  * isolamento: token de outro paciente NÃO baixa documento alheio (403);
  * contenção de path no download.
"""

from __future__ import annotations

import datetime as dt
import re

import pytest
from flask_jwt_extended import create_access_token

from app_cors_livre import create_app
from config import TestingConfig
from models import (
    db,
    Paciente,
    Consulta,
    Evolucao,
    Prescricao,
    Exame,
    ExameImagem,
    ExameLabResultado,
)


@pytest.fixture()
def ctx(tmp_path):
    app = create_app(config_obj=TestingConfig)
    app.config["UPLOAD_FOLDER_EXAMES"] = str(tmp_path)

    with app.app_context():
        db.create_all()

        p = Paciente(
            nome="Maria Teste", cpf="111.222.333-44", telefone="5511999999999",
            condicao_medica="Ansiedade",
        )
        db.session.add(p)
        db.session.flush()

        ex = Exame(
            paciente_id=p.id, data_exame=dt.date(2026, 1, 1),
            tipo_exame="numerico", titulo="Hemoglobina", valor=13.5, unidade="g/dL",
        )
        db.session.add(ex)
        db.session.flush()
        db.session.add(ExameLabResultado(
            exame_id=ex.id, teste_nome="Leucócitos", valor=7000,
            unidade="/mm3", valor_referencia="4000-11000",
        ))

        nome_arq = "abcd_laudo_exame.pdf"
        (tmp_path / nome_arq).write_bytes(b"%PDF-1.4 exame")
        img = ExameImagem(
            exame_id=ex.id, arquivo_nome="laudo_exame.pdf",
            arquivo_caminho=nome_arq, laudo="Dentro da normalidade",
        )
        db.session.add(img)

        receita = "presc_1.pdf"
        (tmp_path / receita).write_bytes(b"%PDF-1.4 receita")
        presc = Prescricao(
            paciente_id=p.id, data_emissao=dt.datetime(2026, 2, 1),
            arquivo_path=receita,
            conteudo_json={"medicamentos": [{"nome": "CBD 200mg", "posologia": "2 gotas"}]},
        )
        db.session.add(presc)

        db.session.add(Consulta(
            paciente_id=p.id, data_hora=dt.datetime(2026, 3, 1, 10, 0),
            tipo_consulta="telemedicina", status="agendada",
        ))
        db.session.add(Evolucao(
            paciente_id=p.id, data_evolucao=dt.datetime(2026, 2, 20),
            nota_evolucao="Paciente estável.", avaliacao="Boa resposta",
            plano="Manter dose", sinais_vitais={"pa": "120/80"},
        ))
        db.session.commit()

        impl_id = img.id
        presc_id = presc.id
        paciente_tok = create_access_token(
            identity=str(p.id), additional_claims={"user_type": "patient"}
        )
        outro_tok = create_access_token(
            identity="999999", additional_claims={"user_type": "patient"}
        )

    app.config["PATIENT_TOK"] = paciente_tok
    app.config["OUTRO_TOK"] = outro_tok
    app.config["IMPL_ID"] = impl_id
    app.config["PRESC_ID"] = presc_id
    return app


def _hdr(app, key):
    return {"Authorization": f"Bearer {app.config[key]}"}


ROTAS = [
    "/api/patient-portal/me/dashboard",
    "/api/patient-portal/me/exames",
    "/api/patient-portal/me/documentos",
    "/api/patient-portal/me/prontuario",
    "/api/patient-portal/me/prescricoes",
    "/api/patient-portal/me/evolucoes",
    "/api/patient-portal/me/stats",
    "/api/patient-portal/me/rastreios",
]


def test_endpoints_do_portal_respondem(ctx):
    app = ctx
    client = app.test_client()
    for rota in ROTAS:
        resp = client.get(rota, headers=_hdr(app, "PATIENT_TOK"))
        assert resp.status_code == 200, (rota, resp.status_code, resp.get_data(as_text=True))


def test_dashboard_agrega_dados(ctx):
    app = ctx
    client = app.test_client()
    body = client.get("/api/patient-portal/me/dashboard",
                      headers=_hdr(app, "PATIENT_TOK")).get_json()
    assert body["perfil"]["primeiro_nome"] == "Maria"
    assert body["indicadores"]["exames"] == 1
    assert body["prescricoes_ativas"][0]["medicamentos"][0]["nome"] == "CBD 200mg"


def test_exames_incluem_lab_e_imagem(ctx):
    app = ctx
    client = app.test_client()
    exames = client.get("/api/patient-portal/me/exames",
                        headers=_hdr(app, "PATIENT_TOK")).get_json()["exames"]
    assert exames[0]["resultados_lab"][0]["teste_nome"] == "Leucócitos"
    assert exames[0]["imagens"][0]["laudo"] == "Dentro da normalidade"


def test_documentos_agrega_categorias(ctx):
    app = ctx
    client = app.test_client()
    docs = client.get("/api/patient-portal/me/documentos",
                      headers=_hdr(app, "PATIENT_TOK")).get_json()["documentos"]
    tipos = {d["tipo"] for d in docs}
    assert {"exame_imagem", "prescricao"} <= tipos


def test_download_proprio_ok(ctx):
    app = ctx
    client = app.test_client()
    resp = client.get(
        f"/api/patient-portal/me/documentos/exame_imagem/{app.config['IMPL_ID']}/arquivo",
        headers=_hdr(app, "PATIENT_TOK"),
    )
    assert resp.status_code == 200
    assert resp.data.startswith(b"%PDF")


def test_download_de_outro_paciente_negado(ctx):
    app = ctx
    client = app.test_client()
    resp = client.get(
        f"/api/patient-portal/me/documentos/prescricao/{app.config['PRESC_ID']}/arquivo",
        headers=_hdr(app, "OUTRO_TOK"),
    )
    assert resp.status_code == 403


def test_download_tipo_desconhecido(ctx):
    app = ctx
    client = app.test_client()
    resp = client.get("/api/patient-portal/me/documentos/xyz/1/arquivo",
                      headers=_hdr(app, "PATIENT_TOK"))
    assert resp.status_code == 400


def test_pagina_paciente_aplica_nonce_do_csp(ctx):
    """A CSP não permite inline sem nonce: todos os <script> devem recebê-lo."""
    app = ctx
    client = app.test_client()
    resp = client.get("/paciente")
    assert resp.status_code == 200

    csp = resp.headers.get("Content-Security-Policy", "")
    match = re.search(r"nonce-([^']+)", csp)
    assert match, csp
    nonce = match.group(1)

    html = resp.get_data(as_text=True)
    assert html.count("<script") == html.count(f'nonce="{nonce}"')
    assert "cdn.jsdelivr.net" not in html
    assert "/static/vendor/chart.umd.min.js" in html
