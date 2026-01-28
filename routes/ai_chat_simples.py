"""
Rota de chat simplificada que funciona melhor com modelos locais pequenos
Não depende de function calling - busca dados diretamente
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from models import db, Paciente, Evolucao, Dosagem, Sintoma
from services.ai_agents import ai_manager
from security_config import sanitize_input

ai_chat_simples_bp = Blueprint('ai_chat_simples', __name__)
logger = logging.getLogger(__name__)

def buscar_contexto_paciente(paciente_id):
    """Busca todos os dados do paciente para incluir no contexto"""
    try:
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return None

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
    """
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        data = sanitize_input(data)

        mensagem = data.get('mensagem')
        paciente_id = data.get('paciente_id')

        if not mensagem:
            return jsonify({'error': 'Mensagem é obrigatória'}), 400

        # Se tiver paciente_id, buscar contexto completo
        contexto_texto = ""
        if paciente_id:
            contexto = buscar_contexto_paciente(paciente_id)

            if contexto:
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
                contexto_texto = f"\nPaciente ID {paciente_id} encontrado mas sem dados adicionais."

        # Montar prompt para a IA
        system_prompt = """Você é um assistente médico especializado em cannabis medicinal.

Suas responsabilidades:
- Analisar dados de pacientes e fornecer insights úteis
- Responder perguntas sobre tratamentos, dosagens e evolução clínica
- Manter um tom profissional e empático
- SEMPRE usar os dados fornecidos no contexto para responder
- Se não houver dados suficientes, informar claramente

IMPORTANTE: Base suas respostas EXCLUSIVAMENTE nos dados fornecidos. Não invente informações."""

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Se tiver contexto de paciente, adicionar
        if contexto_texto:
            messages.append({
                "role": "system",
                "content": f"CONTEXTO DO PACIENTE:\n{contexto_texto}"
            })

        # Adicionar mensagem do usuário
        messages.append({
            "role": "user",
            "content": mensagem
        })

        # Chamar a IA
        logger.info(f"Chat simples - Usuário {current_user_id}, Paciente: {paciente_id}")

        response = ai_manager.chat_completion(
            messages=messages,
            temperature=0.5,
            max_tokens=2000
        )

        resposta = response.get('content', 'Desculpe, não consegui gerar uma resposta.')

        return jsonify({
            'mensagem': mensagem,
            'resposta': resposta,
            'paciente_id': paciente_id,
            'provider': response.get('provider'),
            'model': response.get('model'),
            'tem_contexto': bool(contexto_texto)
        }), 200

    except Exception as e:
        logger.error(f"Erro no chat simples: {str(e)}", exc_info=True)
        return jsonify({'error': f'Erro ao processar chat: {str(e)}'}), 500

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
