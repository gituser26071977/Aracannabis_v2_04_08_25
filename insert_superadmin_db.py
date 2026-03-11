#!/usr/bin/env python3
"""
Script para inserir superadmin diretamente no banco de dados
"""

import sqlite3
import secrets
import string

def generate_strong_password(length=16):
    """Gera uma senha forte com letras maiúsculas, minúsculas, números e símbolos"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

# Conectar ao banco
conn = sqlite3.connect('aracannabis.db')
cursor = conn.cursor()

# Gerar senha
senha = generate_strong_password()

# Verificar se superadmin já existe
cursor.execute("SELECT id, usuario, role FROM profissionais WHERE usuario = ?", ('superadmin',))
existing = cursor.fetchone()

if existing:
    print(f"⚠️  Superadmin já existe (ID: {existing[0]})")
    print(f"Atualizando senha...")
    # Atualizar senha do superadmin existente
    from werkzeug.security import generate_password_hash
    senha_hash = generate_password_hash(senha)
    cursor.execute("UPDATE profissionais SET senha = ? WHERE usuario = ?", (senha_hash, 'superadmin'))
    conn.commit()
    print("✅ Senha atualizada com sucesso!")
else:
    print("👤 Criando usuário 'superadmin'...")
    
    # Gerar hash da senha
    from werkzeug.security import generate_password_hash
    senha_hash = generate_password_hash(senha)
    
    # Inserir superadmin
    cursor.execute("""
        INSERT INTO profissionais (nome, crm, uf_crm, usuario, email, senha, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        'Super Administrador',
        'ADMIN0001',
        'BR',
        'superadmin',
        'superadmin@aracannabis.com.br',
        senha_hash,
        'superadmin'
    ))
    
    conn.commit()
    print("✅ Superadmin criado com sucesso!")

# Confirmar inserção/atualização
cursor.execute("SELECT id, nome, usuario, email, role FROM profissionais WHERE usuario = ?", ('superadmin',))
result = cursor.fetchone()

conn.close()

if result:
    print("\n" + "="*70)
    print("🔐 CREDENCIAIS DO SUPERADMIN")
    print("="*70)
    print(f"🆔 ID: {result[0]}")
    print(f"👤 Nome: {result[1]}")
    print(f"📧 Email: {result[3]}")
    print(f"🆔 Usuário: superadmin")
    print(f"🔑 Senha: {senha}")
    print(f"🎭 Role: {result[4]}")
    print("="*70)
    print("\n⚠️  ATENÇÃO: Salve estas credenciais em local seguro!")
    print("   Esta senha foi gerada automaticamente e é segura.")
    print("   Você pode alterá-la através da interface do sistema.")
    print("="*70 + "\n")