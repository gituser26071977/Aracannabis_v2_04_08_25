#!/usr/bin/env python3
"""
Script de inicialização para Docker/VPS
Cria tabelas, aplica migrações e verifica o ambiente
"""
import os
import sys
import time

# Aguardar banco de dados ficar disponível
def wait_for_db(max_retries=30):
    """Aguarda o banco de dados ficar disponível"""
    import socket
    
    # Parse DATABASE_URL para obter host e porta
    db_url = os.getenv('DATABASE_URL', '')
    if '@' in db_url:
        host_port = db_url.split('@')[1].split('/')[0]
        if ':' in host_port:
            host, port = host_port.split(':')
            port = int(port)
        else:
            host = host_port
            port = 5432
    else:
        host = 'siap-db'
        port = 5432
    
    print(f"⏳ Aguardando banco de dados em {host}:{port}...")
    
    for i in range(max_retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((host, port))
            sock.close()
            print(f"✅ Banco de dados disponível!")
            return True
        except Exception as e:
            print(f"  Tentativa {i+1}/{max_retries}...")
            time.sleep(2)
    
    print("❌ Banco de dados não respondeu após várias tentativas")
    return False

def init_database():
    """Inicializa o banco de dados"""
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        from app_cors_livre import create_app
        from models import db
        
        app = create_app()
        
        with app.app_context():
            print("🔄 Criando tabelas do banco de dados...")
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            # Verificar se é necessário criar superadmin inicial
            from models import Profissional
            admin = Profissional.query.filter_by(role='superadmin').first()
            if not admin:
                print("⚠️ Nenhum superadmin encontrado. Crie um usando create_superadmin.py")
            else:
                print(f"✅ Superadmin encontrado: {admin.usuario}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("════════════════════════════════════════════════════════════")
    print("  🚀 INICIALIZAÇÃO DO SISTEMA ARACANNABIS (DOCKER/VPS)")
    print("════════════════════════════════════════════════════════════\n")
    
    # Aguardar banco
    if not wait_for_db():
        sys.exit(1)
    
    print("")
    
    # Inicializar banco
    if not init_database():
        sys.exit(1)
    
    print("\n✅ Inicialização concluída com sucesso!")
    print("════════════════════════════════════════════════════════════\n")

if __name__ == "__main__":
    main()
