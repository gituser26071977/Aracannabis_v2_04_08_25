#!/usr/bin/env python3
"""
Script simples para rodar o servidor Flask
"""

from app_cors_livre import create_app

if __name__ == '__main__':
    app = create_app()
    print("🚀 Iniciando servidor Aracannabis...")
    print("📱 API disponível em: http://localhost:5001")
    print("🔍 Status da API: http://localhost:5001/api/status")
    print("⏹️  Pressione Ctrl+C para parar")
    print("-" * 50)
    
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5001,
        use_reloader=False
    )
