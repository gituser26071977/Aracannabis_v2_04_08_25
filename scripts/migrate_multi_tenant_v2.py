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

tables_to_migrate = [
    'logs_atividades',
    'sintomas',
    'dosagens',
    'prescricoes',
    'evolucoes',
    'consultas',
    'exames'
]

print("--- Iniciando Migração Multi-tenant ---")

for table in tables_to_migrate:
    try:
        # Tentar adicionar a coluna associacao_id
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN associacao_id INTEGER REFERENCES associacoes(id) ON DELETE CASCADE")
        print(f"✅ Coluna associacao_id adicionada à tabela {table}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"ℹ️ Coluna associacao_id já existe na tabela {table}")
        else:
            print(f"❌ Erro ao alterar tabela {table}: {e}")

# Tentar atualizar constraints de chaves estrangeiras que faltavam on delete cascade
# SQLite não suporta alterar constraints diretamente (precisa recriar tabela),
# mas para as novas colunas e as que já tinham referências enviadas pelo app.create_all(),
# as alterações no models.py serão aplicadas em novas instalações.
# Aqui vamos focar em garantir que o associacao_id seja preenchido baseado no paciente_id

print("\n--- Populando associacao_id baseado no paciente_id ---")

for table in tables_to_migrate:
    if table == 'logs_atividades':
        continue # logs de atividade podem não ter paciente_id direto
        
    try:
        cursor.execute(f"""
            UPDATE {table} 
            SET associacao_id = (
                SELECT associacao_id FROM pacientes WHERE pacientes.id = {table}.paciente_id
            )
            WHERE associacao_id IS NULL
        """)
        print(f"✅ Dados de associacao_id populados na tabela {table}")
    except Exception as e:
        print(f"❌ Erro ao popular dados na tabela {table}: {e}")

conn.commit()
conn.close()
print("\n--- Migração concluída com sucesso! ---")
