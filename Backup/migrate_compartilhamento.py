#!/usr/bin/env python3
"""
Script de migração para implementar sistema de compartilhamento de pacientes
Adiciona:
- Campo profissional_responsavel_id na tabela pacientes
- Nova tabela compartilhamentos_pacientes
"""

import os
import sys
from sqlalchemy import text

# Adicionar o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_sem_ia import create_app
from models import db, Paciente, Profissional, CompartilhamentoPaciente

# Criar instância da aplicação
app = create_app()

def executar_migracao():
    """Executa a migração do banco de dados"""
    
    with app.app_context():
        print("🔄 Iniciando migração do sistema de compartilhamento...")
        
        try:
            # 1. Verificar se a coluna profissional_responsavel_id já existe
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='pacientes' AND column_name='profissional_responsavel_id'
            """))
            
            if not result.fetchone():
                print("📝 Adicionando coluna profissional_responsavel_id à tabela pacientes...")
                
                # Adicionar a coluna
                db.session.execute(text("""
                    ALTER TABLE pacientes 
                    ADD COLUMN profissional_responsavel_id INTEGER
                """))
                
                # Obter o primeiro profissional para usar como padrão
                primeiro_profissional = Profissional.query.first()
                if primeiro_profissional:
                    print(f"📝 Definindo profissional padrão: {primeiro_profissional.nome}")
                    
                    # Atualizar todos os pacientes existentes
                    db.session.execute(text("""
                        UPDATE pacientes 
                        SET profissional_responsavel_id = :prof_id 
                        WHERE profissional_responsavel_id IS NULL
                    """), {'prof_id': primeiro_profissional.id})
                    
                    # Adicionar constraint NOT NULL
                    db.session.execute(text("""
                        ALTER TABLE pacientes 
                        ALTER COLUMN profissional_responsavel_id SET NOT NULL
                    """))
                    
                    # Adicionar foreign key
                    db.session.execute(text("""
                        ALTER TABLE pacientes 
                        ADD CONSTRAINT REDACTED 
                        FOREIGN KEY (profissional_responsavel_id) 
                        REFERENCES profissionais(id) ON DELETE SET NULL
                    """))
                else:
                    print("⚠️  Nenhum profissional encontrado. Criando profissional padrão...")
                    # Criar um profissional padrão se não existir nenhum
                    from werkzeug.security import generate_password_hash
                    
                    prof_padrao = Profissional(
                        nome="Administrador",
                        crm="ADMIN001",
                        usuario="admin",
                        senha=generate_password_hash("Aracannabis@2025")
                    )
                    db.session.add(prof_padrao)
                    db.session.flush()  # Para obter o ID
                    
                    # Atualizar pacientes
                    db.session.execute(text("""
                        UPDATE pacientes 
                        SET profissional_responsavel_id = :prof_id
                    """), {'prof_id': prof_padrao.id})
                    
                    # Adicionar constraints
                    db.session.execute(text("""
                        ALTER TABLE pacientes 
                        ALTER COLUMN profissional_responsavel_id SET NOT NULL
                    """))
                    
                    db.session.execute(text("""
                        ALTER TABLE pacientes 
                        ADD CONSTRAINT REDACTED 
                        FOREIGN KEY (profissional_responsavel_id) 
                        REFERENCES profissionais(id) ON DELETE SET NULL
                    """))
                
                print("✅ Coluna profissional_responsavel_id adicionada com sucesso!")
            else:
                print("✅ Coluna profissional_responsavel_id já existe")
            
            # 2. Verificar se a tabela compartilhamentos_pacientes já existe
            result = db.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name='compartilhamentos_pacientes'
            """))
            
            if not result.fetchone():
                print("📝 Criando tabela compartilhamentos_pacientes...")
                
                # Criar a tabela usando SQLAlchemy
                db.create_all()
                
                print("✅ Tabela compartilhamentos_pacientes criada com sucesso!")
            else:
                print("✅ Tabela compartilhamentos_pacientes já existe")
            
            # 3. Commit das alterações
            db.session.commit()
            print("🎉 Migração concluída com sucesso!")
            
            # 4. Verificar dados
            total_pacientes = Paciente.query.count()
            total_profissionais = Profissional.query.count()
            total_compartilhamentos = CompartilhamentoPaciente.query.count()
            
            print("\n📊 Estatísticas do banco:")
            print(f"   - Profissionais: {total_profissionais}")
            print(f"   - Pacientes: {total_pacientes}")
            print(f"   - Compartilhamentos: {total_compartilhamentos}")
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {str(e)}")
            db.session.rollback()
            raise

def verificar_migracao():
    """Verifica se a migração foi aplicada corretamente"""
    
    with app.app_context():
        print("\n🔍 Verificando migração...")
        
        try:
            # Verificar estrutura da tabela pacientes
            result = db.session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name='pacientes' 
                ORDER BY ordinal_position
            """))
            
            print("\n📋 Estrutura da tabela pacientes:")
            for row in result:
                print(f"   - {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
            
            # Verificar estrutura da tabela compartilhamentos_pacientes
            result = db.session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name='compartilhamentos_pacientes' 
                ORDER BY ordinal_position
            """))
            
            print("\n📋 Estrutura da tabela compartilhamentos_pacientes:")
            for row in result:
                print(f"   - {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
            
            print("\n✅ Verificação concluída!")
            
        except Exception as e:
            print(f"❌ Erro durante a verificação: {str(e)}")

if __name__ == "__main__":
    print("🚀 Sistema de Compartilhamento de Pacientes - Migração")
    print("=" * 60)
    
    try:
        executar_migracao()
        verificar_migracao()
        
        print("\n🎯 Próximos passos:")
        print("   1. Reiniciar o servidor backend")
        print("   2. Testar o sistema de compartilhamento")
        print("   3. Verificar isolamento de dados por usuário")
        
    except Exception as e:
        print(f"\n💥 Falha na migração: {str(e)}")
        sys.exit(1)
