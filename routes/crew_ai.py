"""
Rotas para o sistema multi-agente CrewAI do Aracannabis
"""

import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime

from models import db, Profissional, LogAtividade, Paciente
from services.crew_agents import sistema_agentes
from services.email_service import EmailService
from security_config import sanitize_input

crew_ai_bp = Blueprint('crew_ai', __name__)
logger = logging.getLogger(__name__)

# Middleware para verificar permissões
def crew_ai_required(f):
    """Decorator para verificar se o usuário pode usar o sistema multi-agente"""
    from functools import wraps
    
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        profissional = Profissional.query.get(int(current_user_id))
        
        if not profissional or profissional.role not in ['admin', 'profissional']:
            return jsonify({'error': 'Acesso negado. Permissão necessária.'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@crew_ai_bp.route('/processar', methods=['POST'])
@crew_ai_required
def processar_solicitacao():
    """Processa solicitação do usuário usando sistema multi-agente"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        # Validar dados obrigatórios
        if 'solicitacao' not in data:
            return jsonify({'error': 'Solicitação é obrigatória'}), 400
        
        solicitacao = data['solicitacao']
        paciente_id = data.get('paciente_id')
        contexto = data.get('contexto', {})
        # Inclui o usuário atual para ferramentas de criação
        contexto['profissional_id'] = current_user_id
        
        # Verificar se paciente existe (se fornecido)
        if paciente_id:
            paciente = Paciente.query.get(paciente_id)
            if not paciente:
                return jsonify({'error': 'Paciente não encontrado'}), 404
            
            # Adicionar informações do paciente ao contexto
            contexto['paciente_info'] = {
                'nome': paciente.nome,
                'condicao_medica': paciente.condicao_medica,
                'email': paciente.email
            }
        
        # Processar solicitação
        resultado = sistema_agentes.processar_solicitacao(
            solicitacao=solicitacao,
            paciente_id=paciente_id,
            contexto=contexto
        )
        
        # Registrar log de atividade
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='PROCESSAR_SOLICITACAO_AGENTES',
            detalhes=f"Solicitação processada por sistema multi-agente: {solicitacao[:100]}..."
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Erro ao processar solicitação com agentes: {str(e)}")
        return jsonify({'error': f'Erro ao processar solicitação: {str(e)}'}), 500

@crew_ai_bp.route('/gerar-relatorio', methods=['POST'])
@crew_ai_required
def gerar_relatorio():
    """Gera relatório completo do paciente usando sistema multi-agente"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        # Validar dados obrigatórios
        if 'paciente_id' not in data:
            return jsonify({'error': 'ID do paciente é obrigatório'}), 400
        
        paciente_id = data['paciente_id']
        tipo_relatorio = data.get('tipo_relatorio', 'clinico')
        
        # Verificar se paciente existe
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Gerar relatório
        resultado = sistema_agentes.gerar_relatorio(paciente_id, tipo_relatorio)
        
        # Registrar log de atividade
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='GERAR_RELATORIO_AGENTES',
            detalhes=f"Relatório gerado para paciente {paciente.nome} (ID: {paciente_id})"
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório com agentes: {str(e)}")
        return jsonify({'error': f'Erro ao gerar relatório: {str(e)}'}), 500

@crew_ai_bp.route('/analisar-exame', methods=['POST'])
@crew_ai_required
def analisar_exame():
    """Analisa exame usando agente biomédico"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        # Validar dados obrigatórios
        if 'texto_exame' not in data:
            return jsonify({'error': 'Texto do exame é obrigatório'}), 400
        
        texto_exame = data['texto_exame']
        paciente_id = data.get('paciente_id')
        
        # Adicionar contexto do paciente se fornecido
        contexto = {}
        if paciente_id:
            paciente = Paciente.query.get(paciente_id)
            if paciente:
                contexto['paciente'] = {
                    'nome': paciente.nome,
                    'condicao_medica': paciente.condicao_medica
                }
        
        # Analisar exame
        resultado = sistema_agentes.analisar_exame(texto_exame)
        
        # Registrar log de atividade
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='ANALISAR_EXAME_AGENTES',
            detalhes=f"Exame analisado por agente biomédico (Paciente ID: {paciente_id or 'N/A'})"
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Erro ao analisar exame com agentes: {str(e)}")
        return jsonify({'error': f'Erro ao analisar exame: {str(e)}'}), 500

@crew_ai_bp.route('/sugerir-ajuste-tratamento', methods=['POST'])
@crew_ai_required
def sugerir_ajuste_tratamento():
    """Sugere ajuste de tratamento usando agente farmacêutico"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        # Validar dados obrigatórios
        required_fields = ['paciente_id', 'medicamento', 'contexto_atual']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Campos obrigatórios: {", ".join(required_fields)}'}), 400
        
        paciente_id = data['paciente_id']
        medicamento = data['medicamento']
        contexto_atual = data['contexto_atual']
        
        # Verificar se paciente existe
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Sugerir ajuste
        resultado = sistema_agentes.sugerir_ajuste_tratamento(
            paciente_id, medicamento, contexto_atual
        )
        
        # Registrar log de atividade
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='SUGERIR_AJUSTE_TRATAMENTO',
            detalhes=f"Ajuste de tratamento sugerido para paciente {paciente.nome} - Medicamento: {medicamento}"
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Erro ao sugerir ajuste de tratamento: {str(e)}")
        return jsonify({'error': f'Erro ao sugerir ajuste: {str(e)}'}), 500

@crew_ai_bp.route('/enviar-relatorio-email', methods=['POST'])
@crew_ai_required
def enviar_relatorio_email():
    """Gera e envia relatório por email usando sistema multi-agente"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        # Validar dados obrigatórios
        required_fields = ['paciente_id', 'destinatario']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Campos obrigatórios: {", ".join(required_fields)}'}), 400
        
        paciente_id = data['paciente_id']
        destinatario = data['destinatario']
        tipo_relatorio = data.get('tipo_relatorio', 'clinico')
        assunto = data.get('assunto', f'Relatório Médico - {tipo_relatorio.title()}')
        
        # Verificar se paciente existe
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return jsonify({'error': 'Paciente não encontrado'}), 404
        
        # Gerar relatório
        relatorio_resultado = sistema_agentes.gerar_relatorio(paciente_id, tipo_relatorio)
        
        if 'error' in relatorio_resultado:
            return jsonify(relatorio_resultado), 400
        
        relatorio = relatorio_resultado.get('relatorio', '')
        
        # Preparar corpo do email - processar relatório para HTML
        relatorio_html = relatorio.replace('\n', '<br>')
        
        corpo_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{assunto}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; border-radius: 5px; }}
                .content {{ padding: 20px; background-color: #f9f9f9; border-radius: 5px; margin-top: 20px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏥 Relatório Médico - Aracannabis</h1>
                    <p>Paciente: {paciente.nome} | Data: {datetime.now().strftime('%d/%m/%Y')}</p>
                </div>
                
                <div class="content">
                    {relatorio_html}
                </div>
                
                <div class="footer">
                    <p>Este relatório foi gerado automaticamente pelo sistema Aracannabis usando inteligência artificial.</p>
                    <p>Em caso de dúvidas, entre em contato com o profissional responsável.</p>
                    <p><strong>Sistema Aracannabis</strong> - Assistência Médica Inteligente</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        corpo_texto = f"""
        Relatório Médico - Aracannabis
        
        Paciente: {paciente.nome}
        Data: {datetime.now().strftime('%d/%m/%Y')}
        
        {relatorio}
        
        ---
        Este relatório foi gerado automaticamente pelo sistema Aracannabis usando inteligência artificial.
        Em caso de dúvidas, entre em contato com o profissional responsável.
        
        Sistema Aracannabis - Assistência Médica Inteligente
        """
        
        # Enviar email
        email_service = EmailService()
        sucesso = email_service.send_email(destinatario, assunto, corpo_html, corpo_texto)
        
        if sucesso:
            # Registrar log de atividade
            log = LogAtividade(
                profissional_id=current_user_id,
                acao='ENVIAR_RELATORIO_EMAIL',
                detalhes=f"Relatório enviado por email para {destinatario} (Paciente: {paciente.nome})"
            )
            db.session.add(log)
            db.session.commit()
            
            return jsonify({
                'status': 'sucesso',
                'message': f'Relatório enviado com sucesso para {destinatario}',
                'paciente': paciente.nome,
                'tipo_relatorio': tipo_relatorio
            }), 200
        else:
            return jsonify({
                'status': 'erro',
                'message': 'Falha ao enviar email'
            }), 500
        
    except Exception as e:
        logger.error(f"Erro ao enviar relatório por email: {str(e)}")
        return jsonify({'error': f'Erro ao enviar relatório: {str(e)}'}), 500


@crew_ai_bp.route('/chat', methods=['POST'])
@crew_ai_required
def chat():
    """Chat com o agente conversacional (com acesso às demais ferramentas)."""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        data = sanitize_input(data)

        mensagem = data.get('mensagem') or data.get('solicitacao')
        paciente_id = data.get('paciente_id')
        contexto_extra = data.get('contexto', {})

        contexto_extra['profissional_id'] = current_user_id

        if not mensagem:
            return jsonify({'error': 'Mensagem é obrigatória'}), 400

        resultado = sistema_agentes.processar_solicitacao(
            solicitacao=mensagem,
            paciente_id=paciente_id,
            contexto=contexto_extra
        )

        # Registrar log de atividade
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='CHAT_MULTIAGENTE',
            detalhes=f'Chat multiagente iniciado (paciente: {paciente_id or "N/A"})'
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'mensagem': mensagem,
            'resposta': resultado,
            'paciente_id': paciente_id,
            'contexto': contexto_extra,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Erro no chat multiagente: {str(e)}")
        return jsonify({'error': f'Erro ao processar chat: {str(e)}'}), 500

@crew_ai_bp.route('/whatsapp-webhook', methods=['POST'])
def whatsapp_webhook():
    """
    Webhook para receber mensagens do WhatsApp via Evolution API
    
    SEGURANÇA:
    - Requer X-Webhook-Secret header para autenticação
    - Rate limiting: máximo 10 mensagens por minuto por telefone
    - IP whitelist opcional via WEBHOOK_IP_WHITELIST
    """
    from middleware.webhook_auth import webhook_rate_limiter
    
    # 1. Validar autenticação (X-Webhook-Secret)
    webhook_secret = os.environ.get('WEBHOOK_SECRET_KEY')
    
    if webhook_secret:  # Se configurado, validar
        provided_secret = request.headers.get('X-Webhook-Secret')
        
        if not provided_secret:
            logger.warning(f"Tentativa de acesso ao webhook WhatsApp sem autenticação do IP: {request.remote_addr}")
            return jsonify({
                'error': 'Autenticação necessária',
                'message': 'Header X-Webhook-Secret não fornecido'
            }), 401
        
        if provided_secret != webhook_secret:
            logger.error(f"Tentativa de acesso ao webhook WhatsApp com secret inválido do IP: {request.remote_addr}")
            return jsonify({
                'error': 'Autenticação falhou',
                'message': 'X-Webhook-Secret inválido'
            }), 403
    else:
        # Apenas log warning em desenvolvimento
        if os.environ.get('FLASK_ENV') != 'development':
            logger.error("WEBHOOK_SECRET_KEY não configurado em produção!")
    
    try:
        data = request.get_json()
        
        # Log do webhook recebido (sem dados sensíveis)
        logger.info(f"Webhook WhatsApp autenticado recebido do IP: {request.remote_addr}")
        
        # Validar estrutura básica do webhook
        if not data or 'messages' not in data:
            return jsonify({'status': 'ignored', 'message': 'Estrutura inválida'}), 400
        
        messages = data['messages']
        respostas = []
        
        for msg in messages:
            phone = msg.get('from', '').replace('@c.us', '')
            text = msg.get('body', '')
            message_id = msg.get('id', '')

            if not text or not phone:
                continue
            
            # 2. Rate limiting por telefone
            is_allowed, rate_message = webhook_rate_limiter(phone)
            if not is_allowed:
                logger.warning(f"Rate limit excedido para WhatsApp {phone}")
                respostas.append({
                    'phone': phone,
                    'message_id': message_id,
                    'resposta': '⚠️ Muitas mensagens em um curto período. Aguarde um momento e tente novamente.'
                })
                continue

            logger.info(f"Mensagem WhatsApp de {phone}: {text[:100]}...")

            resultado = sistema_agentes.processar_solicitacao(
                solicitacao=text,
                paciente_id=None,
                contexto={'whatsapp': True, 'telefone': phone}
            )

            resposta_texto = resultado.get('resultado', '')
            respostas.append({
                'phone': phone,
                'message_id': message_id,
                'resposta': resposta_texto
            })

            logger.info(f"Resposta gerada para WhatsApp {phone}: {str(resposta_texto)[:100]}...")

        return jsonify({'status': 'received', 'responses': respostas}), 200
        
    except Exception as e:
        logger.error(f"Erro no webhook WhatsApp: {str(e)}")
        return jsonify({'error': 'Erro interno'}), 500
