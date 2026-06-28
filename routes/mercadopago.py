"""
Rotas para integração com Mercado Pago
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import re
from services.mercadopago_service import mercadopago_service
from services.webhook_handler import webhook_handler
from services.feature_flag_service import FeatureFlagService
from services.webhook_auth import mercadopago_webhook_required, register_webhook_event
from security_config import limiter

logger = logging.getLogger(__name__)

mercadopago_bp = Blueprint('mercadopago', __name__)

@mercadopago_bp.route('/criar-preferencia', methods=['POST'])
@jwt_required()
def criar_preferencia():
    """
    Cria uma preferência de pagamento no Mercado Pago
    """
    try:
        user_id = get_jwt_identity()
        dados = request.get_json()
        
        # Validar dados obrigatórios
        campos_obrigatorios = ['plano', 'periodo']
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {campo}'
                }), 400
        
        # Validar plano
        planos_validos = ['sem_ia', 'com_ia']
        if dados['plano'] not in planos_validos:
            return jsonify({
                'success': False,
                'error': 'Plano inválido'
            }), 400
        
        # Validar período
        periodos_validos = ['mensal', 'trimestral', 'semestral', 'anual']
        if dados['periodo'] not in periodos_validos:
            return jsonify({
                'success': False,
                'error': 'Período inválido'
            }), 400
        
        # Adicionar user_id aos dados
        dados['user_id'] = user_id
        
        # Criar preferência no Mercado Pago
        resultado = mercadopago_service.criar_preferencia_pagamento(dados)
        
        if resultado['success']:
            logger.info(f"Preferência criada para usuário {user_id}: {resultado['preference_id']}")
            return jsonify(resultado), 200
        else:
            logger.error(f"Erro ao criar preferência para usuário {user_id}: {resultado['error']}")
            return jsonify(resultado), 400
            
    except Exception as e:
        logger.error(f"Erro na rota criar_preferencia: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500


@mercadopago_bp.route('/criar-preferencia-publica', methods=['POST'])
def criar_preferencia_publica():
    """
    Cria uma preferência de pagamento sem autenticação (fluxo público)
    """
    try:
        dados = request.get_json() or {}

        campos_obrigatorios = ['plano', 'periodo', 'email']
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({
                    'success': False,
                    'error': f'Campo obrigatório: {campo}'
                }), 400

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', dados.get('email', '')):
            return jsonify({'success': False, 'error': 'Email inválido'}), 400

        planos_validos = ['sem_ia', 'com_ia']
        if dados['plano'] not in planos_validos:
            return jsonify({
                'success': False,
                'error': 'Plano inválido'
            }), 400

        periodos_validos = ['mensal', 'trimestral', 'semestral', 'anual']
        if dados['periodo'] not in periodos_validos:
            return jsonify({
                'success': False,
                'error': 'Período inválido'
            }), 400

        resultado = mercadopago_service.criar_preferencia_pagamento(dados)

        if resultado['success']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400
    except Exception as e:
        logger.error(f"Erro na rota criar_preferencia_publica: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

def _mp_extract_data_id(payload):
    """Extrai data.id do payload MP (suporta formato novo e antigo)."""
    if not isinstance(payload, dict):
        return ""
    data = payload.get('data') or {}
    if isinstance(data, dict):
        return str(data.get('id') or "")
    return str(payload.get('id') or "")


@mercadopago_bp.route('/webhook', methods=['POST'])
@limiter.exempt  # FASE 5A — webhook já validado por HMAC MP (FASE 4.5); não deve contar no rate limit
@mercadopago_webhook_required(get_data_id=_mp_extract_data_id)
def webhook():
    """
    Endpoint para receber notificações do Mercado Pago.
    Assinatura validada via padrao oficial MP (x-signature + x-request-id + data.id).
    Se new_billing_v2 estiver ativo, delega ao webhook_handler unificado.
    """
    try:
        dados_webhook = request.get_json()

        if not dados_webhook:
            dados_webhook = {
                'topic': request.form.get('topic'),
                'resource': request.form.get('resource'),
                'id': request.form.get('id')
            }

        # FASE 4.1 — Anti-replay atômico via INSERT + UNIQUE(provider, provider_event_id).
        # Substitui check_replay (race condition) por register_webhook_event.
        data_id = _mp_extract_data_id(dados_webhook)
        is_replay, log_id = register_webhook_event(
            provider="mercadopago",
            event_id=data_id,
            event_type="mercadopago_webhook",
            payload=dados_webhook,
        )
        if is_replay:
            logger.info(
                f"[mercadopago_webhook] replay detectado data_id={data_id} "
                f"log_id={log_id}"
            )
            return jsonify({'status': 'ok', 'idempotent': True}), 200

        logger.info(f"Webhook Mercado Pago recebido: data_id={data_id}")

        if FeatureFlagService.is_enabled('new_billing_v2'):
            resultado = webhook_handler.process('mercadopago', dados_webhook)
            if resultado['success']:
                return jsonify({'status': 'ok', 'idempotent': resultado.get('idempotent', False)}), 200
            else:
                return jsonify({'status': 'error', 'error': resultado.get('error')}), 200
        else:
            # Fallback para o serviço legado
            resultado = mercadopago_service.processar_webhook(dados_webhook)

            if resultado['success']:
                logger.info(f"Webhook processado com sucesso: {resultado}")
                if resultado.get('action') == 'subscription_activated':
                    subscription = resultado.get('subscription', {})
                    logger.info(f"Assinatura ativada: {subscription}")
                return jsonify({'status': 'ok'}), 200
            else:
                logger.error(f"Erro ao processar webhook: {resultado['error']}")
                return jsonify({'status': 'error'}), 400

    except Exception as e:
        logger.error(f"Erro no webhook: {str(e)}")
        return jsonify({'status': 'error'}), 500

@mercadopago_bp.route('/consultar-pagamento/<payment_id>', methods=['GET'])
@jwt_required()
def consultar_pagamento(payment_id):
    """
    Consulta informações de um pagamento específico
    """
    try:
        user_id = get_jwt_identity()
        
        resultado = mercadopago_service.consultar_pagamento(payment_id)
        
        if resultado['success']:
            logger.info(f"Pagamento consultado por usuário {user_id}: {payment_id}")
            return jsonify(resultado), 200
        else:
            logger.error(f"Erro ao consultar pagamento {payment_id}: {resultado['error']}")
            return jsonify(resultado), 404
            
    except Exception as e:
        logger.error(f"Erro na consulta de pagamento: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@mercadopago_bp.route('/status-integracao', methods=['GET'])
@jwt_required()
def status_integracao():
    """
    Verifica o status da integração com Mercado Pago
    """
    try:
        configuracoes = {
            'access_token_configurado': bool(mercadopago_service.access_token),
            'public_key_configurado': bool(mercadopago_service.public_key),
            'webhook_url_configurado': bool(mercadopago_service.notification_url),
            'sandbox_mode': mercadopago_service.sandbox
        }
        
        try:
            test_response = mercadopago_service.sdk.payment().search()
            sdk_funcionando = test_response.get('status') in [200, 404]
        except Exception:
            sdk_funcionando = False
        
        configuracoes['sdk_funcionando'] = sdk_funcionando
        configuracoes['integracao_ativa'] = all([
            configuracoes['access_token_configurado'],
            configuracoes['public_key_configurado'],
            configuracoes['sdk_funcionando']
        ])
        
        return jsonify({
            'success': True,
            'configuracoes': configuracoes
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar status da integração: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao verificar integração'
        }), 500

@mercadopago_bp.route('/calcular-preco', methods=['POST'])
def calcular_preco():
    """
    Calcula preço baseado no período (endpoint público)
    """
    try:
        dados = request.get_json()
        periodo = dados.get('periodo', 'mensal')
        plano = dados.get('plano', 'sem_ia')
        
        periodos_validos = ['mensal', 'trimestral', 'semestral', 'anual']
        if periodo not in periodos_validos:
            return jsonify({
                'success': False,
                'error': 'Período inválido'
            }), 400

        planos_validos = ['sem_ia', 'com_ia']
        if plano not in planos_validos:
            return jsonify({
                'success': False,
                'error': 'Plano inválido'
            }), 400
        
        precos_base = {
            'sem_ia': 99.00,
            'com_ia': 250.00
        }

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

        preco_base = precos_base[plano]
        preco_sem_desconto = preco_base * multiplicadores[periodo]
        desconto = descontos[periodo]
        preco_com_desconto = preco_sem_desconto * (1 - desconto)
        
        resultado = {
            'success': True,
            'plano': plano,
            'periodo': periodo,
            'preco': {
                'original': preco_sem_desconto,
                'final': preco_com_desconto,
                'desconto_percentual': desconto * 100,
                'economia': preco_sem_desconto - preco_com_desconto
            }
        }
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Erro ao calcular preço: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@mercadopago_bp.route('/public-key', methods=['GET'])
def get_public_key():
    """
    Retorna a public key do Mercado Pago (endpoint público para o frontend)
    """
    try:
        return jsonify({
            'success': True,
            'public_key': mercadopago_service.public_key,
            'sandbox': mercadopago_service.sandbox
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter public key: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

# Registrar blueprint
def register_mercadopago_routes(app):
    """Registra as rotas do Mercado Pago"""
    app.register_blueprint(mercadopago_bp, url_prefix='/api/mercadopago')
