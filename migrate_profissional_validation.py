"""
Migration script to add validation fields to profissionais table
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection from environment
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'siap_db')
DB_USER = os.getenv('DB_USER', 'siap_user')
DB_PASS = os.getenv('DB_PASS', 'siap_pass')

def migrate_profissionais_validation():
    """Add validation fields to profissionais table"""
    
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    
    try:
        cursor = conn.cursor()
        
        print("Adding validation fields to profissionais table...")
        
        # Add new columns
        migrations = [
            "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS status_cadastro VARCHAR(20) DEFAULT 'aprovado' NOT NULL",
            "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS motivo_rejeicao TEXT",
            "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS data_aprovacao TIMESTAMP",
            "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS aprovado_por VARCHAR(50)",
            "ALTER TABLE profissionais ADD COLUMN IF NOT EXISTS validation_data JSONB"
        ]
        
        for migration in migrations:
            print(f"Executing: {migration}")
            cursor.execute(migration)
        
        # Set existing professionals as approved
        print("Setting existing professionals as 'aprovado'...")
        cursor.execute("""
            UPDATE profissionais 
            SET status_cadastro = 'aprovado',
                data_aprovacao = created_at,
                aprovado_por = 'migration'
            WHERE status_cadastro IS NULL OR status_cadastro = ''
        """)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # Show results
        cursor.execute("SELECT COUNT(*) FROM profissionais WHERE status_cadastro = 'aprovado'")
        approved_count = cursor.fetchone()[0]
        print(f"Total approved professionals: {approved_count}")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    migrate_profissionais_validation()
