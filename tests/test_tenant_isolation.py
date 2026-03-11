"""
Teste de Isolamento Multi-Tenant nos Agentes
CRÍTICO: Este teste valida que agentes não vazam dados entre associações diferentes
"""
import pytest
from app_cors_livre import create_app
from models import db, Profissional, Paciente
from association.models import Associacao
from models_extra import UsuarioAssociacao
from services.db_tools import DatabaseTools
from datetime import datetime, date
from werkzeug.security import generate_password_hash
from flask import g

@pytest.fixture
def app():
    """Cria aplicação Flask para testes"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_isolamento_multi_tenant_database_tools(app):
    """
    TESTE CRÍTICO: Valida que DatabaseTools bloqueia acesso a pacientes de outras associações
    """
    with app.app_context():
        # 1. Criar duas associações diferentes
        assoc_a = Associacao(nome="Clínica A", cnpj="11111111111111")
        assoc_b = Associacao(nome="Clínica B", cnpj="22222222222222")
        db.session.add_all([assoc_a, assoc_b])
        db.session.commit()
        
        # 2. Criar profissionais
        prof_a = Profissional(
            nome="Dr. A",
            crm="123456",
            uf_crm="SP",
            usuario="dra",
            senha=generate_password_hash("test"),
            email="dra@test.com",
            status_cadastro="aprovado"
        )
        prof_b = Profissional(
            nome="Dr. B",
            crm="654321",
            uf_crm="RJ",
            usuario="drb",
            senha=generate_password_hash("test"),
            email="drb@test.com",
            status_cadastro="aprovado"
        )
        db.session.add_all([prof_a, prof_b])
        db.session.commit()
        
        # 3. Vincular profissionais às associações
        link_a = UsuarioAssociacao(
            profissional_id=prof_a.id,
            associacao_id=assoc_a.id,
            role="admin",
            status="active"
        )
        link_b = UsuarioAssociacao(
            profissional_id=prof_b.id,
            associacao_id=assoc_b.id,
            role="admin",
            status="active"
        )
        db.session.add_all([link_a, link_b])
        db.session.commit()
        
        # 4. Criar pacientes (cada profissional cria 1)
        paciente_a = Paciente(
            associacao_id=assoc_a.id,  # Pertence à Clínica A
            profissional_responsavel_id=prof_a.id,
            nome="Paciente A",
            data_nascimento=date(1990, 1, 1),
            cpf="11111111111"
        )
        paciente_b = Paciente(
            associacao_id=assoc_b.id,  # Pertence à Clínica B
            profissional_responsavel_id=prof_b.id,
            nome="Paciente B",
            data_nascimento=date(1985, 5, 15),
            cpf="22222222222"
        )
        db.session.add_all([paciente_a, paciente_b])
        db.session.commit()
        
        # 5. TESTE: Prof A tenta acessar paciente de Prof B
        db_tools_a = DatabaseTools(profissional_id=prof_a.id, associacao_id=assoc_a.id)
        
        # ✅ Prof A DEVE conseguir acessar seu próprio paciente
        resultado_a_proprio = db_tools_a.buscar_paciente(paciente_a.id)
        assert resultado_a_proprio["nome"] == "Paciente A", "Prof A deve acessar seu próprio paciente"
        
        # ❌ Prof A NÃO DEVE conseguir acessar paciente de outra associação
        resultado_a_outro = db_tools_a.buscar_paciente(paciente_b.id)
        assert resultado_a_outro.get("error") or resultado_a_outro.get("nome") is None, \
            "FALHA CRÍTICA: Prof A conseguiu acessar paciente da Clínica B!"
        
        # 6. TESTE: Prof B tenta acessar paciente de Prof A
        db_tools_b = DatabaseTools(profissional_id=prof_b.id, associacao_id=assoc_b.id)
        
        # ✅ Prof B DEVE conseguir acessar seu próprio paciente
        resultado_b_proprio = db_tools_b.buscar_paciente(paciente_b.id)
        assert resultado_b_proprio["nome"] == "Paciente B", "Prof B deve acessar seu próprio paciente"
        
        # ❌ Prof B NÃO DEVE conseguir acessar paciente de outra associação
        resultado_b_outro = db_tools_b.buscar_paciente(paciente_a.id)
        assert resultado_b_outro.get("error") or resultado_b_outro.get("nome") is None, \
            "FALHA CRÍTICA: Prof B conseguiu acessar paciente da Clínica A!"
        
        print("✅ TESTE PASSOU: Isolamento multi-tenant funcionando corretamente!")

def test_criar_paciente_sem_associacao_id(app):
    """
    TESTE: Validar que não é possível criar paciente sem associacao_id em ambiente multi-tenant
    """
    with app.app_context():
        assoc = Associacao(nome="Clínica Teste", cnpj="33333333333333")
        db.session.add(assoc)
        db.session.commit()
        
        prof = Profissional(
            nome="Dr. Teste",
            crm="999999",
            uf_crm="SP",
            usuario="drtest",
            senha=generate_password_hash("test"),
            email="test@test.com",
            status_cadastro="aprovado"
        )
        db.session.add(prof)
        db.session.commit()
        
        # Tentar criar paciente SEM associacao_id
        paciente_sem_assoc = Paciente(
            profissional_responsavel_id=prof.id,
            # associacao_id=None,  # ❌ Não definido
            nome="Paciente Sem Associação",
            data_nascimento=date(2000, 1, 1)
        )
        db.session.add(paciente_sem_assoc)
        db.session.commit()
        
        # Validar que paciente foi criado MAS será bloqueado por DatabaseTools
        db_tools = DatabaseTools(profissional_id=prof.id, associacao_id=assoc.id)
        resultado = db_tools.buscar_paciente(paciente_sem_assoc.id)
        
        # Deve falhar porque paciente não tem associacao_id
        assert resultado.get("error") or resultado.get("nome") is None, \
            "Paciente sem associacao_id deveria ser bloqueado"
        
        print("✅ TESTE PASSOU: Pacientes sem associacao_id são bloqueados!")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
