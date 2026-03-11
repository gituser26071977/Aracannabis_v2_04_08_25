"""
Serviço de Gerenciamento de Expiração de Acesso

Detecta profissionais com acesso expirado e envia emails
com propostas de assinatura/renovação.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from models import db, Profissional
from services.email_service import EmailService

logger = logging.getLogger(__name__)

class SubscriptionExpirationService:
    """Gerencia expiração de acesso e renovações"""
    
    # Configurações padrão
    TRIAL_DAYS = 7  # Período de trial gratuito
    WARNING_DAYS_BEFORE = 2  # Avisar 2 dias antes de expirar
    
    @staticmethod
    def get_expiring_professionals(days_before: int = WARNING_DAYS_BEFORE) -> List[Profissional]:
        """
        Busca profissionais que vão expirar em X dias
        
        Args:
            days_before: Quantos dias antes da expiração buscar
            
        Returns:
            Lista de profissionais próximos da expiração
        """
        try:
            target_date = datetime.utcnow() + timedelta(days=days_before)
            next_day = target_date + timedelta(days=1)
            
            expiring = Profissional.query.filter(
                Profissional.data_expiracao.isnot(None),
                Profissional.data_expiracao >= target_date,
                Profissional.data_expiracao < next_day,
                Profissional.status_cadastro == 'aprovado'
            ).all()
            
            logger.info(f"Encontrados {len(expiring)} profissionais expirando em {days_before} dias")
            return expiring
            
        except Exception as e:
            logger.error(f"Erro ao buscar profissionais expirando: {str(e)}")
            return []
    
    @staticmethod
    def get_expired_professionals() -> List[Profissional]:
        """
        Busca profissionais com acesso já expirado
        
        Returns:
            Lista de profissionais expirados
        """
        try:
            now = datetime.utcnow()
            
            expired = Profissional.query.filter(
                Profissional.data_expiracao.isnot(None),
                Profissional.data_expiracao < now,
                Profissional.status_cadastro == 'aprovado'
            ).all()
            
            logger.info(f"Encontrados {len(expired)} profissionais expirados")
            return expired
            
        except Exception as e:
            logger.error(f"Erro ao buscar profissionais expirados: {str(e)}")
            return []
    
    @staticmethod
    def set_trial_expiration(profissional_id: int, trial_days: int = TRIAL_DAYS) -> Dict:
        """
        Define data de expiração para um profissional (período trial)
        
        Args:
            profissional_id: ID do profissional
            trial_days: Dias de trial (padrão 7)
            
        Returns:
            Dict com resultado da operação
        """
        try:
            prof = Profissional.query.get(profissional_id)
            if not prof:
                return {'error': f'Profissional {profissional_id} não encontrado'}
            
            # Se já tem data de expiração, não sobrescrever
            if prof.data_expiracao:
                return {
                    'warning': 'Profissional já possui data de expiração',
                    'current_expiration': prof.data_expiracao.isoformat()
                }
            
            # Definir expiração para agora + trial_days
            prof.data_expiracao = datetime.utcnow() + timedelta(days=trial_days)
            db.session.commit()
            
            logger.info(f"Trial de {trial_days} dias definido para {prof.nome} (expira em {prof.data_expiracao})")
            
            return {
                'success': True,
                'profissional_id': profissional_id,
                'expiration_date': prof.data_expiracao.isoformat(),
                'trial_days': trial_days
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao definir trial: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def extend_subscription(profissional_id: int, days: int) -> Dict:
        """
        Estende a assinatura de um profissional por X dias
        
        Args:
            profissional_id: ID do profissional
            days: Dias para estender
            
        Returns:
            Dict com resultado
        """
        try:
            prof = Profissional.query.get(profissional_id)
            if not prof:
                return {'error': f'Profissional {profissional_id} não encontrado'}
            
            # Se não tem expiração, criar a partir de agora
            if not prof.data_expiracao:
                base_date = datetime.utcnow()
            else:
                # Se já expirou, partir de agora; senão, da data atual
                base_date = max(prof.data_expiracao, datetime.utcnow())
            
            prof.data_expiracao = base_date + timedelta(days=days)
            db.session.commit()
            
            logger.info(f"Assinatura de {prof.nome} estendida por {days} dias (nova expiração: {prof.data_expiracao})")
            
            return {
                'success': True,
                'profissional_id': profissional_id,
                'new_expiration_date': prof.data_expiracao.isoformat(),
                'days_extended': days
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao estender assinatura: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def revoke_access(profissional_id: int) -> Dict:
        """
        Revoga acesso de profissional (marca como expirado)
        
        Args:
            profissional_id: ID do profissional
            
        Returns:
            Dict com resultado
        """
        try:
            prof = Profissional.query.get(profissional_id)
            if not prof:
                return {'error': f'Profissional {profissional_id} não encontrado'}
            
            # Marcar como expirado (data no passado)
            prof.data_expiracao = datetime.utcnow() - timedelta(days=1)
            db.session.commit()
            
            logger.warning(f"Acesso revogado para {prof.nome}")
            
            return {
                'success': True,
                'profissional_id': profissional_id,
                'status': 'access_revoked'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao revogar acesso: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def send_expiration_warning(profissional: Profissional, days_remaining: int) -> Dict:
        """
        Envia email de aviso de expiração próxima
        
        Args:
            profissional: Objeto Profissional
            days_remaining: Dias restantes até expiração
            
        Returns:
            Dict com resultado do envio
        """
        if not profissional.email:
            return {'error': 'Profissional sem email cadastrado'}
        
        subject = f"⏰ Seu acesso expira em {days_remaining} dia(s) - Aracannabis"
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #ff9800;">⏰ Seu acesso está próximo do fim</h2>
            
            <p>Olá <strong>Dr(a). {profissional.nome}</strong>,</p>
            
            <p>Seu período de <strong>trial gratuito</strong> está chegando ao fim!</p>
            
            <div style="background: #fff3cd; border-left: 4px solid #ff9800; padding: 15px; margin: 20px 0;">
                <p style="margin: 0;"><strong>⏰ Tempo restante:</strong> {days_remaining} dia(s)</p>
                <p style="margin: 5px 0 0 0;"><strong>📅 Data de expiração:</strong> {profissional.data_expiracao.strftime('%d/%m/%Y às %H:%M')}</p>
            </div>
            
            <p>Para continuar utilizando o sistema Aracannabis sem interrupções, escolha um de nossos planos:</p>
            
            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                <h3 style="margin-top: 0;">📋 Planos Disponíveis</h3>
                <p style="color: #666; margin-bottom: 20px;">Em breve você receberá informações detalhadas sobre nossos planos de assinatura.</p>
                <a href="http://localhost:3000/pricing" style="background: #4CAF50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold;">Ver Planos</a>
            </div>
            
            <p style="margin-top: 30px;">Caso tenha dúvidas, nossa equipe está à disposição:</p>
            <p>📧 Email: contato@aracannabis.com.br<br>
            📱 WhatsApp: (11) 99999-9999</p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">Este é um email automático do sistema Aracannabis.</p>
        </div>
        """
        
        try:
            email_service = EmailService()
            return email_service.send_email(
                destinatario=profissional.email,
                assunto=subject,
                corpo_html=html_body,
                corpo_texto=f"Seu acesso expira em {days_remaining} dia(s). Acesse para renovar: http://localhost:3000/pricing"
            )
        except Exception as e:
            logger.error(f"Erro ao enviar email de aviso: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def send_subscription_proposal(profissional: Profissional) -> Dict:
        """
        Envia email com propostas de assinatura após expiração
        
        Args:
            profissional: Objeto Profissional
            
        Returns:
            Dict com resultado do envio
        """
        if not profissional.email:
            return {'error': 'Profissional sem email cadastrado'}
        
        subject = "💼 Continue usando o Aracannabis - Escolha seu Plano"
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2196F3;">💼 Seu período trial expirou</h2>
            
            <p>Olá <strong>Dr(a). {profissional.nome}</strong>,</p>
            
            <p>Esperamos que tenha aproveitado o período de teste do <strong>Aracannabis</strong>!</p>
            
            <div style="background: #e3f2fd; border-left: 4px solid #2196F3; padding: 15px; margin: 20px 0;">
                <p style="margin: 0;">Seu acesso expirou, mas você pode continuar aproveitando todos os benefícios do sistema.</p>
            </div>
            
            <h3>🎯 Por que assinar o Aracannabis?</h3>
            
            <ul style="line-height: 1.8;">
                <li>📊 <strong>Gestão completa</strong> de prontuários e pacientes</li>
                <li>🤖 <strong>Assistência de IA</strong> para diagnósticos e dosagens</li>
                <li>📈 <strong>Relatórios automáticos</strong> e análises</li>
                <li>🏥 <strong>Gestão de associações</strong> e dispensações</li>
                <li>🔒 <strong>Segurança LGPD</strong> e backup automático</li>
                <li>📱 <strong>Acesso em qualquer lugar</strong></li>
            </ul>
            
            <div style="background: #ffffff; border: 2px solid #4CAF50; border-radius: 8px; padding: 25px; margin: 30px 0; text-align: center;">
                <h3 style="color: #4CAF50; margin-top: 0;">🎁 Oferta Especial</h3>
                <p style="font-size: 18px; margin: 15px 0;">Escolha o plano ideal para você</p>
                <p style="color: #666; margin-bottom: 20px;">Planos flexíveis com desconto para pagamento anual</p>
                <a href="http://localhost:3000/pricing" style="background: #4CAF50; color: white; padding: 15px 40px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; font-size: 16px;">Ver Planos e Assinar</a>
            </div>
            
            <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h4 style="margin-top: 0;">📋 Planos Disponíveis</h4>
                <p style="color: #666; margin: 10px 0;">
                    <strong>Básico:</strong> Ideal para profissionais individuais<br>
                    <strong>Profissional:</strong> Para clínicas e consultórios<br>
                    <strong>Enterprise:</strong> Para associações e redes de saúde
                </p>
                <p style="color: #666; font-size: 13px; margin-top: 15px;">
                    * Informações detalhadas e preços disponíveis na página de planos
                </p>
            </div>
            
            <p style="margin-top: 30px;">Precisa de ajuda para escolher? Entre em contato:</p>
            <p>📧 Email: contato@aracannabis.com.br<br>
            📱 WhatsApp: (11) 99999-9999<br>
            💬 Chat: Disponível no sistema</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="http://localhost:3000/pricing" style="background: #2196F3; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; display: inline-block;">Renovar Acesso Agora</a>
            </div>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
            <p style="color: #666; font-size: 12px;">Este email foi enviado automaticamente pelo sistema Aracannabis.</p>
        </div>
        """
        
        try:
            email_service = EmailService()
            return email_service.send_email(
                destinatario=profissional.email,
                assunto=subject,
                corpo_html=html_body,
                corpo_texto="Seu trial expirou. Continue usando o Aracannabis! Veja os planos em: http://localhost:3000/pricing"
            )
        except Exception as e:
            logger.error(f"Erro ao enviar proposta de assinatura: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def process_expirations() -> Dict:
        """
        Processa todos os profissionais próximos da expiração ou expirados
        Envia emails apropriados
        
        Returns:
            Dict com estatísticas do processamento
        """
        stats = {
            'warnings_sent': 0,
            'proposals_sent': 0,
            'errors': []
        }
        
        # 1. Avisar os que vão expirar em 2 dias
        expiring_soon = SubscriptionExpirationService.get_expiring_professionals(days_before=2)
        for prof in expiring_soon:
            try:
                result = SubscriptionExpirationService.send_expiration_warning(prof, days_remaining=2)
                if result.get('status') == 'sucesso':
                    stats['warnings_sent'] += 1
                    logger.info(f"Aviso enviado para {prof.nome}")
                else:
                    stats['errors'].append(f"Falha ao avisar {prof.nome}: {result.get('error')}")
            except Exception as e:
                stats['errors'].append(f"Erro ao processar {prof.nome}: {str(e)}")
        
        # 2. Enviar propostas para os já expirados
        expired = SubscriptionExpirationService.get_expired_professionals()
        for prof in expired:
            try:
                result = SubscriptionExpirationService.send_subscription_proposal(prof)
                if result.get('status') == 'sucesso':
                    stats['proposals_sent'] += 1
                    logger.info(f"Proposta enviada para {prof.nome}")
                else:
                    stats['errors'].append(f"Falha ao enviar proposta para {prof.nome}: {result.get('error')}")
            except Exception as e:
                stats['errors'].append(f"Erro ao processar {prof.nome}: {str(e)}")
        
        logger.info(f"Processamento concluído: {stats['warnings_sent']} avisos, {stats['proposals_sent']} propostas")
        return stats


# Função auxiliar para usar em cron jobs
def run_expiration_check():
    """Função para ser chamada por cron job"""
    logger.info("=== Iniciando verificação de expirações ===")
    stats = SubscriptionExpirationService.process_expirations()
    logger.info(f"=== Verificação concluída: {stats} ===")
    return stats
