#!/usr/bin/env python3
"""
Script para definir a senha do admin principal
"""

import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Conectar ao banco
conn = sqlite3.connect('aracannabis.db')
cursor = conn.cursor()

# Senha desejada
senha_nova = "admin123"

# Gerar hash
senha_hash = generate_password_hash(senha_nova)

# Atualizar admin principal (id=1)
cursor.execute("UPDATE profissionais SET senha = ? WHERE id = 1", (senha_hash,))
conn.commit()

# Verificar atualização
cursor.execute("SELECT id, nome, usuario, senha FROM profissionais WHERE id = 1")
result = cursor.fetchone()

print("="*70)
print("🔐 CREDENCIAIS DO ADMIN ATUALIZADAS")
print("="*70)
print(f"🆔 ID: {result[0]}")
print(f"👤 Nome: {result[1]}")
print(f"📧 Usuário: {result[2]}")
print(f"🔑 Senha: {senha_nova}")
print(f"🔒 Hash (início): {result[3][:60]}...")
print("="*70)

# Testar verificação
check = check_password_hash(result[3], senha_nova)
print(f"\n✅ Verificação de senha: {'VÁLIDA' if check else 'INVÁLIDA'}")

conn.close()

print("\n" + "="*70)
print("🚀 TENTE FAZER LOGIN COM:")
print("   Usuário: admin")
print("   Senha: admin123")
print("="*70 + "\n")