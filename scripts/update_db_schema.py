import sys
import os

# Adicionar diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db
from app_cors_livre import create_app

app = create_app()

def update_schema():
    with app.app_context():
        print("Atualizando esquema do banco de dados...")
        
        # Verificar e adicionar colunas na tabela produtos
        with db.engine.connect() as conn:
            # Check if columns exist
            result = conn.execute(db.text("SELECT column_name FROM information_schema.columns WHERE table_name='produtos'"))
            existing_columns = [row[0] for row in result.fetchall()]
            
            # Adicionar instrucoes
            if 'instrucoes' not in existing_columns:
                print("Adicionando coluna 'instrucoes' em 'produtos'...")
                conn.execute(db.text("ALTER TABLE produtos ADD COLUMN instrucoes TEXT"))
            
            # Adicionar via_administracao
            if 'via_administracao' not in existing_columns:
                print("Adicionando coluna 'via_administracao' em 'produtos'...")
                conn.execute(db.text("ALTER TABLE produtos ADD COLUMN via_administracao VARCHAR(50) DEFAULT 'Oral'"))
                
        # Verificar e adicionar colunas na tabela dosagens
        with db.engine.connect() as conn:
            result = conn.execute(db.text("SELECT column_name FROM information_schema.columns WHERE table_name='dosagens'"))
            existing_columns = [row[0] for row in result.fetchall()]
            
            # Adicionar produto_id para vincular diretamente
            if 'produto_id' not in existing_columns:
                print("Adicionando coluna 'produto_id' em 'dosagens'...")
                conn.execute(db.text("ALTER TABLE dosagens ADD COLUMN produto_id INTEGER REFERENCES produtos(id)"))

            # Adicionar instrucoes personalizada na dosagem (caso médico queira mudar o padrão)
            if 'instrucoes_uso' not in existing_columns:
                print("Adicionando coluna 'instrucoes_uso' em 'dosagens'...")
                conn.execute(db.text("ALTER TABLE dosagens ADD COLUMN instrucoes_uso TEXT"))

            # Adicionar via (caso mude)
            if 'via_administracao' not in existing_columns:
                print("Adicionando coluna 'via_administracao' em 'dosagens'...")
                conn.execute(db.text("ALTER TABLE dosagens ADD COLUMN via_administracao VARCHAR(50)"))
                
        db.session.commit()
        print("Schema atualizado com sucesso!")

if __name__ == "__main__":
    update_schema()
