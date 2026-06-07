"""
Migração: Adicionar campos de autenticação na tabela Paciente

Adiciona:
- email (unique)
- senha_hash
- is_active
- email_verified
- last_login_at
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_cors_livre import create_app
from models import db

def migrate_add_patient_auth_fields():
    """Adiciona campos de autenticação para pacientes"""
    
    app = create_app()
    
    with app.app_context():
        print("🔄 Iniciando migração: Autenticação de Pacientes")
        
        # SQL para adicionar campos
        migrations = [
            """
            ALTER TABLE pacientes 
            ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE,
            ADD COLUMN IF NOT EXISTS senha_hash VARCHAR(255),
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT false,
            ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT false,
            ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP;
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_pacientes_email ON pacientes(email);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_pacientes_cpf ON pacientes(cpf);
            """
        ]
        
        try:
            for i, sql in enumerate(migrations, 1):
                print(f"  [{i}/{len(migrations)}] Executando migração...")
                db.session.execute(db.text(sql))
            
            db.session.commit()
            print("✅ Migração concluída com sucesso!")
            
            # Verificar resultados
            result = db.session.execute(db.text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'pacientes' 
                AND column_name IN ('email', 'senha_hash', 'is_active', 'email_verified', 'last_login_at')
                ORDER BY column_name;
            """))
            
            print("\n📋 Campos adicionados:")
            for row in result:
                print(f"   - {row[0]}: {row[1]}")
            
            # Contar pacientes
            total = db.session.execute(db.text("SELECT COUNT(*) FROM pacientes")).scalar()
            print(f"\n📊 Total de pacientes no sistema: {total}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro na migração: {str(e)}")
            raise


if __name__ == '__main__':
    migrate_add_patient_auth_fields()
