"""Testes da hierarquia física da unidade (instalação → andar/setor → espaço).

Espelha o modelo Facility → Sector → Bed do CareOS e é compatível com o
VSF (vsf_facility_key/vsf_room_key). Escala para hospitais (UTI, alas,
centro cirúrgico, leitos).
"""

from __future__ import annotations

import uuid

import pytest

from config import TestingConfig
from app_cors_livre import create_app
from models import db
from models_extra import AndarSetor, SalaAmbiente, UnidadeFisica


@pytest.fixture
def app():
    a = create_app(TestingConfig)
    with a.app_context():
        db.create_all()
    yield a
    with a.app_context():
        db.session.remove()
        db.drop_all()


def _nova_associacao(nome="Clinica Teste"):
    from association.models import Associacao

    a = Associacao(
        nome=nome,
        slug=f"slug-{uuid.uuid4().hex[:8]}",
        cnpj=f"AUTO-{uuid.uuid4().hex[:8]}",
        ativo=True,
    )
    db.session.add(a)
    db.session.flush()
    return a


class TestUnidadeFisica:
    def test_criar_hospital(self, app):
        assoc = _nova_associacao()
        unidade = UnidadeFisica(
            associacao_id=assoc.id, nome="Hospital Central", tipo="hospital",
            possui_uti=True, possui_centro_cirurgico=True,
            vsf_facility_key="fac-001",
        )
        db.session.add(unidade)
        db.session.commit()
        d = unidade.to_dict()
        assert d["tipo"] == "hospital"
        assert d["possui_uti"] is True
        assert d["vsf_facility_key"] == "fac-001"

    def test_criar_consultorio(self, app):
        assoc = _nova_associacao()
        unidade = UnidadeFisica(associacao_id=assoc.id, nome="Consultório A", tipo="consultorio")
        db.session.add(unidade)
        db.session.commit()
        assert unidade.tipo == "consultorio"


class TestAndarSetor:
    def test_criar_uti_com_leitos(self, app):
        assoc = _nova_associacao()
        hospital = UnidadeFisica(associacao_id=assoc.id, nome="Hosp", tipo="hospital", possui_uti=True)
        db.session.add(hospital)
        db.session.flush()

        uti = AndarSetor(associacao_id=assoc.id, unidade_id=hospital.id, nome="UTI 1", tipo="uti")
        db.session.add(uti)
        db.session.flush()

        # leitos da UTI como espaços (tipo procedimento/outro com capacidade 1 = leito)
        leito1 = SalaAmbiente(associacao_id=assoc.id, nome="Leito UTI-01", tipo="procedimento",
                              capacidade=1, unidade_id=hospital.id, andar_setor_id=uti.id,
                              vsf_room_key="room-uti-01")
        db.session.add(leito1)
        db.session.commit()

        assert uti.tipo == "uti"
        assert leito1.andar_setor_id == uti.id
        assert leito1.vsf_room_key == "room-uti-01"

    def test_sub_setor_ala(self, app):
        assoc = _nova_associacao()
        hospital = UnidadeFisica(associacao_id=assoc.id, nome="Hosp", tipo="hospital")
        db.session.add(hospital)
        db.session.flush()
        andar = AndarSetor(associacao_id=assoc.id, unidade_id=hospital.id, nome="Andar 2", tipo="andar")
        db.session.add(andar)
        db.session.flush()
        ala = AndarSetor(associacao_id=assoc.id, unidade_id=hospital.id, nome="Ala Norte",
                         tipo="ala", parent_id=andar.id)
        db.session.add(ala)
        db.session.commit()
        assert ala.parent_id == andar.id


class TestEndpointsUnidade:
    def test_criar_unidade_api(self, app):
        from models import Profissional
        from models_extra import UsuarioAssociacao
        from werkzeug.security import generate_password_hash

        client = app.test_client()
        suf = uuid.uuid4().hex[:6]
        usuario = f"admin.u{suf}"
        email = f"{usuario}@x.com"
        with app.app_context():
            assoc = _nova_associacao()
            admin = Profissional(
                nome="Admin U", usuario=usuario, email=email,
                crm=f"CRM-{suf.upper()}", uf_crm="SE", senha=generate_password_hash("Teste@123456"),
                role="admin", perfil_acesso="administrativo", status_cadastro="aprovado",
            )
            db.session.add(admin)
            db.session.flush()
            db.session.add(UsuarioAssociacao(profissional_id=admin.id, associacao_id=assoc.id,
                                             role="admin", status="active"))
            db.session.commit()
            admin_id = admin.id

        # Gera o token diretamente (evita rate-limit de login nos testes)
        from flask_jwt_extended import create_access_token

        tok = create_access_token(identity=str(admin_id))
        headers = {"Authorization": f"Bearer {tok}"}

        # cria hospital
        r = client.post("/api/unidade", json={"nome": "Hospital Teste", "tipo": "hospital", "possui_uti": True}, headers=headers)
        assert r.status_code == 201, r.data
        unidade_id = r.get_json()["unidade"]["id"]

        # cria UTI
        r = client.post(f"/api/unidade/{unidade_id}/andares", json={"nome": "UTI 1", "tipo": "uti"}, headers=headers)
        assert r.status_code == 201, r.data
        andar_id = r.get_json()["andar"]["id"]

        # cria espaço na UTI
        r = client.post("/api/salas/ambientes", json={
            "nome": "Leito UTI-01", "tipo": "procedimento", "capacidade": 1,
            "unidade_id": unidade_id, "andar_setor_id": andar_id, "vsf_room_key": "room-uti-01",
        }, headers=headers)
        assert r.status_code == 201, r.data

        # árvore completa
        r = client.get(f"/api/unidade/{unidade_id}", headers=headers)
        assert r.status_code == 200, r.data
        body = r.get_json()
        assert body["unidade"]["nome"] == "Hospital Teste"
        assert len(body["andares"]) == 1
        assert body["andares"][0]["nome"] == "UTI 1"
        assert len(body["andares"][0]["espacos"]) == 1
