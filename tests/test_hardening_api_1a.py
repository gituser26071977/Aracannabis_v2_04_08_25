"""
Testes do Programa de Hardening API-1A — Aracannabis SIAP.

Cobertura:
- HARDENING-1: Autenticação nos endpoints de exames
- HARDENING-2: Timestamps de audit em Evolucao
- HARDENING-3: Timestamps de audit em Prescricao
- HARDENING-6: Consistência do admin_required
"""
import pytest
import sys
import os
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_cors_livre import create_app
from config import TestingConfig
from models import db, Paciente, Profissional, Exame, Evolucao, Prescricao, CompartilhamentoPaciente
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Cria aplicação Flask com banco SQLite em memória para testes."""
    app = create_app(config_obj=TestingConfig)
    app.config.update({
        'JWT_SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Cliente de teste Flask."""
    return app.test_client()


@pytest.fixture
def admin_user(app):
    """Cria um usuário admin para testes."""
    with app.app_context():
        user = Profissional(
            nome='Admin Teste',
            email='admin@test.com',
            usuario='admin_test',
            senha=generate_password_hash('Admin@123'),
            crm='123456',
            uf_crm='SP',
            role='admin',
            status_cadastro='aprovado'
        )
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def prof_user(app):
    """Cria um profissional comum para testes."""
    with app.app_context():
        user = Profissional(
            nome='Profissional Teste',
            email='prof@test.com',
            usuario='prof_test',
            senha=generate_password_hash('Prof@123'),
            crm='654321',
            uf_crm='RJ',
            role='profissional',
            status_cadastro='aprovado'
        )
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def paciente(app, prof_user):
    """Cria um paciente vinculado ao profissional."""
    with app.app_context():
        p = Paciente(
            nome='Paciente Teste',
            data_nascimento=date(1990, 1, 15),
            profissional_responsavel_id=prof_user,
            cpf='12345678900'
        )
        db.session.add(p)
        db.session.commit()
        return p.id


@pytest.fixture
def exame(app, paciente, prof_user):
    """Cria um exame para o paciente."""
    with app.app_context():
        e = Exame(
            paciente_id=paciente,
            profissional_id=prof_user,
            data_exame=date(2025, 1, 15),
            tipo_exame='numerico',
            titulo='Hemoglobina',
            valor=13.5,
            unidade='g/dL'
        )
        db.session.add(e)
        db.session.commit()
        return e.id


@pytest.fixture
def token_admin(client, admin_user):
    """Obtém token JWT para admin."""
    resp = client.post('/api/auth/login', json={
        'usuario': 'admin_test',
        'senha': 'Admin@123'
    })
    return resp.get_json()['access_token']


@pytest.fixture
def token_prof(client, prof_user):
    """Obtém token JWT para profissional."""
    resp = client.post('/api/auth/login', json={
        'usuario': 'prof_test',
        'senha': 'Prof@123'
    })
    return resp.get_json()['access_token']


# ============================================================================
# HARDENING-1: Secure Exams API
# ============================================================================

class TestHardening1ExamsAuth:
    """Testes para verificar que endpoints de exames exigem autenticação."""

    def REDACTED(self, client, paciente):
        resp = client.get(f'/api/pacientes/{paciente}/exames')
        assert resp.status_code == 401

    def REDACTED(self, client, paciente, token_prof):
        resp = client.get(
            f'/api/pacientes/{paciente}/exames',
            headers={'Authorization': f'Bearer {token_prof}'}
        )
        assert resp.status_code == 200

    def REDACTED(self, client, exame):
        resp = client.get(f'/api/exames/{exame}')
        assert resp.status_code == 401

    def REDACTED(self, client, exame, token_prof):
        resp = client.get(
            f'/api/exames/{exame}',
            headers={'Authorization': f'Bearer {token_prof}'}
        )
        assert resp.status_code == 200

    def REDACTED(self, client, exame):
        resp = client.get(f'/api/exames/{exame}/imagens')
        assert resp.status_code == 401

    def REDACTED(self, client, exame):
        resp = client.get(f'/api/exames/{exame}/resultados')
        assert resp.status_code == 401

    def REDACTED(self, client):
        resp = client.post('/api/exames', data={
            'paciente_id': 1,
            'tipo_exame': 'texto',
            'titulo': 'Teste',
            'descricao': 'Desc'
        })
        assert resp.status_code == 401

    def REDACTED(self, client, exame):
        resp = client.put(f'/api/exames/{exame}', json={'tipo_exame': 'texto'})
        assert resp.status_code == 401

    def REDACTED(self, client, exame):
        resp = client.delete(f'/api/exames/{exame}')
        assert resp.status_code == 401

    def REDACTED(self, client, paciente):
        resp = client.get(f'/api/pacientes/{paciente}/exames/chartable')
        assert resp.status_code == 401

    def REDACTED(self, client):
        resp = client.get('/api/exames/nomes-unicos')
        assert resp.status_code == 401

    def REDACTED(self, client, app, paciente, exame, token_prof):
        """Profissional sem acesso ao paciente não deve ver o exame."""
        # Criar outro profissional
        with app.app_context():
            outro = Profissional(
                nome='Outro Prof',
                email='outro@test.com',
                usuario='outro_test',
                senha=generate_password_hash('Outro@123'),
                crm='111111',
                uf_crm='MG',
                role='profissional',
                status_cadastro='aprovado'
            )
            db.session.add(outro)
            db.session.commit()
            outro_id = outro.id

        # Login como outro profissional
        resp = client.post('/api/auth/login', json={
            'usuario': 'outro_test',
            'senha': 'Outro@123'
        })
        token_outro = resp.get_json()['access_token']

        resp = client.get(
            f'/api/exames/{exame}',
            headers={'Authorization': f'Bearer {token_outro}'}
        )
        assert resp.status_code == 403


# ============================================================================
# HARDENING-2 & HARDENING-3: Audit Timestamps
# ============================================================================

class TestHardening2e3AuditTimestamps:
    """Testes para verificar created_at e updated_at em Evolucao e Prescricao."""

    def test_evolucao_tem_created_at(self, app, paciente, prof_user):
        with app.app_context():
            evo = Evolucao(
                paciente_id=paciente,
                profissional_id=prof_user,
                data_evolucao=datetime(2025, 6, 1, 10, 0, 0),
                nota_evolucao='Evolução de teste'
            )
            db.session.add(evo)
            db.session.commit()

            assert evo.created_at is not None
            assert evo.updated_at is not None

    def REDACTED(self, app, paciente, prof_user):
        with app.app_context():
            evo = Evolucao(
                paciente_id=paciente,
                profissional_id=prof_user,
                data_evolucao=datetime(2025, 6, 1, 10, 0, 0),
                nota_evolucao='Evolução de teste'
            )
            db.session.add(evo)
            db.session.commit()

            d = evo.to_dict()
            assert 'created_at' in d
            assert 'updated_at' in d
            assert d['created_at'] is not None
            assert d['updated_at'] is not None

    def test_prescricao_tem_created_at(self, app, paciente, prof_user):
        with app.app_context():
            presc = Prescricao(
                paciente_id=paciente,
                profissional_id=prof_user,
                data_emissao=datetime(2025, 6, 1, 10, 0, 0),
                arquivo_path='/tmp/test.pdf',
                conteudo_json={'meds': []}
            )
            db.session.add(presc)
            db.session.commit()

            assert presc.created_at is not None
            assert presc.updated_at is not None

    def REDACTED(self, app, paciente, prof_user):
        with app.app_context():
            presc = Prescricao(
                paciente_id=paciente,
                profissional_id=prof_user,
                data_emissao=datetime(2025, 6, 1, 10, 0, 0),
                arquivo_path='/tmp/test.pdf',
                conteudo_json={'meds': []}
            )
            db.session.add(presc)
            db.session.commit()

            d = presc.to_dict()
            assert 'created_at' in d
            assert 'updated_at' in d
            assert d['created_at'] is not None
            assert d['updated_at'] is not None


# ============================================================================
# HARDENING-6: Admin Authorization Consistency
# ============================================================================

class TestHardening6AdminAuthConsistency:
    """Testes para verificar padronização do admin_required."""

    def REDACTED(self, client, token_admin):
        resp = client.get(
            '/api/admin/dashboard-stats',
            headers={'Authorization': f'Bearer {token_admin}'}
        )
        assert resp.status_code == 200

    def REDACTED(self, client, token_prof):
        resp = client.get(
            '/api/admin/dashboard-stats',
            headers={'Authorization': f'Bearer {token_prof}'}
        )
        assert resp.status_code == 403

    def REDACTED(self, client):
        resp = client.get('/api/admin/dashboard-stats')
        assert resp.status_code == 401

    def test_planos_admin_retorna_200(self, client, token_admin):
        resp = client.get(
            '/api/planos/admin',
            headers={'Authorization': f'Bearer {token_admin}'}
        )
        assert resp.status_code == 200

    def test_planos_prof_retorna_403(self, client, token_prof):
        resp = client.get(
            '/api/planos/admin',
            headers={'Authorization': f'Bearer {token_prof}'}
        )
        assert resp.status_code == 403

    def REDACTED(self, client, token_admin):
        resp = client.post(
            '/api/billing/plans',
            headers={'Authorization': f'Bearer {token_admin}'},
            json={'nome': 'Plano Teste', 'preco_mensal': 99.9}
        )
        assert resp.status_code in (201, 400)  # 400 se validação adicional falhar

    def REDACTED(self, client, token_prof):
        resp = client.post(
            '/api/billing/plans',
            headers={'Authorization': f'Bearer {token_prof}'},
            json={'nome': 'Plano Teste', 'preco_mensal': 99.9}
        )
        assert resp.status_code == 403

    def REDACTED(self, client, token_admin):
        resp = client.get(
            '/api/admin/logs-atividade',
            headers={'Authorization': f'Bearer {token_admin}'}
        )
        assert resp.status_code == 200

    def REDACTED(self, client, token_prof):
        resp = client.get(
            '/api/admin/logs-atividade',
            headers={'Authorization': f'Bearer {token_prof}'}
        )
        assert resp.status_code == 403


# ============================================================================
# Contagem de testes
# ============================================================================
# HARDENING-1: 12 testes
# HARDENING-2+3: 4 testes
# HARDENING-6: 9 testes
# Total: 25 testes
