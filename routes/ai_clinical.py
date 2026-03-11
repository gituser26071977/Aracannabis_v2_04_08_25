from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
import os
import logging

logger = logging.getLogger(__name__)

ai_clinical_bp = Blueprint('ai_clinical', __name__)

ANONYMIZATION_SERVICE_URL = os.getenv('ANONYMIZATION_SERVICE_URL', 'http://anonymization_service:8000')
LLM_GATEWAY_URL = os.getenv('LLM_GATEWAY_URL', 'http://llm_gateway:8000')

@ai_clinical_bp.route('/generate-soap', methods=['POST'])
@jwt_required()
def generate_soap():
    """
    Gera um resumo SOAP a partir de transcrição ou texto clínico.
    Pipeline: Backend -> Anonymizer -> LLM Gateway -> Backend -> Frontend
    """
    try:
        data = request.json
        consultation_id = data.get('consultation_id')
        patient_id = data.get('patient_id')
        text = data.get('text')
        task = data.get('task', 'soap_summary')

        if not text or not patient_id:
            return jsonify({'error': 'Missing required fields (text, patient_id)'}), 400

        # Identificar tenant (para rate limit no gateway)
        # Pode ser o ID do profissional ou uma claim no JWT
        # Por enquanto, usamos profissional_id como tenant_id simplificado
        tenant_id = get_jwt_identity()

        # 1. Anonimizar
        try:
            anon_resp = requests.post(f"{ANONYMIZATION_SERVICE_URL}/anonymize", json={
                "consultation_id": consultation_id or 0, # 0 se for avulso
                "patient_id": patient_id,
                "text": text
            }, timeout=10)
            
            if anon_resp.status_code != 200:
                logger.error(f"Erro na anonimização: {anon_resp.text}")
                return jsonify({'error': 'Erro ao anonimizar dados. Verifique consentimento.'}), anon_resp.status_code
            
            anon_data = anon_resp.json()
            anonymized_text = anon_data['anonymized_text']
            
        except requests.RequestException as e:
            logger.error(f"Falha ao contatar Anonymization Service: {e}")
            return jsonify({'error': 'Serviço de anonimização indisponível'}), 503

        # 2. Gerar com LLM Gateway
        try:
            # Carregar provedor preferencial das configurações
            config_path = os.path.join(current_app.root_path, 'config', 'ai_settings.json')
            provider = "zhipu" # Fallback
            if os.path.exists(config_path):
                import json
                try:
                    with open(config_path, 'r') as f:
                        settings = json.load(f)
                        provider = settings.get('chat_provider', 'zhipu')
                except: pass

            llm_resp = requests.post(f"{LLM_GATEWAY_URL}/generate", json={
                "consultation_id": consultation_id or 0,
                "tenant_id": tenant_id,
                "anonymized_text": anonymized_text,
                "task": task,
                "provider": provider
            }, timeout=45) # Timeout maior para LLM
            
            if llm_resp.status_code != 200:
                logger.error(f"Erro no LLM Gateway: {llm_resp.text}")
                return jsonify({'error': 'Falha na geração de IA'}), llm_resp.status_code
            
            llm_data = llm_resp.json()
            soap_output = llm_data['output']
            
        except requests.RequestException as e:
            logger.error(f"Falha ao contatar LLM Gateway: {e}")
            return jsonify({'error': 'Gateway de IA indisponível'}), 503

        # 3. Reidratar (Opcional - mas recomendado para exibir dados coerentes)
        # Se o SOAP contiver tokens como [DATE_01], queremos restaurar?
        # Sim, para o médico ver.
        # Iterar sobre os campos do SOAP e reidratar
        rehydrated_soap = {}
        for key, value in soap_output.items():
            if isinstance(value, str):
                try:
                    rehydrate_resp = requests.post(f"{ANONYMIZATION_SERVICE_URL}/rehydrate", json={
                        "consultation_id": consultation_id or 0,
                        "text": value
                    }, timeout=5)
                    if rehydrate_resp.status_code == 200:
                        rehydrated_soap[key] = rehydrate_resp.json()['original_text']
                    else:
                        rehydrated_soap[key] = value # Fallback
                except:
                    rehydrated_soap[key] = value
            else:
                rehydrated_soap[key] = value

        return jsonify({
            'soap': rehydrated_soap,
            'meta': {
                'tokens_used': llm_data['tokens_used'],
                'provider': llm_data['provider'],
                'processing_time_ms': llm_data['processing_time_ms']
            }
        }), 200

    except Exception as e:
        logger.error(f"Erro no endpoint generate-soap: {e}")
        return jsonify({'error': str(e)}), 500
