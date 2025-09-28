#!/usr/bin/env python3
"""
Script para testar diferentes configurações SMTP do Hostinger
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp_config(server, port, username, password, use_tls=True, use_ssl=False):
    """Testar configuração SMTP específica"""
    
    print(f"\n🔧 Testando: {server}:{port} (TLS: {use_tls}, SSL: {use_ssl})")
    
    try:
        if use_ssl:
            # Usar SSL direto
            server_conn = smtplib.SMTP_SSL(server, port)
        else:
            # Usar conexão normal
            server_conn = smtplib.SMTP(server, port)
            
            if use_tls:
                server_conn.starttls()
        
        # Tentar login
        server_conn.login(username, password)
        server_conn.quit()
        
        print(f"✅ Sucesso: {server}:{port}")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def send_test_email(server, port, username, password, use_tls=True, use_ssl=False):
    """Enviar email de teste"""
    
    print(f"\n📧 Enviando email de teste via {server}:{port}")
    
    try:
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = f"Aracannabis Sistema <{username}>"
        msg['To'] = username  # Enviar para si mesmo
        msg['Subject'] = "Teste de Email - Aracannabis Sistema"
        
        body = """
        Este é um email de teste do sistema Aracannabis.
        
        Se você recebeu este email, a configuração SMTP está funcionando corretamente!
        
        Configuração testada:
        - Servidor: {}
        - Porta: {}
        - TLS: {}
        - SSL: {}
        
        Atenciosamente,
        Sistema Aracannabis
        """.format(server, port, use_tls, use_ssl)
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Conectar e enviar
        if use_ssl:
            server_conn = smtplib.SMTP_SSL(server, port)
        else:
            server_conn = smtplib.SMTP(server, port)
            if use_tls:
                server_conn.starttls()
        
        server_conn.login(username, password)
        server_conn.send_message(msg)
        server_conn.quit()
        
        print(f"✅ Email enviado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        return False

def main():
    print("🚀 Testando configurações SMTP do Hostinger...")
    
    # Configurações do .env
    username = os.getenv('SMTP_USERNAME', 'suporte@agentesinteligentes.pro')
    password = os.getenv('SMTP_PASSWORD', '')
    
    if not password:
        print("❌ SMTP_PASSWORD não configurado no .env")
        return
    
    print(f"📧 Usuário: {username}")
    
    # Diferentes configurações para testar
    configs = [
        # Hostinger configurações comuns
        ('smtp.hostinger.com', 587, True, False),   # TLS
        ('smtp.hostinger.com', 465, False, True),   # SSL
        ('smtp.hostinger.com', 25, False, False),   # Sem criptografia
        ('smtp.hostinger.com', 2525, True, False),  # Porta alternativa
        
        # Configurações alternativas
        ('mail.agentesinteligentes.pro', 587, True, False),
        ('mail.agentesinteligentes.pro', 465, False, True),
    ]
    
    successful_configs = []
    
    for server, port, use_tls, use_ssl in configs:
        if test_smtp_config(server, port, username, password, use_tls, use_ssl):
            successful_configs.append((server, port, use_tls, use_ssl))
    
    if successful_configs:
        print(f"\n🎉 Configurações que funcionaram:")
        for i, (server, port, use_tls, use_ssl) in enumerate(successful_configs, 1):
            print(f"   {i}. {server}:{port} (TLS: {use_tls}, SSL: {use_ssl})")
        
        # Testar envio de email com a primeira configuração que funcionou
        server, port, use_tls, use_ssl = successful_configs[0]
        print(f"\n📤 Testando envio de email com a melhor configuração...")
        
        if send_test_email(server, port, username, password, use_tls, use_ssl):
            print(f"\n✅ CONFIGURAÇÃO RECOMENDADA:")
            print(f"   SMTP_SERVER={server}")
            print(f"   SMTP_PORT={port}")
            print(f"   SMTP_USE_TLS={'True' if use_tls else 'False'}")
            print(f"   SMTP_USE_SSL={'True' if use_ssl else 'False'}")
        
    else:
        print(f"\n❌ Nenhuma configuração funcionou. Verifique:")
        print(f"   - Credenciais de email")
        print(f"   - Configurações do provedor")
        print(f"   - Firewall/proxy")

if __name__ == "__main__":
    main()
