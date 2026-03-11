import sqlite3
from werkzeug.security import generate_password_hash
import datetime
import os

db_path = 'instance/aracannabis.db'
if not os.path.exists(db_path):
    db_path = 'aracannabis.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Get data from solicitacoes_cadastro
cursor.execute("SELECT nome, email, crm, uf_crm FROM solicitacoes_cadastro WHERE email = 'abholzwarth@gmail.com'")
row = cursor.fetchone()

if row:
    nome, email, crm, uf_crm = row
    
    # 2. Check if already exists in profissionais
    cursor.execute("SELECT id FROM profissionais WHERE email = ?", (email,))
    if cursor.fetchone():
        print(f"Usuário {email} já existe em profissionais. Atualizando senha...")
        hashed_password = generate_password_hash('S@iUnimed123S@i', method='pbkdf2:sha256:100000')
        cursor.execute("UPDATE profissionais SET senha = ? WHERE email = ?", (hashed_password, email))
    else:
        print(f"Criando usuário {email} em profissionais...")
        hashed_password = generate_password_hash('S@iUnimed123S@i', method='pbkdf2:sha256:100000')
        cursor.execute("""
            INSERT INTO profissionais (nome, crm, uf_crm, usuario, email, senha, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nome, crm, uf_crm, email, email, hashed_password, 'profissional', datetime.datetime.utcnow()))
        
    # 3. Mark solicitacao as approved
    cursor.execute("UPDATE solicitacoes_cadastro SET status = 'aprovado' WHERE email = ?", (email,))
    
    conn.commit()
    print("Sucesso! Usuário 'abholzwarth@gmail.com' agora pode logar com a senha 'S@iUnimed123S@i'.")
else:
    print("Solicitação para 'abholzwarth@gmail.com' não encontrada.")

conn.close()
