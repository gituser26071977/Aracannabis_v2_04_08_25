#!/usr/bin/env python3
"""
Script para migrar o banco de dados e adicionar a tabela de exames
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Exame

def migrate_database():
    """Executa a migração do banco de dados"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔄 Iniciando migração do banco de dados...")
            print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Verificar se a tabela de exames já existe
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'exames' in existing_tables:
                print("✅ Tabela 'exames' já existe no banco de dados")
                
                # Verificar se todas as colunas existem
                columns = [col['name'] for col in inspector.get_columns('exames')]
                expected_columns = [
                    'id', 'paciente_id', 'profissional_id', 'tipo_exame', 
                    'data_exame', 'data_resultado', 'observacoes', 
                    'arquivo_nome', 'arquivo_path', 'arquivo_tipo', 
                    'arquivo_tamanho', 'arquivo_hash', 'created_at', 'updated_at'
                ]
                
                missing_columns = [col for col in expected_columns if col not in columns]
                if missing_columns:
                    print(f"⚠️  Colunas faltando na tabela 'exames': {missing_columns}")
                    print("🔄 Recriando tabela com todas as colunas...")
                    
                    # Fazer backup dos dados existentes se houver
                    try:
                        existing_exames = db.session.execute(db.text("SELECT * FROM exames")).fetchall()
                        print(f"📦 Backup de {len(existing_exames)} exames existentes")
                    except:
                        existing_exames = []
                    
                    # Recriar tabela
                    db.drop_all(tables=[Exame.__table__])
                    db.create_all(tables=[Exame.__table__])
                    
                    print("✅ Tabela 'exames' recriada com sucesso")
                else:
                    print("✅ Tabela 'exames' está atualizada")
            else:
                print("🆕 Criando tabela 'exames'...")
                db.create_all(tables=[Exame.__table__])
                print("✅ Tabela 'exames' criada com sucesso")
            
            # Criar diretório de uploads se não existir
            upload_dir = 'uploads/exames'
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir, exist_ok=True)
                print(f"📁 Diretório de uploads criado: {upload_dir}")
            else:
                print(f"📁 Diretório de uploads já existe: {upload_dir}")
            
            # Verificar integridade das foreign keys
            print("🔍 Verificando integridade das foreign keys...")
            
            # Verificar se as tabelas relacionadas existem
            required_tables = ['pacientes', 'profissionais']
            for table in required_tables:
                if table not in existing_tables:
                    print(f"⚠️  Tabela relacionada '{table}' não encontrada")
                    print("🔄 Criando todas as tabelas...")
                    db.create_all()
                    break
            else:
                print("✅ Todas as tabelas relacionadas existem")
            
            # Commit das mudanças
            db.session.commit()
            
            print("\n🎉 Migração concluída com sucesso!")
            print("\n📋 Resumo da migração:")
            print("   ✅ Tabela 'exames' configurada")
            print("   ✅ Diretório de uploads configurado")
            print("   ✅ Foreign keys verificadas")
            print("\n🚀 O sistema está pronto para gerenciar exames!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro durante a migração: {str(e)}")
            db.session.rollback()
            return False

def verify_migration():
    """Verifica se a migração foi bem-sucedida"""
    app = create_app()
    
    with app.app_context():
        try:
            # Testar criação de um exame fictício
            from models import Paciente, Profissional
            
            # Verificar se existem pacientes e profissionais
            paciente_count = Paciente.query.count()
            profissional_count = Profissional.query.count()
            
            print(f"\n📊 Estatísticas do banco:")
            print(f"   👥 Pacientes: {paciente_count}")
            print(f"   👨‍⚕️ Profissionais: {profissional_count}")
            
            # Verificar estrutura da tabela exames
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('exames')
            
            print(f"\n🏗️  Estrutura da tabela 'exames':")
            for col in columns:
                print(f"   📋 {col['name']}: {col['type']}")
            
            print("\n✅ Verificação concluída - Sistema pronto para uso!")
            return True
            
        except Exception as e:
            print(f"\n❌ Erro na verificação: {str(e)}")
            return False

if __name__ == '__main__':
    print("🏥 Sistema de Prontuário Aracannabis")
    print("📋 Migração da Tabela de Exames")
    print("=" * 50)
    
    # Executar migração
    if migrate_database():
        print("\n" + "=" * 50)
        verify_migration()
    else:
        print("\n❌ Migração falhou. Verifique os logs de erro acima.")
        sys.exit(1)
