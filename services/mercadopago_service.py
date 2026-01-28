"""
Serviço de integração com Mercado Pago
Baseado na documentação oficial: https://www.mercadopago.com.br/developers/pt/reference
"""

import os
import mercadopago
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MercadoPagoService:
    def __init__(self):
        """Inicializa o serviço do Mercado Pago"""
        self.access_token = os.getenv('MERCADOPAGO_ACCESS_TOKEN')
        self.public_key = os.getenv('MERCADOPAGO_PUBLIC_KEY')
        self.webhook_secret = os.getenv('MERCADOPAGO_WEBHOOK_SECRET')
        self.sandbox = os.getenv('MERCADOPAGO_SANDBOX', 'True').lower() == 'true'
        self.notification_url = os.getenv('MERCADOPAGO_NOTIFICATION_URL')
        
        if not self.access_token:
            logger.warning("⚠️ MERCADOPAGO_ACCESS_TOKEN não configurado. Funcionalidades de pagamento estarão indisponíveis.")
            self.sdk = None
        else:
            # Inicializar SDK do Mercado Pago
            self.sdk = mercadopago.SDK(self.access_token)
        
        # Configurar sandbox se necessário
        if self.sandbox:
            logger.info("Mercado Pago configurado em modo SANDBOX")
        else:
            logger.info("Mercado Pago configurado em modo PRODUÇÃO")

    def criar_preferencia_pagamento(self, dados_pedido: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria uma preferência de pagamento no Mercado Pago
        
        Args:
            dados_pedido: Dados do pedido contendo informações do plano e cliente
            
        Returns:
            Dict com dados da preferência criada
        """
        try:
            if not self.sdk:
                return {"success": False, "error": "Integração Mercado Pago não configurada (Token ausente)"}

            # Calcular preços
            preco_info = self._calcular_preco(dados_pedido['plano'], dados_pedido['periodo'])
            plano_nome = self._get_plano_nome(dados_pedido['plano'])
            
            # Dados da preferência
            preference_data = {
                "items": [
                    {
                        "id": f"aracannabis_{dados_pedido['plano']}_{dados_pedido['periodo']}",
                        "title": f"Aracannabis - {plano_nome}",
                        "description": f"Assinatura {self._get_periodo_texto(dados_pedido['periodo'])} ({plano_nome})",
                        "category_id": "services",
                        "quantity": 1,
                        "currency_id": "BRL",
                        "unit_price": float(preco_info['final'])
                    }
                ],
                "payer": {
                    "name": dados_pedido.get('nome', ''),
                    "email": dados_pedido.get('email', ''),
                    "phone": {
                        "number": dados_pedido.get('telefone', '')
                    } if dados_pedido.get('telefone') else {}
                },
                "back_urls": {
                    "success": f"{self._get_base_url()}/pagamento-sucesso",
                    "failure": f"{self._get_base_url()}/pagamento-erro",
                    "pending": f"{self._get_base_url()}/pagamento-pendente"
                },
                "auto_return": "approved",
                "payment_methods": {
                    "excluded_payment_methods": [],
                    "excluded_payment_types": [],
                    "installments": 12  # Até 12x no cartão
                },
                "notification_url": self.notification_url,
                "statement_descriptor": "ARACANNABIS",
                "external_reference": f"aracannabis_{dados_pedido.get('user_id', 'guest')}_{int(datetime.now().timestamp())}",
                "expires": True,
                "expiration_date_from": datetime.now().isoformat(),
                "expiration_date_to": (datetime.now() + timedelta(hours=24)).isoformat(),
                "metadata": {
                    "plano": dados_pedido['plano'],
                    "periodo": dados_pedido['periodo'],
                    "user_id": dados_pedido.get('user_id'),
                    "email": dados_pedido.get('email'),
                    "nome": dados_pedido.get('nome'),
                    "sistema": "aracannabis",
                    "versao": "1.0"
                }
            }
            
            # Criar preferência
            preference_response = self.sdk.preference().create(preference_data)
            
            if preference_response["status"] == 201:
                preference = preference_response["response"]
                
                return {
                    "success": True,
                    "preference_id": preference["id"],
                    "init_point": preference["init_point"],
                    "sandbox_init_point": preference["sandbox_init_point"],
                    "public_key": self.public_key,
                    "sandbox": self.sandbox,
                    "qr_code": preference.get("qr_code"),
                    "qr_code_base64": preference.get("qr_code_base64"),
                    "ticket_url": preference.get("ticket_url")
                }
            else:
                logger.error(f"Erro ao criar preferência: {preference_response}")
                return {
                    "success": False,
                    "error": "Erro ao criar preferência de pagamento",
                    "details": preference_response
                }
                
        except Exception as e:
            logger.error(f"Erro no serviço Mercado Pago: {str(e)}")
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }

    def processar_webhook(self, dados_webhook: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa notificações de webhook do Mercado Pago
        
        Args:
            dados_webhook: Dados recebidos do webhook
            
        Returns:
            Dict com resultado do processamento
        """
        try:
            # Verificar tipo de notificação
            topic = dados_webhook.get('topic')
            resource_id = dados_webhook.get('resource')
            
            if topic == 'payment':
                return self._processar_notificacao_pagamento(resource_id)
            elif topic == 'merchant_order':
                return self._processar_notificacao_pedido(resource_id)
            else:
                logger.warning(f"Tipo de notificação não suportado: {topic}")
                return {"success": False, "error": "Tipo de notificação não suportado"}
                
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {str(e)}")
            return {"success": False, "error": str(e)}

    def consultar_pagamento(self, payment_id: str) -> Dict[str, Any]:
        """
        Consulta informações de um pagamento específico
        
        Args:
            payment_id: ID do pagamento no Mercado Pago
            
        Returns:
            Dict com informações do pagamento
        """
        try:
            payment_response = self.sdk.payment().get(payment_id)
            
            if payment_response["status"] == 200:
                payment = payment_response["response"]
                
                return {
                    "success": True,
                    "payment": {
                        "id": payment["id"],
                        "status": payment["status"],
                        "status_detail": payment["status_detail"],
                        "transaction_amount": payment["transaction_amount"],
                        "currency_id": payment["currency_id"],
                        "payment_method_id": payment["payment_method_id"],
                        "payment_type_id": payment["payment_type_id"],
                        "date_created": payment["date_created"],
                        "date_approved": payment.get("date_approved"),
                        "external_reference": payment.get("external_reference"),
                        "metadata": payment.get("metadata", {})
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Pagamento não encontrado",
                    "details": payment_response
                }
                
        except Exception as e:
            logger.error(f"Erro ao consultar pagamento: {str(e)}")
            return {"success": False, "error": str(e)}

    def _processar_notificacao_pagamento(self, payment_id: str) -> Dict[str, Any]:
        """Processa notificação de pagamento"""
        try:
            payment_info = self.consultar_pagamento(payment_id)
            
            if not payment_info["success"]:
                return payment_info
            
            payment = payment_info["payment"]
            status = payment["status"]
            
            # Processar baseado no status
            if status == "approved":
                # Pagamento aprovado - ativar assinatura
                return self._ativar_assinatura(payment)
            elif status == "pending":
                # Pagamento pendente - aguardar
                return {"success": True, "action": "pending", "payment": payment}
            elif status == "rejected":
                # Pagamento rejeitado - notificar usuário
                return {"success": True, "action": "rejected", "payment": payment}
            else:
                return {"success": True, "action": "unknown", "payment": payment}
                
        except Exception as e:
            logger.error(f"Erro ao processar notificação de pagamento: {str(e)}")
            return {"success": False, "error": str(e)}

    def _processar_notificacao_pedido(self, order_id: str) -> Dict[str, Any]:
        """Processa notificação de pedido"""
        try:
            # Consultar informações do pedido
            order_response = self.sdk.merchant_order().get(order_id)
            
            if order_response["status"] == 200:
                order = order_response["response"]
                return {"success": True, "action": "order_updated", "order": order}
            else:
                return {"success": False, "error": "Pedido não encontrado"}
                
        except Exception as e:
            logger.error(f"Erro ao processar notificação de pedido: {str(e)}")
            return {"success": False, "error": str(e)}

    def _ativar_assinatura(self, payment: Dict[str, Any]) -> Dict[str, Any]:
        """Ativa assinatura após pagamento aprovado"""
        try:
            metadata = payment.get("metadata", {})
            external_reference = payment.get("external_reference", "")
            
            # Extrair informações da assinatura
            plano = metadata.get("plano", "profissional")
            periodo = metadata.get("periodo", "mensal")
            user_id = metadata.get("user_id")
            
            # Calcular data de vencimento
            data_vencimento = self._calcular_data_vencimento(periodo)
            
            # Aqui você integraria com seu sistema de usuários/assinaturas
            # Por exemplo, atualizar tabela de assinaturas no banco de dados
            
            logger.info(f"Assinatura ativada - User: {user_id}, Plano: {plano}, Período: {periodo}")
            
            return {
                "success": True,
                "action": "subscription_activated",
                "payment": payment,
                "subscription": {
                    "user_id": user_id,
                    "plano": plano,
                    "periodo": periodo,
                    "data_vencimento": data_vencimento.isoformat(),
                    "payment_id": payment["id"]
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao ativar assinatura: {str(e)}")
            return {"success": False, "error": str(e)}

    def _calcular_preco(self, plano: str, periodo: str) -> Dict[str, float]:
        """Calcula preço baseado no período"""
        precos_base = {
            'sem_ia': 99.00,
            'com_ia': 250.00
        }
        preco_base = precos_base.get(plano, precos_base['sem_ia'])
        
        descontos = {
            'mensal': 0,
            'trimestral': 0.05,
            'semestral': 0.08,
            'anual': 0.12
        }
        
        multiplicadores = {
            'mensal': 1,
            'trimestral': 3,
            'semestral': 6,
            'anual': 12
        }
        
        preco_sem_desconto = preco_base * multiplicadores.get(periodo, 1)
        desconto = descontos.get(periodo, 0)
        preco_com_desconto = preco_sem_desconto * (1 - desconto)
        
        return {
            'original': preco_sem_desconto,
            'final': preco_com_desconto,
            'desconto': desconto * 100,
            'economia': preco_sem_desconto - preco_com_desconto
        }

    def _calcular_data_vencimento(self, periodo: str) -> datetime:
        """Calcula data de vencimento baseada no período"""
        agora = datetime.now()
        
        if periodo == 'mensal':
            return agora + timedelta(days=30)
        elif periodo == 'trimestral':
            return agora + timedelta(days=90)
        elif periodo == 'semestral':
            return agora + timedelta(days=180)
        elif periodo == 'anual':
            return agora + timedelta(days=365)
        else:
            return agora + timedelta(days=30)

    def _get_periodo_texto(self, periodo: str) -> str:
        """Converte período para texto legível"""
        textos = {
            'mensal': '1 mês',
            'trimestral': '3 meses',
            'semestral': '6 meses',
            'anual': '12 meses'
        }
        return textos.get(periodo, '1 mês')

    def _get_plano_nome(self, plano: str) -> str:
        """Converte plano para nome legível"""
        nomes = {
            'sem_ia': 'Plano Sem IA',
            'com_ia': 'Plano Com IA'
        }
        return nomes.get(plano, 'Plano Sem IA')

    def _get_base_url(self) -> str:
        """Retorna URL base da aplicação"""
        # Em produção, isso viria de uma variável de ambiente
        if self.sandbox:
            return "http://localhost:3000"
        else:
            return os.getenv('FRONTEND_BASE_URL') or os.getenv('BASE_URL', 'https://seu-dominio.com')

# Instância global do serviço
mercadopago_service = MercadoPagoService()
