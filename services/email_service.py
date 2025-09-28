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
        
    def test_connection(self):
        # Testar conexão com o servidor SMTP
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                if self.use_tls:
                    server.starttls()
            server.login(self.username, self.password)
            server.quit()
            msg = "Conexão SMTP testada com sucesso!"
            logger.info(msg)
            return True, msg
        except Exception as e:
            msg = f"Falha na conexão SMTP: {e}"
            logger.error(msg)
            return False, msg
        
    def send_email(self, to_email, subject, html_body, text_body=None):
        # Enviar email usando SMTP ou simular em modo desenvolvimento
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
        # Simular envio de email para desenvolvimento
        try:
            # Criar diretório de emails se não existir (usando caminho absoluto)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(base_dir)  # Only one level up to ARACANNABIS_PRONTUARIO_NO_AI
            email_dir = os.path.join(project_root, "emails_simulados")
            os.makedirs(email_dir, exist_ok=True)
            logger.info(f"Diretório de emails simulado criado em: {email_dir}")
            print(f"📁 Diretório de emails simulado: {email_dir}")
            
            # Nome do arquivo baseado no timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(email_dir, f"email_{timestamp}_{to_email.replace('@', '_at_')}.html")
            
            # Conteúdo do email simulado
            simulated_content = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Email Simulado</title></head><body>"
            simulated_content += f"<div><h2>📧 Email Simulado (Modo Desenvolvimento)</h2>"
            simulated_content += f"<p><strong>Para:</strong> {to_email}</p>"
            simulated_content += f"<p><strong>Assunto:</strong> {subject}</p>"
            simulated_content += f"<p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p></div>"
            simulated_content += f"<div>{html_body}</div>"
            simulated_content += f"<div><p>Este email foi simulado em modo desenvolvimento.</p>"
            simulated_content += f"<p>Em produção, seria enviado via SMTP para: {to_email}</p></div></body></html>"
            
            # Salvar arquivo
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(simulated_content)
            
            # Log to both file and console
            logger.info(f"Email simulado salvo em: {filename}")
            print(f"📧 Email simulado para {to_email} salvo em: {filename}")
            
            # Also log the email simulation itself
            logger.info(f"Email simulado: {subject} para {to_email}")
            print(f"📧 Email simulado registrado: {subject} para {to_email}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao simular email: {e}")
            return False
    
    def send_approval_email(self, email, nome, usuario, senha_temporaria, data_expiracao):
        # Enviar email de aprovação com credenciais temporárias
        subject = "🎉 Sua solicitação foi aprovada - Aracannabis Sistema"
        
        # Formatear data de expiração
        try:
            if isinstance(data_expiracao, str):
                exp_date = datetime.fromisoformat(data_expiracao.replace('Z', '+00:00'))
            else:
                exp_date = data_expiracao
            data_formatada = exp_date.strftime('%d/%m/%Y')
        except:
            data_formatada = "7 dias a partir de agora"
        
        # Create email body
        html_body = f"<p>Olá {nome},</p>"
        html_body += f"<p>Sua solicitação de acesso ao sistema Aracannabis foi aprovada!</p>"
        html_body += f"<p>Seus dados de acesso temporários:</p>"
        html_body += "<ul>"
        html_body += f"<li><strong>Usuário:</strong> {usuario}</li>"
        html_body += f"<li><strong>Senha temporária:</strong> {senha_temporaria}</li>"
        html_body += f"<li><strong>Validade:</strong> {data_formatada}</li>"
        html_body += "</ul>"
        html_body += f"<p>Por favor, altere sua senha após o primeiro login.</p>"
        
        # Send email
        return self.send_email(email, subject, html_body)

    def send_exam_email(self, to_email, paciente_nome, exame_titulo, exame_data, exame_resultados, observacoes):
        # Enviar email de notificação de exame
        subject = f"🔬 Resultado de Exame - {exame_titulo} - Aracannabis"
        
        # Formatear data do exame
        try:
            if isinstance(exame_data, str):
                data_exame = datetime.strptime(exame_data, '%Y-%m-%d')
            else:
                data_exame = exame_data
            data_formatada = data_exame.strftime('%d/%m/%Y')
        except:
            data_formatada = "Data não disponível"
        
        # Create email body
        html_body = f"<p>Olá {paciente_nome},</p>"
        html_body += f"<p>Seu exame <strong>{exame_titulo}</strong> realizado em <strong>{data_formatada}</strong> está disponível.</p>"
        html_body += f"<p><strong>Resultados:</strong> {exame_resultados}</p>"
        
        if observacoes:
            html_body += f"<p><strong>Observações:</strong> {observacoes}</p>"
        
        html_body += f"<p>Acesse o sistema Aracannabis para mais detalhes.</p>"
        html_body += f"<p>Atenciosamente,<br>Equipe Aracannabis</p>"
        
        # Send email
        return self.send_email(to_email, subject, html_body)
