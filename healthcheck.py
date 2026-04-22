#!/usr/bin/env python3
"""
Healthcheck simples para o backend
Retorna 0 se saudável, 1 se não
"""
import sys
import os

# Adicionar path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_health():
    try:
        from app_cors_livre import create_app
        from models import db
        
        app = create_app()
        
        with app.app_context():
            # Testar conexão com banco
            result = db.session.execute(db.text('SELECT 1')).scalar()
            if result != 1:
                print("❌ Falha na conexão com banco de dados")
                return False
            
            print("✅ Banco de dados: OK")
            
            # Verificar se tabelas principais existem
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['profissionais', 'pacientes']
            for table in required_tables:
                if table in tables:
                    print(f"✅ Tabela '{table}': OK")
                else:
                    print(f"❌ Tabela '{table}': NÃO ENCONTRADA")
                    return False
            
            return True
            
    except Exception as e:
        print(f"❌ Erro no healthcheck: {e}")
        return False

if __name__ == "__main__":
    if check_health():
        print("\n✅ Sistema saudável!")
        sys.exit(0)
    else:
        print("\n❌ Sistema com problemas!")
        sys.exit(1)
