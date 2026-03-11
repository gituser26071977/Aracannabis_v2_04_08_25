#!/usr/bin/env python3
"""
Script para verificar o hash da senha do superadmin
"""

import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Conectar ao banco
conn = sqlite3.connect('aracannabis.db')
cursor = conn.cursor()

# Buscar o superadmin
cursor.execute("SELECT id, nome, usuario, senha, email, role FROM profissionais WHERE usuario = ?", ('superadmin',))
result = cursor.fetchone()

if result:
    print("="*70)
    print("🔍 DADOS DO SUPERADMIN NO BANCO")
    print("="*70)
    print(f"🆔 ID: {result[0]}")
    print(f"👤 Nome: {result[1]}")
    print(f"📧 Email: {result[4]}")
    print(f"🎭 Role: {result[5]}")
    print(f"🔒 Hash da senha (início): {result[3][:60]}...")
    print("="*70)
    
    # Senha correta
    senha_correta = "5D*I]zSx,Rfx'DRq"
    
    # Testar verificação
    print("\n🧪 Teste 1: Verificar senha correta")
    check1 = check_password_hash(result[3], senha_correta)
    print(f"Senha: {senha_correta}")
    print(f"Resultado: {'✅ VÁLIDA' if check1 else '❌ INVÁLIDA'}")
    
    # Criar um novo hash para comparação
    print("\n🧪 Teste 2: Criar novo hash e testar")
    novo_hash = generate_password_hash(senha_correta)
    check2 = check_password_hash(novo_hash, senha_correta)
    print(f"Novo hash (início): {novo_hash[:60]}...")
    print(f"Resultado: {'✅ VÁLIDA' if check2 else '❌ INVÁLIDA'}")
    
    # Testar com senha errada
    print("\n🧪 Teste 3: Verificar senha errada")
    senha_errada = "senha_errada"
    check3 = check_password_hash(result[3], senha_errada)
    print(f"Senha: {senha_errada}")
    print(f"Resultado: {'✅ VÁLIDA' if check3 else '❌ INVÁLIDA (esperado)'}")
    
    # Criar superadmin com senha simples para teste
    print("\n" + "="*70)
    print("🔄 Criando superadmin com senha simples para teste...")
    print("="*70)
    
    senha_simples = "admin123"
    hash_simples = generate_password_hash(senha_simples)
    
    # Atualizar o superadmin
    cursor.execute("UPDATE profissionais SET senha = ? WHERE usuario = ?", (hash_simples, 'superadmin'))
    conn.commit()
    
    print(f"✅ Senha atualizada para: {senha_simples}")
    print(f"🔒 Novo hash (início): {hash_simples[:60]}...")
    
    # Verificar novo hash
    cursor.execute("SELECT senha FROM profissionais WHERE usuario = ?", ('superadmin',))
    novo_result = cursor.fetchone()
    
    check4 = check_password_hash(novo_result[0], senha_simples)
    print(f"Verificação: {'✅ VÁLIDA' if check4 else '❌ INVÁLIDA'}")
    
    print("\n" + "="*70)
    print("🔐 NOVAS CREDENCIAIS (para teste)")
    print("="*70)
    print(f"Usuário: superadmin")
    print(f"Senha: {senha_simples}")
    print("="*70 + "\n")
    
else:
    print("❌ Superadmin não encontrado no banco de dados!")

conn.close()