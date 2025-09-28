"""
Serviço de envio de emails com fallback para desenvolvimento
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.hostinger.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.username = os.getenv('SMTP_USERNAME', 'suporte@agentesinteligentes.pro')
        self.password = os.getenv('SMTP_PASSWORD', '')
        self.use_tls = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
        self.use_ssl = os.getenv('SMTP_USE_SSL', 'False').lower() == 'true'
        self.email_from = os.getenv('EMAIL_FROM', 'suporte@agentesinteligentes.pro')
        self.email_from_name = os.getenv('EMAIL_FROM_NAME', 'Aracannabis Sistema')
        self.development_mode = os.getenv('EMAIL_DEVELOPMENT_MODE', 'True').lower() == 'true'
        
    def send_email(self, to_email, subject, html_body, text_body=None):
        """Enviar email usando SMTP ou simular em modo desenvolvimento"""
        
        if self.development_mode:
            return self._simulate_email_send(to_email, subject, html_body, text_body)
        
        try:
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email_from_name} <{self.email_from}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Adicionar corpo do email
            if text_body:
                part1 = MIMEText(text_body, 'plain', 'utf-8')
                msg.attach(part1)
            
            part2 = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(part2)
            
            # Conectar ao servidor SMTP
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_tls:
                    server.starttls()
            
            server.login(self.username, self.password)
            
            # Enviar email
            text = msg.as_string()
            server.sendmail(self.email_from, to_email, text)
            server.quit()
            
            logger.info(f"Email enviado com sucesso para {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email para {to_email}: {e}")
            # Fallback para modo desenvolvimento se SMTP falhar
            logger.warning("Fallback para modo desenvolvimento ativado")
            return self._simulate_email_send(to_email, subject, html_body, text_body)
    
    def _simulate_email_send(self, to_email, subject, html_body, text_body=None):
        """Simular envio de email para desenvolvimento"""
        try:
            # Criar diretório de emails se não existir
            email_dir = "emails_simulados"
            os.makedirs(email_dir, exist_ok=True)
            
            # Nome do arquivo baseado no timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{email_dir}/email_{timestamp}_{to_email.replace('@', '_at_')}.html"
            
            # Conteúdo do email simulado
            simulated_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Email Simulado - {subject}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .content {{ border: 1px solid #ddd; padding: 20px; border-radius: 5px; }}
        .footer {{ margin-top: 20px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>📧 Email Simulado (Modo Desenvolvimento)</h2>
        <p><strong>Para:</strong> {to_email}</p>
        <p><strong>Assunto:</strong> {subject}</p>
        <p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
    </div>
    
    <div class="content">
        {html_body}
    </div>
    
    <div class="footer">
        <p>Este email foi simulado em modo desenvolvimento.</p>
        <p>Em produção, seria enviado via SMTP para: {to_email}</p>
    </div>
</body>
</html>
            """
            
            # Salvar arquivo
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(simulated_content)
            
            logger.info(f"Email simulado salvo em: {filename}")
            print(f"📧 Email simulado para {to_email} salvo em: {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao simular email: {e}")
            return False
    
    def send_approval_email(self, email, nome, usuario, senha_temporaria, data_expiracao):
        """Enviar email de aprovação com credenciais temporárias"""
        
        subject = "🎉 Sua solicitação foi aprovada - Aracannabis Sistema"
        
        # Formatear data de expiração
        try:
            if isinstance(data_expiracao, str):
                exp_date = datetime.fromisoformat(data_expiracao.replace('Z', '+00:00'))
            else:
                exp_date = data_expiracao
            data_formatada = exp_date.strftime('%d/%m/%Y às %H:%M')
        except:
            data_formatada = "7 dias a partir de agora"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2e7d32; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .credentials {{ background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 5px solid #2e7d32; }}
                .warning {{ background: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 5px solid #ff9800; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                .button {{ display: inline-block; background: #2e7d32; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌿 Aracannabis Sistema</h1>
                    <p>Sua solicitação foi aprovada!</p>
                </div>
                
                <div class="content">
                    <h2>Olá, {nome}!</h2>
                    
                    <p>Temos o prazer de informar que sua solicitação de acesso ao sistema Aracannabis foi <strong>aprovada</strong>!</p>
                    
                    <p>Você agora tem acesso temporário ao nosso sistema de prontuário eletrônico para pacientes de cannabis medicinal.</p>
                    
                    <div class="credentials">
                        <h3>🔑 Suas Credenciais de Acesso:</h3>
                        <p><strong>Usuário:</strong> {usuario}</p>
                        <p><strong>Senha Temporária:</strong> {senha_temporaria}</p>
                        <p><strong>Válido até:</strong> {data_formatada}</p>
                    </div>
                    
                    <div class="warning">
                        <h3>⚠️ Importante:</h3>
                        <ul>
                            <li>Esta é uma conta temporária válida por <strong>7 dias</strong></li>
                            <li>Use este período para avaliar todas as funcionalidades do sistema</li>
                            <li>Mantenha suas credenciais em segurança</li>
                            <li>Entre em contato conosco se tiver dúvidas</li>
                        </ul>
                    </div>
                    
                    <p style="text-align: center;">
                        <a href="http://localhost:3000/login" class="button">Acessar Sistema</a>
                    </p>
                    
                    <h3>📋 Funcionalidades Disponíveis:</h3>
                    <ul>
                        <li>✅ Gerenciamento completo de pacientes</li>
                        <li>✅ Registro e acompanhamento de sintomas</li>
                        <li>✅ Controle de dosagens e medicações</li>
                        <li>✅ Histórico de evolução dos pacientes</li>
                        <li>✅ Agendamento de consultas</li>
                        <li>✅ Relatórios e gráficos detalhados</li>
                        <li>✅ Sistema de compartilhamento entre profissionais</li>
                        <li>✅ Conformidade total com LGPD</li>
                    </ul>
                    
                    <p>Esperamos que o sistema atenda às suas necessidades. Após o período de avaliação, entre em contato para discutir a contratação.</p>
                    
                    <p>Atenciosamente,<br>
                    <strong>Equipe Aracannabis</strong></p>
                </div>
                
                <div class="footer">
                    <p>Este é um email automático. Para suporte, responda este email ou entre em contato conosco.</p>
                    <p>© 2025 Aracannabis Sistema - Todos os direitos reservados</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Aracannabis Sistema - Solicitação Aprovada
        
        Olá, {nome}!
        
        Sua solicitação de acesso ao sistema Aracannabis foi APROVADA!
        
        CREDENCIAIS DE ACESSO:
        Usuário: {usuario}
        Senha Temporária: {senha_temporaria}
        Válido até: {data_formatada}
        
        IMPORTANTE:
        - Esta é uma conta temporária válida por 7 dias
        - Use este período para avaliar o sistema
        - Mantenha suas credenciais em segurança
        
        Acesse: http://localhost:3000/login
        
        Atenciosamente,
        Equipe Aracannabis
        """
        
        return self.send_email(email, subject, html_body, text_body)
    
    def send_rejection_email(self, email, nome, observacoes=""):
        """Enviar email de rejeição"""
        
        subject = "Solicitação de Acesso - Aracannabis Sistema"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #d32f2f; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                .info {{ background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 5px solid #2196f3; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌿 Aracannabis Sistema</h1>
                    <p>Sobre sua solicitação de acesso</p>
                </div>
                
                <div class="content">
                    <h2>Olá, {nome}!</h2>
                    
                    <p>Agradecemos seu interesse no sistema Aracannabis.</p>
                    
                    <p>Após análise, não foi possível aprovar sua solicitação de acesso no momento.</p>
                    
                    {f'<div class="info"><h3>Observações:</h3><p>{observacoes}</p></div>' if observacoes else ''}
                    
                    <p>Você pode enviar uma nova solicitação a qualquer momento com informações atualizadas.</p>
                    
                    <p>Para dúvidas ou esclarecimentos, entre em contato conosco.</p>
                    
                    <p>Atenciosamente,<br>
                    <strong>Equipe Aracannabis</strong></p>
                </div>
                
                <div class="footer">
                    <p>Este é um email automático. Para suporte, responda este email.</p>
                    <p>© 2025 Aracannabis Sistema - Todos os direitos reservados</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Aracannabis Sistema - Solicitação de Acesso
        
        Olá, {nome}!
        
        Agradecemos seu interesse no sistema Aracannabis.
        
        Após análise, não foi possível aprovar sua solicitação no momento.
        
        {f'Observações: {observacoes}' if observacoes else ''}
        
        Você pode enviar uma nova solicitação a qualquer momento.
        
        Atenciosamente,
        Equipe Aracannabis
        """
        
        return self.send_email(email, subject, html_body, text_body)
    
    def test_connection(self):
        """Testar conexão SMTP ou modo desenvolvimento"""
        
        if self.development_mode:
            return True, "Modo desenvolvimento ativo - emails serão simulados"
        
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_tls:
                    server.starttls()
            
            server.login(self.username, self.password)
            server.quit()
            
            return True, "Conexão SMTP bem-sucedida"
            
        except Exception as e:
            return False, f"Erro na conexão SMTP: {e}"

# Instância global do serviço
email_service = EmailService()
