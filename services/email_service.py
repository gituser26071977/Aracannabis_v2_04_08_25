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
        self.email_from = os.getenv('EMAIL_FROM', 'suporte@arapath.com.br')
        self.email_from_name = os.getenv('EMAIL_FROM_NAME', 'AraOS — Clinical Intelligence Operating System')
        self.development_mode = os.getenv('EMAIL_DEVELOPMENT_MODE', 'True').lower() == 'true'
        # D05l (trial 14d): URL do site para CTA nos emails de boas-vindas/expiração
        self.site_url = os.getenv('ARAOS_SITE_URL', 'https://araos.aracannabis.com.br').strip()
        print(f"DEBUG: EmailService initialized. User={self.username}, DevMode={self.development_mode}")
        
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
            project_root = os.path.dirname(base_dir)  # Only one level up to ARAOS_PROJECT
            email_dir = os.path.join(project_root, "emails_simulados")
            os.makedirs(email_dir, exist_ok=True)
            logger.info(f"Diretório de emails simulado criado em: {email_dir}")
            print(f"📁 Diretório de emails simulado: {email_dir}")
            
            # Nome do arquivo baseado no timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(email_dir, f"email_{timestamp}_{to_email.replace('@', '_at_')}.html")
            
            # Conteúdo do email simulado
            simulated_content = "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Email Simulado</title></head><body>"
            simulated_content += "<div><h2>📧 Email Simulado (Modo Desenvolvimento)</h2>"
            simulated_content += f"<p><strong>Para:</strong> {to_email}</p>"
            simulated_content += f"<p><strong>Assunto:</strong> {subject}</p>"
            simulated_content += f"<p><strong>Data:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p></div>"
            simulated_content += f"<div>{html_body}</div>"
            simulated_content += "<div><p>Este email foi simulado em modo desenvolvimento.</p>"
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
        subject = "🎉 Sua solicitação foi aprovada - AraOS"

        # D05l (trial 14d): trial configurável via ARAOS_TRIAL_DAYS
        try:
            trial_days = int(os.getenv("ARAOS_TRIAL_DAYS", "14"))
        except (TypeError, ValueError):
            trial_days = 14

        # Formatear data de expiração
        try:
            if isinstance(data_expiracao, str):
                exp_date = datetime.fromisoformat(data_expiracao.replace('Z', '+00:00'))
            else:
                exp_date = data_expiracao
            data_formatada = exp_date.strftime('%d/%m/%Y')
        except:
            data_formatada = f"{trial_days} dias a partir de agora"

        # Create email body
        html_body = f"<p>Olá {nome},</p>"
        html_body += "<p>Sua solicitação de acesso ao AraOS foi aprovada!</p>"
        html_body += "<p>Seus dados de acesso temporários:</p>"
        html_body += "<ul>"
        html_body += f"<li><strong>Usuário:</strong> {usuario}</li>"
        html_body += f"<li><strong>Senha temporária:</strong> {senha_temporaria}</li>"
        html_body += f"<li><strong>Validade do trial:</strong> {data_formatada} ({trial_days} dias de acesso gratuito)</li>"
        html_body += "</ul>"
        html_body += "<p>Por favor, altere sua senha após o primeiro login.</p>"
        # D05l: aviso explícito do bloqueio + CTA para antecipar escolha de plano
        html_body += (
            "<p><strong>Importante:</strong> após o período de trial, o acesso ao "
            "prontuário eletrônico será pausado até a escolha de um plano pago. "
            "Você pode antecipar a escolha a qualquer momento para evitar "
            "qualquer interrupção.</p>"
        )
        html_body += (
            f"<p style=\"margin:24px 0 8px 0;\">"
            f"<a href=\"{self.site_url}/planos\" "
            f"style=\"display:inline-block;background:#2D5A3D;color:#ffffff;"
            f"padding:12px 24px;border-radius:6px;text-decoration:none;"
            f"font-weight:600;\">Conhecer os planos</a></p>"
        )
        html_body += f"<p><small>Link direto: <a href=\"{self.site_url}/planos\">{self.site_url}/planos</a></small></p>"

        # Send email
        return self.send_email(email, subject, html_body)

    def send_password_setup_email(self, email, nome, link_definicao, data_expiracao):
        subject = "🔐 Defina sua senha - AraOS"

        try:
            if isinstance(data_expiracao, str):
                exp_date = datetime.fromisoformat(data_expiracao.replace('Z', '+00:00'))
            else:
                exp_date = data_expiracao
            data_formatada = exp_date.strftime('%d/%m/%Y %H:%M')
        except Exception:
            data_formatada = "em 24 horas"

        html_body = f"<p>Olá {nome},</p>"
        html_body += "<p>Recebemos sua solicitação para definir a senha de acesso ao AraOS.</p>"
        html_body += f"<p><strong>Link para definir senha:</strong> <a href=\"{link_definicao}\">Definir senha</a></p>"
        html_body += f"<p>Este link expira em: <strong>{data_formatada}</strong></p>"
        html_body += "<p>Se você não solicitou, ignore este email.</p>"
        html_body += "<p>Atenciosamente,<br>Equipe AraOS</p>"

        return self.send_email(email, subject, html_body)

    def send_exam_email(self, to_email, paciente_nome, exame_titulo, exame_data, exame_resultados, observacoes):
        # Enviar email de notificação de exame
        subject = f"🔬 Resultado de Exame - {exame_titulo} - AraOS"
        
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
        
        html_body += "<p>Acesse o AraOS para mais detalhes.</p>"
        html_body += "<p>Atenciosamente,<br>Equipe AraOS</p>"
        
        # Send email
        return self.send_email(to_email, subject, html_body)

    def send_trial_expired_email(self, email, nome):
        subject = "⏳ Seu período de testes acabou - AraOS"

        # D05l (trial 14d): texto alinhado com a constante configurável
        try:
            trial_days = int(os.getenv("ARAOS_TRIAL_DAYS", "14"))
        except (TypeError, ValueError):
            trial_days = 14

        html_body = f"<p>Olá {nome},</p>"
        html_body += "<p>Esperamos que tenha aproveitado seu período de testes no AraOS!</p>"
        html_body += f"<p>Seu acesso gratuito de <strong>{trial_days} dias</strong> expirou.</p>"
        html_body += "<h3>Para continuar usando o sistema, escolha um de nossos planos:</h3>"
        html_body += "<ul>"
        html_body += "<li><strong>Plano Sem IA:</strong> R$ 99,00/mês ou R$ 1.092,96/ano (8% OFF)</li>"
        html_body += "<li><strong>Plano Com IA:</strong> R$ 250,00/mês ou R$ 2.550,00/ano (15% OFF)</li>"
        html_body += "</ul>"
        html_body += "<p>Acesse nossa página de pagamentos para regularizar sua assinatura e desbloquear seu acesso imediatamente:</p>"
        html_body += (
            f"<p style=\"margin:24px 0 8px 0;\">"
            f"<a href=\"{self.site_url}/planos\" "
            f"style=\"display:inline-block;background:#2D5A3D;color:#ffffff;"
            f"padding:12px 24px;border-radius:6px;text-decoration:none;"
            f"font-weight:600;\">Regularizar Assinatura</a></p>"
        )
        html_body += f"<p><small>Link direto: <a href=\"{self.site_url}/planos\">{self.site_url}/planos</a></small></p>"
        html_body += "<p>Se tiver dúvidas, entre em contato com nosso suporte.</p>"
        
        return self.send_email(email, subject, html_body)

    def send_registration_received_email(self, email, nome):
        subject = "🌿 Solicitação de Cadastro Recebida - AraOS"

        # D05l (trial 14d): texto alinhado com a constante configurável
        try:
            trial_days = int(os.getenv("ARAOS_TRIAL_DAYS", "14"))
        except (TypeError, ValueError):
            trial_days = 14

        html_body = f"<p>Olá {nome},</p>"
        html_body += "<p>Recebemos sua solicitação de cadastro no AraOS.</p>"
        html_body += "<p>Nossa equipe irá analisar seus dados (CRM, etc) e em breve você receberá um email com o resultado.</p>"
        html_body += (
            f"<p>Se aprovado, você terá <strong>{trial_days} dias</strong> de "
            f"acesso gratuito para testar a plataforma. Você pode antecipar a "
            f"escolha de um plano a qualquer momento.</p>"
        )
        html_body += "<p>Atenciosamente,<br>Equipe AraOS</p>"
        
        return self.send_email(email, subject, html_body)
