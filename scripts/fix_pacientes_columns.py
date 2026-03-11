import sqlite3
import os

# Tentar encontrar o banco de dados correto
db_path = 'instance/aracannabis.db'
if not os.path.exists(db_path):
    db_path = 'aracannabis.db'

if not os.path.exists(db_path):
    print("Erro: Arquivo de banco de dados não encontrado em root ou instance/")
    exit(1)

print(f"Usando banco de dados: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Adicionando Colunas Faltantes na Tabela Pacientes ---")

columns_to_add = [
    ('senha_hash', 'VARCHAR(255)'),
    ('is_active', 'BOOLEAN DEFAULT 1'),
    ('email_verified', 'BOOLEAN DEFAULT 0'),
    ('last_login_at', 'DATETIME')
]

for col_name, col_type in columns_to_add:
    try:
        cursor.execute(f"ALTER TABLE pacientes ADD COLUMN {col_name} {col_type}")
        print(f"✅ Coluna {col_name} adicionada com sucesso.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"ℹ️ Coluna {col_name} já existe.")
        else:
            print(f"❌ Erro ao adicionar coluna {col_name}: {e}")

conn.commit()
conn.close()
print("\n--- Operação concluída ---")
