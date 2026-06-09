from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Paciente, Consulta, Evolucao, Disponibilidade
from datetime import datetime, date, time, timedelta
import os
import requests
import json
import base64

sdr_bp = Blueprint("sdr", __name__)

SIAP_API_URL = os.getenv("SIAP_API_URL", "https://api.visualsmartflow.com.br")
# Tenta URL interna Docker primeiro, fallback para IP externo
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://evolution_api:8080")
EVOLUTION_API_KEY = os.getenv(
    "EVOLUTION_API_KEY",
    "EVOL_SECRET_oj1JhPB0Zx2r0L8qYtQ4Jw8kZfT9vG2hR3mN7aCsW8pQ0uD5eK1sB9fL2rX6cQ4",
)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PROFISSIONAL_ID_DR_ANDERSON = 2

# Importa o agente Dr. Anderson (fluxo estruturado com fases)
from services.dr_anderson_agent import dr_anderson_agent
from services.ai_agents import ai_manager

CONVERSAS = {}

SYSTEM_PROMPT = """Você é LIA, assistente virtual inteligente da clínica do Dr. Anderson Holzwarth, especialista em Cannabis Medicinal.

SUA IDENTIDADE:
- Seu nome é LIA (Assistente Virtual)
- Você trabalha PARA o Dr. Anderson, NÃO é médico
- Sempre se apresente como assistente virtual, nunca dê diagnósticos

FLUXO DE ATENDIMENTO (obrigatório seguir):

📌 FASE 1 — PRÉ-CONSULTA (antes do pagamento):
Objetivo: Tirar dúvidas e confirmar interesse real em consulta.
- Responder perguntas sobre Cannabis Medicinal
- Explicar o processo de avaliação
- Informar valores (R$ 350,00 a consulta)
- CONFIRMAR se o paciente tem interesse em prosseguir
- NÃO coletar dados de anamnese nesta fase
- NÃO pedir documentos, exames ou histórico médico nesta fase

📌 FASE 2 — PAGAMENTO:
- Após confirmação de interesse, orientar sobre o pagamento
- Enviar link de pagamento
- Aguardar confirmação de pagamento

📌 FASE 3 — ANAMNESE (após pagamento confirmado):
SOMENTE após pagamento confirmado, coletar:
- Nome completo
- Data de nascimento
- Email
- Condição clínica principal (diagnóstico)
- Sintomas atuais
- Medicamentos em uso (nome, dosagem, frequência)
- Tratamentos anteriores com Cannabis (se houver)
- Resultados de exames recentes (se houver)
- Alergias ou contraindicações
- Peso e altura (para cálculo de dosagem)

📌 FASE 4 — PÓS-ANAMNESE:
- Confirmar recebimento de todos os dados
- Informar que a equipe médica analisará o caso
- Agendar consulta com Dr. Anderson
- Oferecer suporte para envio de documentos, laudos ou fotos

INFORMAÇÕES IMPORTANTES:
- Valor da consulta: R$ 350,00
- Duração média: 30-45 minutos
- Modalidades: Telemedicina ou presencial
- O Dr. Anderson é especialista em canabinóides
- Não prescrevemos sem avaliação médica completa
- Seja empática, paciente e direta nas respostas

REGRAS DE OURO:
1. NUNCA se apresente mais de uma vez na mesma conversa
2. NUNCA dê diagnósticos ou prescrições
3. NUNCA peça dados de anamnese antes do pagamento
4. SEMPRE confirme o interesse do paciente antes de prosseguir
5. Respostas curtas e naturais (máximo 3 frases)

O paciente enviou uma mensagem agora. Responda mantendo o contexto da conversa e seguindo o fluxo correto."""


def get_resposta_ia(mensagem, historico_conversa, phone: str = None, media_base64: str = None, mime_type: str = None):
    """Gera resposta usando DrAndersonAgent (fluxo estruturado com fases)"""
    try:
        if phone:
            # Usa o agente estruturado com fases (triagem → pagamento → anamnese)
            resposta = dr_anderson_agent.process_message(
                message=mensagem,
                phone=phone,
                media_base64=media_base64,
                mime_type=mime_type
            )
            print(f"[SDR] Resposta Agent: {resposta[:80]}...")
            return resposta
    except Exception as e:
        print(f"[SDR] Erro DrAndersonAgent: {str(e)}")

    # Fallback direto para DeepSeek
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in historico_conversa[-6:]:
            messages.append(msg)
        messages.append({"role": "user", "content": mensagem})

        resp = ai_manager.chat_completion(messages=messages, temperature=0.7, max_tokens=500)
        if resp and resp.get('content'):
            print(f"[SDR] Resposta DeepSeek fallback: {resp['content'][:80]}...")
            return resp['content']
    except Exception as e:
        print(f"[SDR] Erro DeepSeek fallback: {str(e)}")

    # Fallback final para Groq
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in historico_conversa[-6:]:
            messages.append(msg)
        messages.append({"role": "user", "content": mensagem})

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 300,
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            print(f"[SDR] Erro Groq: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[SDR] Erro IA fallback: {str(e)}")

    return get_resposta_fallback(mensagem, historico_conversa)


def get_resposta_fallback(mensagem, historico_conversa):
    """Respostas básicas se IA não disponível"""
    mensagem_lower = mensagem.lower()

    if any(
        palavra in mensagem_lower
        for palavra in ["oi", "ola", "bom dia", "boa tarde", "boa noite", "hello", "hi"]
    ):
        return "Olá! Sou o assistente do Dr. Anderson, médico especialista em Cannabis Medicinal. Em que posso ajudar?"

    if any(
        palavra in mensagem_lower
        for palavra in ["agendar", "consulta", "marcar", "horario"]
    ):
        return "Para agendar uma consulta com o Dr. Anderson, preciso de alguns dados: seu nome completo, email, telefone e uma breve descrição da sua condição clínica."

    if any(
        palavra in mensagem_lower
        for palavra in ["cannabis", "oleo", "cdb", "thc", "tratamento", "medicinal"]
    ):
        return "O Dr. Anderson é especializado em tratamentos com Cannabis Medicinal. Para Saber mais sobre適合 seu caso, recomendo agendar uma avaliação inicial. Gostaria de agendar?"

    if any(
        palavra in mensagem_lower for palavra in ["preco", "valor", "custo", "quanto"]
    ):
        return "O valor da consulta de avaliação inicial com o Dr. Anderson é R$ 350,00. Gostaria de agendar?"

    if any(
        palavra in mensagem_lower
        for palavra in ["obrigado", "obrigada", "tchau", "flw"]
    ):
        return "Às! Em caso de dúvidas, é só chamar. Abraços do Dr. Anderson!"

    return "Entendi. Para uma avaliação mais precisa sobre tratamento com Cannabis Medicinal, recomendo agendar uma consulta com o Dr. Anderson. Deseja agendar?"


def enviar_mensagem_whatsapp(numero, mensagem):
    """Envia mensagem via Evolution API"""
    try:
        url = f"{EVOLUTION_API_URL}/message/sendText/EuSouLIA"

        payload = {"number": numero, "text": mensagem}

        headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code in [200, 201]:
            print(f"[SDR] Mensagem enviada para {numero}")
            return True
        else:
            print(f"[SDR] Erro ao enviar: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"[SDR] Erro ao enviar mensagem: {str(e)}")
        return False


def _download_media_from_url(url: str, api_key: str) -> tuple:
    """Baixa mídia da URL da Evolution API e converte para base64."""
    try:
        headers = {"apikey": api_key}
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        media_base64 = base64.b64encode(resp.content).decode('utf-8')
        # Detectar mime_type da resposta
        mime_type = resp.headers.get('content-type', 'application/octet-stream')
        return media_base64, mime_type
    except Exception as e:
        print(f"[SDR] Erro ao baixar mídia: {e}")
        return None, None


def _extrair_media_evolucao(message: dict) -> tuple:
    """Extrai base64 e mime_type de mensagens de mídia da Evolution API.
    Suporta tanto base64 inline quanto download por URL."""
    media_base64 = None
    mime_type = None
    caption = ""
    media_url = None

    # Imagem
    if "imageMessage" in message:
        img = message.get("imageMessage", {})
        media_base64 = img.get("base64", img.get("jpegThumbnail", ""))
        mime_type = img.get("mimetype", "image/jpeg")
        caption = img.get("caption", "")
        media_url = img.get("url", "")
    # Áudio
    elif "audioMessage" in message:
        aud = message.get("audioMessage", {})
        media_base64 = aud.get("base64", "")
        mime_type = aud.get("mimetype", "audio/ogg; codecs=opus")
        media_url = aud.get("url", "")
    # Documento
    elif "documentMessage" in message:
        doc = message.get("documentMessage", {})
        media_base64 = doc.get("base64", "")
        mime_type = doc.get("mimetype", "application/pdf")
        caption = doc.get("caption", doc.get("fileName", ""))
        media_url = doc.get("url", "")
    # Vídeo
    elif "videoMessage" in message:
        vid = message.get("videoMessage", {})
        media_base64 = vid.get("base64", "")
        mime_type = vid.get("mimetype", "video/mp4")
        caption = vid.get("caption", "")
        media_url = vid.get("url", "")

    # Se não veio base64 mas tem URL, baixar
    if not media_base64 and media_url:
        print(f"[SDR] Baixando mídia de URL: {media_url[:60]}...")
        media_base64, mime_type = _download_media_from_url(media_url, EVOLUTION_API_KEY)

    return media_base64, mime_type, caption


@sdr_bp.route("/webhook", methods=["POST"])
def webhook_evolution():
    """Webhook para receber mensagens da Evolution API (EuSouLIA - Dr. Anderson)"""
    try:
        data = request.get_json()
        event_type = data.get("event")

        if event_type == "messages.upsert":
            message_data = data.get("data", {})
            message = message_data.get("message", {})
            key = message_data.get("key", {})

            if key.get("fromMe", False):
                return jsonify({"status": "ignored", "reason": "own_message"}), 200

            remote_jid = key.get("remoteJid", "")

            if "@g.us" in remote_jid or "@temp" in remote_jid:
                return jsonify({"status": "ignored", "reason": "group_message"}), 200

            # Extrair texto
            text = ""
            if "conversation" in message:
                text = message["conversation"]
            elif "extendedTextMessage" in message:
                text = message.get("extendedTextMessage", {}).get("text", "")

            # Extrair mídia (imagem, áudio, documento)
            media_base64, mime_type, caption = _extrair_media_evolucao(message)
            if caption and not text:
                text = caption

            # Se não tem texto nem mídia, ignorar
            if not text and not media_base64:
                return jsonify({"status": "ignored", "reason": "no_content"}), 200

            phone = remote_jid.replace("@s.whatsapp.net", "")

            print(f"[SDR Webhook] Mensagem de {phone}: text='{text[:50]}...' | media={bool(media_base64)} | mime={mime_type}")

            if phone not in CONVERSAS:
                CONVERSAS[phone] = []

            # Montar conteúdo para histórico (inclui descrição de mídia)
            content = text
            if media_base64:
                content = f"[MÍDIA: {mime_type}] {text}".strip()

            CONVERSAS[phone].append({"role": "user", "content": content})

            resposta = get_resposta_ia(
                mensagem=text,
                historico_conversa=CONVERSAS[phone],
                phone=phone,
                media_base64=media_base64,
                mime_type=mime_type
            )

            CONVERSAS[phone].append({"role": "assistant", "content": resposta})

            if len(CONVERSAS[phone]) > 20:
                CONVERSAS[phone] = CONVERSAS[phone][-20:]

            enviar_mensagem_whatsapp(phone, resposta)

            return jsonify({"status": "received", "response": resposta}), 200

        return jsonify({"status": "ignored"}), 200

    except Exception as e:
        print(f"[SDR Webhook] Erro: {str(e)}")
        return jsonify({"error": str(e)}), 500


@sdr_bp.route("/webhook/teste", methods=["GET"])
def webhook_teste():
    """Endpoint de teste"""
    return jsonify(
        {
            "status": "ok",
            "service": "SDR Dr. Anderson Webhook",
            "timestamp": datetime.utcnow().isoformat(),
        }
    ), 200


@sdr_bp.route("/webhook/teste-mensagem", methods=["POST"])
def teste_mensagem():
    """Endpoint para testar envio de mensagem"""
    data = request.get_json()
    numero = data.get("numero")
    mensagem = data.get("mensagem")

    if not numero or not mensagem:
        return jsonify({"error": "numero e mensagem são obrigatórios"}), 400

    success = enviar_mensagem_whatsapp(numero, mensagem)

    if success:
        return jsonify({"status": "mensagem_enviada"}), 200
    else:
        return jsonify({"error": "falha_ao_enviar"}), 500


@sdr_bp.route("/agendar", methods=["POST"])
@jwt_required()
def agendar_consulta_sdr():
    """Endpoint para o agente SDR agendar consulta"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    data = request.get_json()

    paciente_nome = data.get("nome")
    paciente_telefone = data.get("telefone")
    paciente_email = data.get("email")
    paciente_endereco = data.get("endereco")
    condicao_clinica = data.get("condicao_clinica")
    tratamento_anterior = data.get("tratamento_anterior")
    data_hora_str = data.get("data_hora")

    if not all([paciente_nome, paciente_telefone, data_hora_str]):
        return jsonify({"error": "Nome, telefone e data_hora são obrigatórios"}), 400

    try:
        data_hora = datetime.fromisoformat(data_hora_str.replace("Z", "+00:00"))

        paciente = Paciente.query.filter_by(telefone=paciente_telefone).first()

        if not paciente:
            data_nascimento = datetime.strptime(
                data.get("data_nascimento", "1990-01-01"), "%Y-%m-%d"
            ).date()

            paciente = Paciente(
                profissional_responsavel_id=profissional_id,
                nome=paciente_nome,
                data_nascimento=data_nascimento,
                telefone=paciente_telefone,
                email=paciente_email or "",
                endereco=paciente_endereco or "",
                diagnostico=condicao_clinica or "",
                em_tratamento=bool(tratamento_anterior),
            )
            db.session.add(paciente)
            db.session.flush()

        consulta = Consulta(
            paciente_id=paciente.id,
            profissional_id=profissional_id,
            data_hora=data_hora,
            duracao_minutos=60,
            tipo_consulta="presencial",
            status="agendada",
            observacoes=f"Condição clínica: {condicao_clinica}\nTratamento anterior: {tratamento_anterior or 'N/A'}",
        )
        db.session.add(consulta)

        nota_evolucao = f"""[DADOS COLETADOS VIA SDR]
Nome: {paciente_nome}
Telefone: {paciente_telefone}
Email: {paciente_email or "N/A"}
Endereço: {paciente_endereco or "N/A"}
Condição clínica: {condicao_clinica or "N/A"}
Tratamento anterior com cannabis: {tratamento_anterior or "N/A"}

Observação: Paciente agendado via agente SDR (Dr. Anderson)."""

        evolucao = Evolucao(
            paciente_id=paciente.id,
            profissional_id=profissional_id,
            nota_evolucao=nota_evolucao,
            fonte_origem="sdr",
        )
        db.session.add(evolucao)

        db.session.commit()

        return jsonify(
            {
                "message": "Consulta agendada com sucesso",
                "paciente_id": paciente.id,
                "consulta_id": consulta.id,
                "evolucao_id": evolucao.id,
            }
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@sdr_bp.route("/disponibilidade", methods=["GET"])
@jwt_required()
def listar_disponibilidades_publico():
    """Lista disponibilidades para o agente SDR"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    disponibilidades = Disponibilidade.query.filter_by(
        profissional_id=profissional_id, ativo=True
    ).all()

    return jsonify({"disponibilidades": [d.to_dict() for d in disponibilidades]}), 200


@sdr_bp.route("/disponibilidade/disponiveis", methods=["GET"])
@jwt_required()
def verificar_horarios_disponiveis_publico():
    """Verifica horários disponíveis para agendamento"""
    current_user_id = get_jwt_identity()
    profissional_id = int(current_user_id)

    data_inicio_str = request.args.get("data_inicio")
    data_fim_str = request.args.get("data_fim")

    if not data_inicio_str:
        data_inicio = date.today()
    else:
        data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()

    if data_fim_str:
        data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
    else:
        data_fim = data_inicio + timedelta(days=14)

    disponibilidades = Disponibilidade.query.filter_by(
        profissional_id=profissional_id, ativo=True
    ).all()

    if not disponibilidades:
        return jsonify(
            {"message": "Nenhuma disponibilidade cadastrada", "horarios": []}
        ), 200

    consultas_existentes = Consulta.query.filter(
        Consulta.profissional_id == profissional_id,
        Consulta.status.in_(["agendada", "confirmada"]),
        Consulta.data_hora >= datetime.combine(data_inicio, time.min),
        Consulta.data_hora <= datetime.combine(data_fim, time.max),
    ).all()

    horarios_ocupados = {}
    for consulta in consultas_existentes:
        data_key = consulta.data_hora.date()
        if data_key not in horarios_ocupados:
            horarios_ocupados[data_key] = []
        horarios_ocupados[data_key].append(consulta.data_hora)

    horarios_disponiveis = []
    current_date = data_inicio

    while current_date <= data_fim:
        dia_semana = current_date.weekday()
        dia_semana_modelo = 6 if dia_semana == 6 else dia_semana + 1

        for disp in disponibilidades:
            if disp.dia_semana == dia_semana_modelo:
                duracao = disp.duracao_consulta_minutos
                current_time = disp.hora_inicio

                while current_time < disp.hora_fim:
                    slot_datetime = datetime.combine(current_date, current_time)

                    is_occupied = False
                    if current_date in horarios_ocupados:
                        for occupied_time in horarios_ocupados[current_date]:
                            occupied_start = occupied_time
                            occupied_end = occupied_start + timedelta(minutes=duracao)
                            slot_end = slot_datetime + timedelta(minutes=duracao)

                            if (
                                slot_datetime >= occupied_start
                                and slot_datetime < occupied_end
                            ) or (
                                occupied_start >= slot_datetime
                                and occupied_start < slot_end
                            ):
                                is_occupied = True
                                break

                    if not is_occupied:
                        horarios_disponiveis.append(
                            {
                                "data": current_date.strftime("%Y-%m-%d"),
                                "hora": current_time.strftime("%H:%M"),
                                "duracao_minutos": duracao,
                            }
                        )

                    current_time = (
                        datetime.combine(date.today(), current_time)
                        + timedelta(minutes=duracao)
                    ).time()

        current_date += timedelta(days=1)

    return jsonify(
        {
            "data_inicio": data_inicio.strftime("%Y-%m-%d"),
            "data_fim": data_fim.strftime("%Y-%m-%d"),
            "horarios": horarios_disponiveis,
        }
    ), 200
