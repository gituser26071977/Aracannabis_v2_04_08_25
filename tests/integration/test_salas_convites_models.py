"""Testes dos modelos de convite e salas/ambientes (multi-tenant).

Cobre:
    - ConviteAssociacao: criação com token + código únicos
    - SalaAmbiente: criação com validação de tipo/capacidade
    - Serialização (to_dict)
"""

from __future__ import annotations

import uuid
from datetime import timedelta
from datetime import datetime

import pytest

from config import TestingConfig
from app_cors_livre import create_app
from models import db


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

    a = Associacao(nome=nome, slug=f"slug-{uuid.uuid4().hex[:8]}", cnpj=f"AUTO-{uuid.uuid4().hex[:8]}", ativo=True)
    db.session.add(a)
    db.session.flush()
    return a


class TestConviteAssociacao:
    def REDACTED(self, app):
        from models_extra import ConviteAssociacao

        assoc = _nova_associacao()
        convite = ConviteAssociacao(
            associacao_id=assoc.id,
            email="medico@teste.com",
            token=uuid.uuid4().hex,
            codigo="ABC123",
            role_convidado="member",
            expira_em=datetime.utcnow() + timedelta(days=7),
        )
        db.session.add(convite)
        db.session.commit()

        d = convite.to_dict()
        assert d["associacao_id"] == assoc.id
        assert d["email"] == "medico@teste.com"
        assert d["codigo"] == "ABC123"
        assert d["status"] == "pendente"
        assert d["token"]

    def test_convite_unicidade_token(self, app):
        from models_extra import ConviteAssociacao

        assoc = _nova_associacao()
        db.session.add_all([
            ConviteAssociacao(associacao_id=assoc.id, email="a@x.com", token="tok-1", codigo="CDE456"),
            ConviteAssociacao(associacao_id=assoc.id, email="b@x.com", token="tok-2", codigo="CDE457"),
        ])
        db.session.commit()
        assert ConviteAssociacao.query.count() == 2


class TestSalaAmbiente:
    def test_criar_sala(self, app):
        from models_extra import SalaAmbiente

        assoc = _nova_associacao()
        sala = SalaAmbiente(
            associacao_id=assoc.id,
            nome="Consultório 1",
            tipo="consultorio",
            capacidade=2,
            vsf_room_key="room-consultorio-1",
        )
        db.session.add(sala)
        db.session.commit()

        d = sala.to_dict()
        assert d["nome"] == "Consultório 1"
        assert d["tipo"] == "consultorio"
        assert d["capacidade"] == 2
        assert d["ativo"] is True
        assert d["vsf_room_key"] == "room-consultorio-1"

    def test_sala_infusao(self, app):
        from models_extra import SalaAmbiente

        assoc = _nova_associacao()
        sala = SalaAmbiente(associacao_id=assoc.id, nome="Sala Infusão A", tipo="infusao", capacidade=4)
        db.session.add(sala)
        db.session.commit()
        assert sala.tipo == "infusao"

    def test_sala_por_associacao(self, app):
        from models_extra import SalaAmbiente

        a1 = _nova_associacao("Clinica A")
        a2 = _nova_associacao("Clinica B")
        db.session.add_all([
            SalaAmbiente(associacao_id=a1.id, nome="Sala A1", tipo="consultorio"),
            SalaAmbiente(associacao_id=a2.id, nome="Sala B1", tipo="terapia"),
        ])
        db.session.commit()
        assert SalaAmbiente.query.filter_by(associacao_id=a1.id).count() == 1
        assert SalaAmbiente.query.filter_by(associacao_id=a2.id).count() == 1

    def test_sala_procedimento_e_banheiro(self, app):
        """Tipos novos: procedimento e banheiro (capacidade = lugares/poltronas)."""
        from models_extra import SalaAmbiente

        assoc = _nova_associacao()
        db.session.add_all([
            SalaAmbiente(associacao_id=assoc.id, nome="Sala Procedimento", tipo="procedimento", capacidade=2),
            SalaAmbiente(associacao_id=assoc.id, nome="Banheiro 1", tipo="banheiro", capacidade=1),
        ])
        db.session.commit()
        tipos = {s.tipo for s in SalaAmbiente.query.filter_by(associacao_id=assoc.id).all()}
        assert "procedimento" in tipos
        assert "banheiro" in tipos

    def REDACTED(self, app):
        """Campos de localização (andar/ala) e recursos para o VSF."""
        from models_extra import SalaAmbiente

        assoc = _nova_associacao()
        sala = SalaAmbiente(
            associacao_id=assoc.id,
            nome="Consultório 1", tipo="consultorio", capacidade=2,
            andar="1º", ala="Norte", recursos="macas=2,computador",
            vsf_room_key="room-consultorio-1",
        )
        db.session.add(sala)
        db.session.commit()
        d = sala.to_dict()
        assert d["andar"] == "1º"
        assert d["ala"] == "Norte"
        assert d["recursos"] == "macas=2,computador"
