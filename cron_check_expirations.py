"""
Cron job script para verificação de expirações

Este script deve ser executado diariamente para:
1. Detectar profissionais próximos da expiração
2. Enviar avisos de expiração iminente
3. Enviar propostas de assinatura para expirados
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_cors_livre import app
from services.subscription_expiration_service import run_expiration_check

if __name__ == '__main__':
    with app.app_context():
        print("🔄 Executando verificação de expirações...")
        stats = run_expiration_check()
        
        print("\n📊 Resultados:")
        print(f"   ⚠️  Avisos enviados: {stats['warnings_sent']}")
        print(f"   💼 Propostas enviadas: {stats['proposals_sent']}")
        
        if stats['errors']:
            print(f"\n❌ Erros ({len(stats['errors'])}):")
            for error in stats['errors']:
                print(f"   - {error}")
        else:
            print("\n✅ Processamento concluído sem erros!")
