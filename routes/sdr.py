from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Paciente, Consulta, Evolucao, Disponibilidade
from datetime import datetime, date, time, timedelta
import os
import requests
import json
import google.generativeai as genai

sdr_bp = Blueprint("sdr", __name__)

SIAP_API_URL = os.getenv("SIAP_API_URL", "https://api.visualsmartflow.com.br")
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://147.93.33.253:8080")
EVOLUTION_API_KEY = os.getenv(
    "EVOLUTION_API_KEY",
    "EVOL_SECRET_oj1JhPB0Zx2r0L8qYtQ4Jw8kZfT9vG2hR3mN7aCsW8pQ0uD5eK1sB9fL2rX6cQ4",
)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PROFISSIONAL_ID_DR_ANDERSON = 2

CONVERSAS = {}

SYSTEM_PROMPT = """Você é LIA, assistente virtual da clínica do Dr. Anderson (especialista em Cannabis Medicinal).

SUA IDENTIDADE:
- Você é uma IA, NÃO o Dr. Anderson
- Você trabalha PARA o Dr. Anderson
- Seu nome é LIA
- Sempre se apresente como assistente, não como médico

IMPORTANTE: Você está em uma conversa ativa. LEMBRE-SE:
- Este lead já conversou com você antes nesta sessão
- NÃO se apresente novamente a cada mensagem
- Continue a conversa de onde parou
- Mantenha contexto das informações já coletadas

SUA FUNÇÃO PRINCIPAL:
- Atender leads que chegam pelo WhatsApp
- Tirar dúvidas sobre tratamento com Cannabis Medicinal
- Qualificar o lead (condição clínica, tratamentos anteriores)
- Identificar intenção de agendamento
- Agendar consultas

DADOS PARA COLETAR (quando quiser agendar):
- Nome completo
- Telefone
- Email
- Data de nascimento
- Condição clínica principal
- Já fez tratamento com Cannabis? Se sim, qual?

INFORMAÇÕES IMPORTANTES:
- Valor da consulta com Dr. Anderson: R$ 350,00
- Consulta inicial é uma avaliação, não prescrição
- O Dr. Anderson é o médico responsável, você é a assistente
- Não prescreva sem avaliação
- Seja empático e paciente
- Responda de forma curta e conversational (máx 2 frases)

O lead enviou uma mensagem agora. Responda mantendo o contexto da conversa."""


def get_resposta_ia(mensagem, historico_conversa):
    """Gera resposta usando Google Gemini 2.5 Flash Lite"""
    google_api_key = os.getenv("GOOGLE_API_KEY", "")

    if not google_api_key:
        return get_resposta_fallback(mensagem, historico_conversa)

    try:
        genai.configure(api_key=google_api_key)

        model = genai.GenerativeModel(
            "gemini-2.5-flash-lite", system_instruction=SYSTEM_PROMPT
        )

        chat_history = []
        for msg in historico_conversa[-6:]:
            chat_history.append(
                {
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [{"text": msg["content"]}],
                }
            )

        chat = model.start_chat(history=chat_history)

        response = chat.send_message(mensagem)

        return response.text

    except Exception as e:
        print(f"[SDR] Erro Gemini: {str(e)}")
        return get_resposta_fallback(mensagem, historico_conversa)

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
            return get_resposta_fallback(mensagem, historico_conversa)

    except Exception as e:
        print(f"[SDR] Erro IA: {str(e)}")
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

            text = ""
            if "conversation" in message:
                text = message["conversation"]
            elif "extendedTextMessage" in message:
                text = message.get("extendedTextMessage", {}).get("text", "")

            if not text:
                return jsonify({"status": "ignored", "reason": "no_text"}), 200

            phone = remote_jid.replace("@s.whatsapp.net", "")

            print(f"[SDR Webhook] Mensagem de {phone}: {text[:50]}...")

            if phone not in CONVERSAS:
                CONVERSAS[phone] = []

            CONVERSAS[phone].append({"role": "user", "content": text})

            resposta = get_resposta_ia(text, CONVERSAS[phone])

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
