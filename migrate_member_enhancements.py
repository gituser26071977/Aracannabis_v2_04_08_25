"""
Migration script to add new fields to Membro and create DocumentoMembro table.
Run this to upgrade the database schema.
"""

from models import db
from app_cors_livre import app

def migrate_member_enhancements():
    """Add new fields to members table and create documents table"""
    
    with app.app_context():
        # Use raw SQL for ALTER TABLE operations
        with db.engine.connect() as conn:
            print("Adding new fields to membros_associacao...")
            
            # Add new columns
            conn.execute(db.text("""
                ALTER TABLE membros_associacao
                ADD COLUMN IF NOT EXISTS data_nascimento DATE,
                ADD COLUMN IF NOT EXISTS endereco TEXT,
                ADD COLUMN IF NOT EXISTS telefone VARCHAR(20),
                ADD COLUMN IF NOT EXISTS email VARCHAR(255),
                ADD COLUMN IF NOT EXISTS rg VARCHAR(20),
                ADD COLUMN IF NOT EXISTS nome_responsavel VARCHAR(255),
                ADD COLUMN IF NOT EXISTS observacoes TEXT;
            """))
            conn.commit()
            
            print("Creating documentos_membro table...")
            
            # Create documentos_membro table
            conn.execute(db.text("""
                CREATE TABLE IF NOT EXISTS documentos_membro (
                    id SERIAL PRIMARY KEY,
                    membro_id INTEGER NOT NULL REFERENCES membros_associacao(id) ON DELETE CASCADE,
                    tipo_documento VARCHAR(50) NOT NULL,
                    nome_arquivo VARCHAR(255) NOT NULL,
                    tamanho INTEGER,
                    mime_type VARCHAR(100),
                    conteudo BYTEA,
                    data_upload TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    observacoes TEXT
                );
            """))
            conn.commit()
            
            print("Creating index on membro_id...")
            conn.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_documentos_membro_id 
                ON documentos_membro(membro_id);
            """))
            conn.commit()
            
            print("Migration completed successfully!")

if __name__ == '__main__':
    migrate_member_enhancements()
