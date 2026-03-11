"""
Script de teste manual de isolamento multi-tenant
"""
from app_cors_livre import create_app
from models import db, Profissional, Paciente
from association.models import Associacao
from models_extra import UsuarioAssociacao
from services.db_tools import DatabaseTools
from datetime import date
from werkzeug.security import generate_password_hash

def main():
    app = create_app()
    
    with app.app_context():
        print("🧪 Teste de Isolamento Multi-Tenant")
        print("="*60)
        
        # 1. Criar associações
        print("\n1️⃣ Criando associações...")
        assoc_a = Associacao.query.filter_by(cnpj="11111111111111").first()
        if not assoc_a:
            assoc_a = Associacao(nome="Clínica A - Teste", cnpj="11111111111111", email="a@test.com")
            db.session.add(assoc_a)
        
        assoc_b = Associacao.query.filter_by(cnpj="22222222222222").first()
        if not assoc_b:
            assoc_b = Associacao(nome="Clínica B - Teste", cnpj="22222222222222", email="b@test.com")
            db.session.add(assoc_b)
        
        db.session.commit()
        print(f"✅ Associação A: ID={assoc_a.id}, Nome={assoc_a.nome}")
        print(f"✅ Associação B: ID={assoc_b.id}, Nome={assoc_b.nome}")
        
        # 2. Criar profissionais
        print("\n2️⃣ Criando profissionais...")
        prof_a = Profissional.query.filter_by(usuario="test_prof_a").first()
        if not prof_a:
            prof_a = Profissional(
                nome="Dr. Teste A",
                crm="111111",
                uf_crm="SP",
                usuario="test_prof_a",
                senha=generate_password_hash("test"),
                email="profa@test.com",
                status_cadastro="aprovado"
            )
            db.session.add(prof_a)
        
        prof_b = Profissional.query.filter_by(usuario="test_prof_b").first()
        if not prof_b:
            prof_b = Profissional(
                nome="Dr. Teste B",
                crm="222222",
                uf_crm="RJ",
                usuario="test_prof_b",
                senha=generate_password_hash("test"),
                email="profb@test.com",
                status_cadastro="aprovado"
            )
            db.session.add(prof_b)
        
        db.session.commit()
        print(f"✅ Profissional A: ID={prof_a.id}, Nome={prof_a.nome}")
        print(f"✅ Profissional B: ID={prof_b.id}, Nome={prof_b.nome}")
        
        # 3. Vincular profissionais às associações
        print("\n3️⃣ Vinculando profissionais às associações...")
        link_a = UsuarioAssociacao.query.filter_by(profissional_id=prof_a.id, associacao_id=assoc_a.id).first()
        if not link_a:
            link_a = UsuarioAssociacao(
                profissional_id=prof_a.id,
                associacao_id=assoc_a.id,
                role="admin",
                status="active"
            )
            db.session.add(link_a)
        
        link_b = UsuarioAssociacao.query.filter_by(profissional_id=prof_b.id, associacao_id=assoc_b.id).first()
        if not link_b:
            link_b = UsuarioAssociacao(
                profissional_id=prof_b.id,
                associacao_id=assoc_b.id,
                role="admin",
                status="active"
            )
            db.session.add(link_b)
        
        db.session.commit()
        print("✅ Prof A vinculado à Associação A")
        print("✅ Prof B vinculado à Associação B")
        
        # 4. Criar pacientes
        print("\n4️⃣ Criando pacientes...")
        paciente_a = Paciente.query.filter_by(cpf="11111111111").first()
        if not paciente_a:
            paciente_a = Paciente(
                associacao_id=assoc_a.id,
                profissional_responsavel_id=prof_a.id,
                nome="Paciente da Clínica A",
                data_nascimento=date(1990, 1, 1),
                cpf="11111111111"
            )
            db.session.add(paciente_a)
        
        paciente_b = Paciente.query.filter_by(cpf="22222222222").first()
        if not paciente_b:
            paciente_b = Paciente(
                associacao_id=assoc_b.id,
                profissional_responsavel_id=prof_b.id,
                nome="Paciente da Clínica B",
                data_nascimento=date(1985, 5, 15),
                cpf="22222222222"
            )
            db.session.add(paciente_b)
        
        db.session.commit()
        print(f"✅ Paciente A: ID={paciente_a.id}, Nome={paciente_a.nome}, Associação={paciente_a.associacao_id}")
        print(f"✅ Paciente B: ID={paciente_b.id}, Nome={paciente_b.nome}, Associação={paciente_b.associacao_id}")
        
        # 5. TESTES DE ISOLAMENTO
        print("\n" + "="*60)
        print("🧪 TESTES DE ISOLAMENTO MULTI-TENANT")
        print("="*60)
        
        # Teste 1: Prof A acessa seu próprio paciente
        print("\n✅ Teste 1: Prof A acessa SEU PRÓPRIO paciente...")
        db_tools_a = DatabaseTools(profissional_id=prof_a.id, associacao_id=assoc_a.id)
        resultado = db_tools_a.buscar_paciente(paciente_a.id)
        if resultado.get("nome") == "Paciente da Clínica A":
            print(f"   ✅ PASSOU: Prof A conseguiu acessar paciente {paciente_a.id}")
        else:
            print("   ❌ FALHOU: Prof A não conseguiu acessar seu próprio paciente!")
            print(f"   Resultado: {resultado}")
        
        # Teste 2: Prof A tenta acessar paciente de outra associação
        print(f"\n❌ Teste 2: Prof A tenta acessar paciente da CLÍNICA B (ID={paciente_b.id})...")
        resultado = db_tools_a.buscar_paciente(paciente_b.id)
        if resultado.get("error") or not resultado.get("nome"):
            print("   ✅ PASSOU: Acesso BLOQUEADO corretamente!")
            print(f"   Resultado: {resultado}")
        else:
            print("   🔴 FALHOU CRITICAMENTE: Prof A conseguiu acessar paciente de outra associação!")
            print(f"   Resultado: {resultado}")
            print("   ⚠️ VAZAMENTO DE DADOS DETECTADO!")
        
        # Teste 3: Prof B acessa seu próprio paciente
        print("\n✅ Teste 3: Prof B acessa SEU PRÓPR IO paciente...")
        db_tools_b = DatabaseTools(profissional_id=prof_b.id, associacao_id=assoc_b.id)
        resultado = db_tools_b.buscar_paciente(paciente_b.id)
        if resultado.get("nome") == "Paciente da Clínica B":
            print(f"   ✅ PASSOU: Prof B conseguiu acessar paciente {paciente_b.id}")
        else:
            print("   ❌ FALHOU: Prof B não conseguiu acessar seu próprio paciente!")
            print(f"   Resultado: {resultado}")
        
        # Teste 4: Prof B tenta acessar paciente de outra associação
        print(f"\n❌ Teste 4: Prof B tenta acessar paciente da CLÍNICA A (ID={paciente_a.id})...")
        resultado = db_tools_b.buscar_paciente(paciente_a.id)
        if resultado.get("error") or not resultado.get("nome"):
            print("   ✅ PASSOU: Acesso BLOQUEADO corretamente!")
            print(f"   Resultado: {resultado}")
        else:
            print("   🔴 FALHOU CRITICAMENTE: Prof B conseguiu acessar paciente de outra associação!")
            print(f"   Resultado: {resultado}")
            print("   ⚠️ VAZAMENTO DE DADOS DETECTADO!")
        
        print("\n" + "="*60)
        print("🏁 TESTES CONCLUÍDOS")
        print("="*60)

if __name__ == "__main__":
    main()
