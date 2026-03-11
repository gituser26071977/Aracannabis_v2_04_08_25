#!/usr/bin/env python3
"""
Script para limpar usuários do banco de dados SIAP

Mantém apenas:
- Admin: abholzwarth@gmail.com
- Paciente de teste: paciente.teste@example.com
"""

import sys
import os

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_cors_livre import create_app
from models import db, Profissional, Paciente

def limpar_usuarios():
    """Limpa usuários do banco, mantendo apenas admin e paciente de teste"""
    
    app = create_app()
    
    with app.app_context():
        print("🧹 Iniciando limpeza de usuários...\n")
        
        # 1. Atualizar admin
        print("📝 Atualizando admin...")
        admin = Profissional.query.get(1)
        if admin:
            admin.email = 'abholzwarth@gmail.com'
            admin.usuario = 'abholzwarth'
            db.session.commit()
            print(f"   ✅ Admin atualizado: {admin.usuario} ({admin.email})")
        else:
            print("   ⚠️ Admin ID=1 não encontrado!")
        
        # 2. Contar antes
        print("\n📊 ANTES:")
        total_prof_antes = Profissional.query.count()
        total_pac_antes = Paciente.query.count()
        print(f"   Profissionais: {total_prof_antes}")
        print(f"   Pacientes: {total_pac_antes}")
        
        # 3. Deletar profissionais extras (mantém só ID 1)
        print("\n🗑️ Deletando profissionais extras...")
        deleted_prof = Profissional.query.filter(Profissional.id != 1).delete()
        db.session.commit()
        print(f"   ✅ {deleted_prof} profissional(is) deletado(s)")
        
        # 4. Deletar pacientes que não são o de teste
        print("\n🗑️ Deletando pacientes extras...")
        
        # Primeiro, buscar IDs dos pacientes a deletar
        pacientes_para_deletar = Paciente.query.filter(
            (Paciente.email == None) | (Paciente.email != 'paciente.teste@example.com')
        ).all()
        
        pacientes_ids = [p.id for p in pacientes_para_deletar]
        
        if pacientes_ids:
            print(f"   📋 Pacientes a deletar: {pacientes_ids}")
            
            # Deletar dependências primeiro (membros_associacao, consultas, prescricoes, etc)
            print("   🔗 Deletando dependências...")
            
            # Importar modelos necessários
            from association.models import Membro
            
            # Deletar membros de associação vinculados
            deleted_membros = Membro.query.filter(
                Membro.paciente_id.in_(pacientes_ids)
            ).delete(synchronize_session=False)
            
            if deleted_membros > 0:
                print(f"      - {deleted_membros} membro(s) de associação deletado(s)")
            
            db.session.commit()
            
            # Agora deletar os pacientes
            deleted_pac = Paciente.query.filter(Paciente.id.in_(pacientes_ids)).delete(synchronize_session=False)
            db.session.commit()
            print(f"   ✅ {deleted_pac} paciente(s) deletado(s)")
        else:
            print("   ℹ️ Nenhum paciente para deletar")

        
        # 5. Contar depois
        print("\n📊 DEPOIS:")
        total_prof_depois = Profissional.query.count()
        total_pac_depois = Paciente.query.count()
        print(f"   Profissionais: {total_prof_depois}")
        print(f"   Pacientes: {total_pac_depois}")
        
        # 6. Mostrar usuários restantes
        print("\n👥 USUÁRIOS MANTIDOS:")
        print("\n📋 Profissionais:")
        for prof in Profissional.query.all():
            print(f"   ID {prof.id}: {prof.usuario} ({prof.email}) - Role: {prof.role}")
        
        print("\n🏥 Pacientes:")
        for pac in Paciente.query.all():
            print(f"   ID {pac.id}: {pac.nome} ({pac.email or 'sem email'}) - CPF: {pac.cpf}")
        
        print("\n✅ Limpeza concluída com sucesso!")

if __name__ == '__main__':
    try:
        limpar_usuarios()
    except Exception as e:
        print(f"\n❌ Erro durante limpeza: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
