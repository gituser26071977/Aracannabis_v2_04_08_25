"""
Rota de chat simplificada que funciona melhor com modelos locais pequenos
Não depende de function calling - busca dados diretamente

SEGURANÇA: Implementa validação de acesso a pacientes (multi-tenant).
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
import base64
import os
from typing import Dict, Optional

import google.generativeai as genai
from models import db, Paciente, Evolucao, Dosagem, Sintoma, CompartilhamentoPaciente, Profissional
from services.ai_agents import ai_manager
from services.ai_config_storage import get_api_key
from security_config import sanitize_input

ai_chat_simples_bp = Blueprint('ai_chat_simples', __name__)
logger = logging.getLogger(__name__)


def _validar_acesso_paciente(paciente_id: int, profissional_id: int) -> bool:
    """
    Valida se o profissional tem acesso ao paciente.
    Um profissional pode acessar pacientes que:
    1. São de sua responsabilidade (profissional_responsavel_id)
    2. Foram compartilhados com ele (compartilhamentos_pacientes)
    3. São de sua associação (para admins)
    
    Returns:
        True se tem acesso, False caso contrário
    """
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        logger.warning(f"Paciente {paciente_id} não encontrado")
        return False
    
    profissional = Profissional.query.get(profissional_id)
    if not profissional:
        logger.warning(f"Profissional {profissional_id} não encontrado")
        return False
    
    # Admin e superadmin têm acesso total
    if profissional.role in ('admin', 'superadmin'):
        logger.info(f"Admin {profissional_id} acessando paciente {paciente_id}")
        return True
    
    # Verificar se é o profissional responsável
    if paciente.profissional_responsavel_id == profissional_id:
        logger.info(f"Profissional {profissional_id} é responsável pelo paciente {paciente_id}")
        return True
    
    # Verificar se tem compartilhamento ativo
    compartilhamento = CompartilhamentoPaciente.query.filter_by(
        paciente_id=paciente_id,
        profissional_id=profissional_id,
        ativo=True
    ).first()
    
    if compartilhamento:
        logger.info(f"Profissional {profissional_id} tem compartilhamento do paciente {paciente_id}")
        return True
    
    logger.warning(f"Acesso negado: Profissional {profissional_id} tentou acessar paciente {paciente_id}")
    return False


def buscar_contexto_paciente(paciente_id: int, profissional_id: int) -> Optional[Dict]:
    """Busca todos os dados do paciente para incluir no contexto.
    SOMENTE retorna dados se o profissional tiver acesso ao paciente.
    
    Args:
        paciente_id: ID do paciente a ser buscado
        profissional_id: ID do profissional que solicita os dados
        
    Returns:
        Dict com dados do paciente ou None se não tiver acesso
    """
    # PRIMEIRO: Validar acesso ao paciente
    if not _validar_acesso_paciente(paciente_id, profissional_id):
        return None
    
    # Buscar paciente
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return None

    try:
        # Buscar últimas evoluções
        evolucoes = Evolucao.query.filter_by(paciente_id=paciente_id)\
            .order_by(Evolucao.data_evolucao.desc())\
            .limit(5).all()

        # Buscar últimas dosagens
        dosagens = Dosagem.query.filter_by(paciente_id=paciente_id)\
             .order_by(Dosagem.data.desc())\
             .limit(10).all()

        # Buscar últimos sintomas
        sintomas = Sintoma.query.filter_by(paciente_id=paciente_id)\
             .order_by(Sintoma.data.desc())\
             .limit(15).all()

        contexto = {
            "paciente": {
                "id": paciente.id,
                "nome": paciente.nome,
                "condicao_medica": paciente.condicao_medica or "Não informada",
                "diagnostico": paciente.diagnostico or "Não informado",
                "em_tratamento": paciente.em_tratamento,
                "data_nascimento": str(paciente.data_nascimento) if paciente.data_nascimento else None
            },
            "evolucoes_recentes": [
                {
                    "data": str(e.data_evolucao.date()) if e.data_evolucao else "",
                    "nota": e.nota_evolucao[:200] if e.nota_evolucao else ""
                } for e in evolucoes
            ],
            "dosagens_recentes": [
                {
                    "data": str(d.data),
                    "dosagem": d.dosagem,
                    "gotas": d.gotas,
                    "frequencia_diaria": d.frequencia_diaria,
                    "cbd": d.concentracao_cbd,
                    "thc": d.concentracao_thc
                } for d in dosagens
            ],
            "sintomas_recentes": [
                {
                    "data": str(s.data),
                    "sintoma": s.sintoma,
                    "intensidade": s.intensidade
                } for s in sintomas
            ]
        }

        logger.info(f"Contexto do paciente {paciente_id} retornado para profissional {profissional_id}")
        return contexto

    except Exception as e:
        logger.error(f"Erro ao buscar contexto do paciente: {str(e)}")
        return None


@ai_chat_simples_bp.route('/chat-simples', methods=['POST'])
@jwt_required()
def chat_simples():
    """
    Chat simplificado que funciona melhor com modelos locais menores
    Não usa function calling - passa todos os dados no contexto
    
    SEGURANÇA: Verifica acesso ao paciente antes de retornar dados.
    """
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        data = sanitize_input(data)

        mensagem = data.get('mensagem')
        paciente_id = data.get('paciente_id')

        if not mensagem:
            return jsonify({'error': 'Mensagem é obrigatória'}), 400

        # Se tiver paciente_id, buscar contexto completo COM VALIDAÇÃO DE ACESSO
        contexto_texto = ""
        if paciente_id:
            contexto = buscar_contexto_paciente(paciente_id, current_user_id)
            
            # Se contexto é None, significa que não tem acesso
            if contexto is None:
                logger.warning(f"Chat simples: Acesso negado ao paciente {paciente_id} para usuário {current_user_id}")
                return jsonify({
                    'error': 'Paciente não encontrado ou você não tem permissão para acessar seus dados',
                    'codigo': 'ACESSO_NEGADO'
                }), 403

            paciente = contexto['paciente']
            contexto_texto = f"""
DADOS DO PACIENTE:
Nome: {paciente['nome']}
Condição Médica: {paciente['condicao_medica']}
Diagnóstico: {paciente['diagnostico']}
Em tratamento: {'Sim' if paciente['em_tratamento'] else 'Não'}

EVOLUÇÕES CLÍNICAS RECENTES ({len(contexto['evolucoes_recentes'])}):
"""
            for i, ev in enumerate(contexto['evolucoes_recentes'], 1):
                contexto_texto += f"\n{i}. [{ev['data']}] {ev['nota']}"

            contexto_texto += f"\n\nDOSAGENS RECENTES ({len(contexto['dosagens_recentes'])}):"
            for i, dos in enumerate(contexto['dosagens_recentes'], 1):
                gotas_info = f"{dos['gotas']} gotas" if dos.get('gotas') else ""
                freq_info = f"{dos['frequencia_diaria']}x/dia" if dos.get('frequencia_diaria') else ""
                cbd_info = f"CBD: {dos['cbd']}%" if dos.get('cbd') else ""
                thc_info = f"THC: {dos['thc']}%" if dos.get('thc') else ""
                info_parts = [p for p in [gotas_info, freq_info, cbd_info, thc_info] if p]
                info_str = " - " + ", ".join(info_parts) if info_parts else ""
                contexto_texto += f"\n{i}. [{dos['data']}] {dos['dosagem']}{info_str}"

            contexto_texto += f"\n\nSINTOMAS RECENTES ({len(contexto['sintomas_recentes'])}):"
            for i, sint in enumerate(contexto['sintomas_recentes'], 1):
                contexto_texto += f"\n{i}. [{sint['data']}] {sint['sintoma']} (Intensidade: {sint['intensidade']}/10)"
        else:
            contexto_texto = "\n[Nenhum dado de paciente disponível - sem acesso ou paciente não existe]"

        # Montar prompt para a IA
        system_prompt = """Você é um assistente médico especializado em cannabis medicinal.

Suas responsabilidades:
- Analisar dados de pacientes e fornecer insights úteis
- Responder perguntas sobre tratamentos, dosagens e evolução clínica
- Manter um tom profissional e empático
- SEMPRE usar os dados fornecidos no contexto para responder
- Se não houver dados suficientes, informar claramente

IMPORTANTE: Base suas respostas EXCLUSIVAMENTE nos dados fornecidos. Não invente informações."""

        # Combinar prompt do sistema com o contexto do paciente se houver
        if contexto_texto:
            system_prompt += f"\n\nCONTEXTO DO PACIENTE:\n{contexto_texto}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": mensagem}
        ]

        # Chamar a IA
        logger.info(f"Chat simples - Usuário {current_user_id}, Paciente: {paciente_id}")

        response = ai_manager.chat_completion(
            messages=messages,
            temperature=0.5,
            max_tokens=2000
        )

        return jsonify({
            'mensagem': mensagem,
            'paciente_id': paciente_id,
            'resposta': response.get('content', 'Desculpe, não consegui processar a resposta.'),
            'tem_contexto': bool(contexto_texto),
            'provider': response.get('provider'),
            'model': response.get('model')
        }), 200

    except Exception as e:
        logger.error(f"Erro no chat simples: {str(e)}")
        return jsonify({'error': str(e)}), 500


@ai_chat_simples_bp.route('/stt', methods=['POST'])
@jwt_required()
def speech_to_text():
    """
    Usa o modelo multimodal (Gemini 2.5 Flash Lite) para transcrever um áudio no formato dictation.
    """
    try:
        data = request.get_json()
        audio_b64 = data.get('audio')
        if not audio_b64:
            return jsonify({'error': 'Áudio base64 não fornecido'}), 400

        # Pegar chave do google configurada e configurar API
        api_key = get_api_key('google') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return jsonify({'error': 'Configuração do provedor Google não encontrada'}), 500
        
        genai.configure(api_key=api_key)
        
        # Limpar prefixo base64 se vier inteiro do js ("data:audio/webm;base64,...")
        if ',' in audio_b64:
            mime_part, audio_b64 = audio_b64.split(',', 1)
            mime_type = mime_part.split(':')[1].split(';')[0]
        else:
            mime_type = "audio/webm"

        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        response = model.generate_content([
            "Transcreva com extrema precisão o áudio deste paciente ou médico em português (Brasil). Retorne APENAS o texto transcrito, sem introduções.",
            {
                "mime_type": mime_type,
                "data": audio_b64
            }
        ])
        
        return jsonify({'text': response.text.strip()})
        
    except Exception as e:
        logger.error(f"Erro STT: {str(e)}")
        return jsonify({'error': f"Falha ao transcrever: {str(e)}"}), 500


@ai_chat_simples_bp.route('/tts', methods=['POST'])
@jwt_required()
def text_to_speech():
    """
    Gera áudio de saída. 
    Idealmente usando TTS-1 da OpenAI ou preview do Gemini, 
    já que Gemini TTS Preview pode estar restrito.
    """
    try:
        data = request.get_json()
        text = data.get('text')
        if not text:
            return jsonify({'error': 'Texto não fornecido'}), 400

        from openai import OpenAI
        api_key = get_api_key('openai') or os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'error': 'Configuração OpenAI não encontrada para TTS'}), 500
            
        client = OpenAI(api_key=api_key)
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        # Converter para base64 para uso fácil no frontend sem arquivos no disco
        audio_data = response.content
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        return jsonify({
            'audio_base64': f"data:audio/mp3;base64,{audio_b64}"
        })
        
    except Exception as e:
        logger.error(f"Erro TTS: {str(e)}")
        return jsonify({'error': f"Falha na síntese de voz: {str(e)}"}), 500


@ai_chat_simples_bp.route('/chat-simples/test', methods=['GET'])
@jwt_required()
def test_chat_simples():
    """Endpoint de teste para o chat simples"""
    return jsonify({
        'status': 'online',
        'message': 'Chat simples disponível',
        'provider': ai_manager.default_provider,
        'model': ai_manager.default_model
    }), 200