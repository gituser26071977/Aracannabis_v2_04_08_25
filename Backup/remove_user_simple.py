#!/usr/bin/env python3
"""
Script simples para remover usuário específico do banco de dados
"""

import os
import sqlite3

def remove_user_by_id(user_id):
    """Remove usuário específico diretamente do banco SQLite"""
    
    # Caminho do banco de dados
    db_path = os.path.join("instance", "aracannabis.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return False
    
    try:
        # Conecta ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se o usuário existe
        cursor.execute("SELECT id, nome, usuario FROM profissionais WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ Usuário com ID {user_id} não encontrado.")
            conn.close()
            return False
        
        print(f"🔍 Usuário encontrado: {user[1]} (ID: {user[0]}, Usuário: {user[2]})")
        
        # Confirma a remoção
        confirm = input(f"⚠️  CONFIRMA a remoção do usuário '{user[1]}'? (sim/não): ").strip().lower()
        
        if confirm not in ['sim', 's', 'yes', 'y']:
            print("❌ Operação cancelada pelo usuário.")
            conn.close()
            return False
        
        # Remove o usuário
        cursor.execute("DELETE FROM profissionais WHERE id = ?", (user_id,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ Usuário '{user[1]}' removido com sucesso!")
            
            # Lista usuários restantes
            cursor.execute("SELECT id, nome, usuario, created_at FROM profissionais ORDER BY id")
            remaining_users = cursor.fetchall()
            
            print(f"\n=== USUÁRIOS RESTANTES ({len(remaining_users)}) ===")
            for u in remaining_users:
                print(f"   - ID: {u[0]}, Nome: {u[1]}, Usuário: {u[2]}")
            
            conn.close()
            return True
        else:
            print("❌ Nenhum usuário foi removido.")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Erro ao remover usuário: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

def list_all_users():
    """Lista todos os usuários do banco"""
    
    db_path = os.path.join("instance", "aracannabis.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, nome, crm, usuario, created_at FROM profissionais ORDER BY id")
        users = cursor.fetchall()
        
        print(f"\n=== USUÁRIOS EXISTENTES ({len(users)}) ===")
        print("-" * 80)
        
        for user in users:
            print(f"ID: {user[0]}")
            print(f"Nome: {user[1]}")
            print(f"CRM: {user[2]}")
            print(f"Usuário: {user[3]}")
            print(f"Criado em: {user[4]}")
            print("-" * 40)
        
        conn.close()
        return users
        
    except Exception as e:
        print(f"❌ Erro ao listar usuários: {str(e)}")
        return []

def main():
    print("🔍 Listando usuários existentes...")
    users = list_all_users()
    
    if len(users) == 0:
        print("❌ Nenhum usuário encontrado.")
        return
    
    if len(users) == 1:
        print("✅ Apenas 1 usuário encontrado. Nada para remover.")
        return
    
    # Identifica usuários não-admin para remoção
    non_admin_users = []
    for user in users:
        if user[3].lower() != 'admin' and 'admin' not in user[1].lower():
            non_admin_users.append(user)
    
    if not non_admin_users:
        print("✅ Apenas usuários admin encontrados. Nada para remover.")
        return
    
    print("\n🗑️  Usuários não-admin que podem ser removidos:")
    for user in non_admin_users:
        print(f"   - ID: {user[0]}, Nome: {user[1]}, Usuário: {user[3]}")
    
    # Remove o usuário Dr. João Silva (ID: 2)
    if any(user[0] == 2 for user in non_admin_users):
        print("\n🎯 Removendo usuário Dr. João Silva (ID: 2)...")
        remove_user_by_id(2)
    else:
        print("❌ Usuário Dr. João Silva (ID: 2) não encontrado.")

if __name__ == "__main__":
    main()
