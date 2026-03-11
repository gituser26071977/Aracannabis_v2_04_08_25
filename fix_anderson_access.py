import sqlite3
import os
import datetime

db_path = 'instance/aracannabis.db'
if not os.path.exists(db_path):
    db_path = 'aracannabis.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Ajustando Perfil de Anderson ---")

# 1. Promover Anderson a admin global
cursor.execute("UPDATE profissionais SET role = 'admin' WHERE email = 'abholzwarth@gmail.com'")
print("✅ Anderson promovido a Admin Global.")

# 2. Criar Associação Padrão
cursor.execute("INSERT INTO associacoes (nome, criada_em) VALUES (?, ?)", ('Aracannabis Matriz', datetime.datetime.utcnow()))
assoc_id = cursor.lastrowid
print(f"✅ Associação 'Aracannabis Matriz' criada (ID: {assoc_id}).")

# 3. Vincular Anderson à associação como admin
cursor.execute("SELECT id FROM profissionais WHERE email = 'abholzwarth@gmail.com'")
user_id = cursor.fetchone()[0]

cursor.execute("""
    INSERT INTO usuarios_associacoes (profissional_id, associacao_id, role, status, created_at)
    VALUES (?, ?, 'admin', 'active', ?)
""", (user_id, assoc_id, datetime.datetime.utcnow()))
print("✅ Vínculo de Anderson com a Associação criado como Admin.")

conn.commit()
conn.close()
print("\n--- Tudo pronto! Basta recarregar a página. ---")
