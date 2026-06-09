import logging
import os
import requests
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from services.ai_agents import ai_manager
from services.google_calendar_service import calendar_service
from services.ocr_service import ocr_service
from services.audio_transcription_service import audio_transcription_service
from services.vsf_bridge import vsf_bridge

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Gerenciador de Estado de Conversa (Redis)
# ──────────────────────────────────────────────

REDIS_HOST = os.getenv("REDIS_HOST", "siap-redis")
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

# Expiração do estado (7 dias para acompanhar todo o fluxo)
STATE_EXPIRY = 7 * 86400

# ──────────────────────────────────────────────
# FASES DO FLUXO
# ──────────────────────────────────────────────
# FASE 1 — TRIAGEM: tirar dúvidas, confirmar interesse, NÃO coletar anamnese
# FASE 2 — PAGAMENTO: aguardar confirmação de pagamento
# FASE 3 — ANAMNESE: coletar dados médicos completos
# FASE 4 — PÓS-ANAMNESE: confirmar, agendar, receber documentos

FASE = {
    "triagem": "triagem",
    "pagamento": "pagamento",
    "anamnese": "anamnese",
    "pos_anamnese": "pos_anamnese",
}

# Passos de anamnese (FASE 3) — coletados SOMENTE após pagamento
ANAMNESE_STEPS = [
    "nome_completo",      # 1. Nome completo
    "data_nascimento",    # 2. Data de nascimento
    "email",              # 3. Email
    "condicao_principal", # 4. Condição clínica principal
    "sintomas_atuais",    # 5. Sintomas que sente no momento
    "medicamentos_uso",   # 6. Medicamentos em uso (nome, dosagem, frequência)
    "historico_cannabis", # 7. Já usou cannabis medicinal?
    "tratamentos_previos",# 8. Outros tratamentos já realizados
    "exames_recentes",    # 9. Resultados de exames recentes
    "alergias",           # 10. Alergias ou reações adversas
    "peso_altura",        # 11. Peso e altura (para dosagem)
    "completo",           # Fim: anamnese completa
]

def get_state(phone: str) -> Dict:
    key = f"lia_state:{phone}"
    state_json = r.get(key)
    if state_json:
        state = json.loads(state_json)
        # Garantir que campos novos existam
        if "history" not in state:
            state["history"] = []
        if "fase" not in state:
            state["fase"] = FASE["triagem"]
        if "dados" not in state:
            state["dados"] = {}
        return state

    # Estado inicial
    new_state = {
        "fase": FASE["triagem"],
        "step": "triagem",           # step dentro da fase atual
        "dados": {},
        "greeted": False,
        "interesse_confirmado": False,
        "pagamento_confirmado": False,
        "leads_created": False,
        "history": [],
    }
    set_state(phone, new_state)
    return new_state

def set_state(phone: str, state: Dict):
    key = f"lia_state:{phone}"
    r.set(key, json.dumps(state), ex=STATE_EXPIRY)

def add_to_history(phone: str, role: str, content: str):
    state = get_state(phone)
    state["history"].append({"role": role, "content": content})
    # Manter apenas as últimas 15 mensagens para contexto maior
    if len(state["history"]) > 15:
        state["history"] = state["history"][-15:]
    set_state(phone, state)

def next_anamnese_step(current: str) -> str:
    """Retorna o próximo passo da anamnese."""
    if current == "triagem" or current == "pagamento":
        return ANAMNESE_STEPS[0]
    if current in ANAMNESE_STEPS:
        idx = ANAMNESE_STEPS.index(current)
        if idx + 1 < len(ANAMNESE_STEPS):
            return ANAMNESE_STEPS[idx + 1]
    return "completo"


# ──────────────────────────────────────────────
# Registrar Paciente no SIAP via API Interna
# ──────────────────────────────────────────────

SIAP_INTERNAL_URL = os.getenv("SIAP_INTERNAL_URL", "http://siap-backend:5002")
INTERNAL_SERVICE_KEY = os.getenv("INTERNAL_SERVICE_KEY", "dr-anderson-internal-key")

def _calcular_data_nascimento(idade_ou_data: str) -> str:
    """Converte idade (35) ou data brasileira (15/03/1985) para formato ISO."""
    texto = str(idade_ou_data).strip()
    
    # Tentar formato brasileiro DD/MM/YYYY
    import re
    match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', texto)
    if match:
        dia, mes, ano = match.groups()
        return f"{ano}-{int(mes):02d}-{int(dia):02d}"
    
    # Tentar formato ISO YYYY-MM-DD
    match_iso = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', texto)
    if match_iso:
        ano, mes, dia = match_iso.groups()
        return f"{ano}-{int(mes):02d}-{int(dia):02d}"
    
    # Fallback: interpretar como idade em anos
    try:
        digitos = ''.join(filter(str.isdigit, texto))
        if digitos:
            anos = int(digitos)
            if 0 < anos < 150:  # Idade plausível
                ano_nasc = datetime.now().year - anos
                return f"{ano_nasc}-01-01"
    except Exception:
        pass
    
    return "1990-01-01"

def criar_paciente_no_siap(dados: Dict) -> Optional[int]:
    """Cria ou atualiza paciente no SIAP com dados completos de anamnese.
    Retorna o paciente_id criado ou None em caso de erro."""
    try:
        url = f"{SIAP_INTERNAL_URL}/api/dr-anderson/criar-lead"
        headers = {
            "Content-Type": "application/json",
            "X-Internal-Key": INTERNAL_SERVICE_KEY,
        }
        
        # Montar observações estruturadas com todos os dados da anamnese
        obs_lines = [
            "=== ANAMNESE COMPLETA ===",
            f"Condição Principal: {dados.get('condicao_principal', 'Não informado')}",
            f"Sintomas Atuais: {dados.get('sintomas_atuais', 'Não informado')}",
            f"Medicamentos em Uso: {dados.get('medicamentos_uso', 'Não informado')}",
            f"Histórico Cannabis: {dados.get('historico_cannabis', 'Não informado')}",
            f"Tratamentos Prévios: {dados.get('tratamentos_previos', 'Não informado')}",
            f"Exames Recentes: {dados.get('exames_recentes', 'Não informado')}",
            f"Alergias: {dados.get('alergias', 'Não informado')}",
            f"Peso/Altura: {dados.get('peso_altura', 'Não informado')}",
            "========================",
        ]
        
        payload = {
            "nome": dados.get("nome_completo", "Paciente Dr. Anderson"),
            "telefone": dados.get("telefone", ""),
            "email": dados.get("email", ""),
            "diagnostico": dados.get("condicao_principal", ""),
            "observacoes": "\n".join(obs_lines),
            "data_nascimento": _calcular_data_nascimento(dados.get("data_nascimento", dados.get("idade", "30"))),
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        if resp.status_code in (200, 201):
            data = resp.json()
            paciente_id = data.get("paciente_id")
            if paciente_id:
                logger.info(f"Paciente criado no SIAP: ID={paciente_id}")
                return paciente_id
        logger.error(f"Erro ao criar paciente no SIAP: {resp.status_code} - {resp.text}")
        return None
    except Exception as e:
        logger.error(f"Exceção ao criar paciente no SIAP: {e}")
        return None


def _criar_paciente_vsf(dados: Dict, face_image_b64: Optional[str] = None) -> Optional[str]:
    """Cria paciente no Visual Smart Flow e retorna o patient_id."""
    try:
        result = vsf_bridge.criar_paciente(
            name=dados.get("nome_completo", "Paciente"),
            phone=dados.get("telefone", ""),
            email=dados.get("email", ""),
            face_image_b64=face_image_b64,
        )
        patient_id = result.get("id")
        logger.info(f"[VSF] Paciente criado: {patient_id}")
        return patient_id
    except Exception as e:
        logger.error(f"[VSF] Erro ao criar paciente: {e}")
        return None


def _sincronizar_agendamento_vsf(dados: Dict, data_hora: datetime) -> Optional[str]:
    """Cria agendamento no Visual Smart Flow e retorna o appointment_id."""
    try:
        vsf_patient_id = dados.get("vsf_patient_id")
        if not vsf_patient_id:
            logger.warning("[VSF] vsf_patient_id não disponível, pulando agendamento")
            return None

        result = vsf_bridge.criar_agendamento(
            patient_name=dados.get("nome_completo", "Paciente"),
            patient_external_id=str(dados.get("paciente_id_siap", "")),
            vsf_patient_id=vsf_patient_id,
            scheduled_for=data_hora,
            exam_type="consulta",
            professional_id="1",  # Dr. Anderson
            exam_duration_minutes=30,
        )
        apt_id = str(result.get("appointment_id"))
        logger.info(f"[VSF] Agendamento criado: {apt_id}")
        return apt_id
    except Exception as e:
        logger.error(f"[VSF] Erro ao criar agendamento: {e}")
        return None


# ──────────────────────────────────────────────
# Prompts
# ──────────────────────────────────────────────

SYSTEM_PROMPT_BASE = """Você é a LIA, assistente SDR dedicada do Dr. Anderson Holzwarth, especialista em Cannabis Medicinal pela Arapath.

PERFIL DO MÉDICO:
- Dr. Anderson Holzwarth
- CRM ativo, especialista em tratamentos com canabinóides
- Atendimento via Telemedicina e presencial
- Consulta inicial: R$ 350,00 | Duração: 30-45 min

FLUXO OBRIGATÓRIO (seguir rigorosamente):

FASE 1 — TRIAGEM (antes do pagamento):
- OBJETIVO: tirar dúvidas e confirmar interesse REAL em consulta
- Responda perguntas sobre Cannabis Medicinal, processo, valores
- NÃO peça nome, email, condição, histórico ou exames nesta fase
- NÃO faça anamnese nesta fase
- SÓ avance para pagamento quando o paciente confirmar interesse

FASE 2 — PAGAMENTO:
- Oriente sobre o pagamento (R$ 350,00)
- Envie link de pagamento
- Aguarde confirmação de pagamento
- SÓ prossiga para anamnese quando confirmar pagamento

FASE 3 — ANAMNESE (após pagamento confirmado):
- Agora SIM colete dados médicos completos
- Condição principal, sintomas, medicamentos, histórico cannabis
- Exames, alergias, peso/altura
- Seja gentil e explique por que precisa de cada informação

FASE 4 — PÓS-ANAMNESE:
- Confirme recebimento de todos os dados
- Ofereça receber documentos, laudos ou fotos por WhatsApp
- Agende consulta com Dr. Anderson
- Explique que o médico analisará o caso antes da consulta

REGRAS DE OURO:
1. NUNCA se apresente mais de uma vez
2. NUNCA dê diagnósticos ou prescrições
3. NUNCA peça dados de anamnese antes do pagamento
4. Respostas curtas e naturais (máx 3 frases por vez)
5. Seja empática e direta
"""

PROMPT_TRIAGEM = SYSTEM_PROMPT_BASE + """

VOCÊ ESTÁ NA FASE DE TRIAGEM.
- Responda dúvidas do paciente sobre Cannabis Medicinal
- NÃO peça dados pessoais ou médicos ainda
- Quando o paciente mostrar interesse em consulta, confirme e ofereça prosseguir com pagamento
- Se não houver interesse, continue tirando dúvidas educadamente
"""

PROMPT_PAGAMENTO = SYSTEM_PROMPT_BASE + """

VOCÊ ESTÁ NA FASE DE PAGAMENTO.
- O paciente já confirmou interesse em consulta
- Informe o valor (R$ 350,00) e oriente sobre o pagamento
- Envie o link de pagamento
- Aguarde confirmação
- NÃO inicie anamnese até confirmar pagamento
"""

PROMPT_ANAMNESE = SYSTEM_PROMPT_BASE + """

VOCÊ ESTÁ NA FASE DE ANAMNESE (pagamento confirmado).
- Colete os dados médicos de forma gentil e estruturada
- Explique brevemente por cada informação é importante
- Aceite respostas parciais e continue naturalmente
- Se o paciente não souber algo, anote "não informado" e prossiga
- Ofereça enviar fotos de documentos, laudos ou exames
"""

PROMPT_POS_ANAMNESE = SYSTEM_PROMPT_BASE + """

VOCÊ ESTÁ NA FASE PÓS-ANAMNESE.
- Agradeça e confirme que todos os dados foram recebidos
- Ofereça enviar documentos, laudos ou fotos adicionais
- Informe que o Dr. Anderson analisará o caso antes da consulta
- Agende a consulta ou passe as opções de horário
- Seja acolhedora e transmita segurança
"""

# Mapa de perguntas para cada passo da anamnese
PERGUNTA_ANAMNESE = {
    "nome_completo": "Para iniciar sua ficha, qual é o seu nome completo?",
    "data_nascimento": "Qual é a sua data de nascimento? (Ex: 15/03/1985)",
    "email": "Qual é o seu melhor e-mail?",
    "condicao_principal": "Qual é a condição de saúde principal que você deseja tratar com Cannabis Medicinal?",
    "sintomas_atuais": "Quais sintomas você está sentindo no momento? (Ex: dor, insônia, ansiedade, náusea...)",
    "medicamentos_uso": "Quais medicamentos você está tomando atualmente? Informe o nome, dosagem e frequência de cada um.",
    "historico_cannabis": "Você já fez ou faz uso de Cannabis Medicinal? Se sim, qual produto e dosagem?",
    "tratamentos_previos": "Já realizou outros tratamentos para essa condição? Quais e como foi a experiência?",
    "exames_recentes": "Possui exames recentes (sangue, imagem, etc.)? Se quiser, pode enviar fotos dos laudos por aqui.",
    "alergias": "Tem alguma alergia medicamentosa ou reação adversa conhecida?",
    "peso_altura": "Qual é o seu peso e altura? (Importante para o cálculo de dosagem)",
}


# ──────────────────────────────────────────────
# Agente de IA
# ──────────────────────────────────────────────

class DrAndersonAgent:
    def process_message(self, message: str, phone: str, media_base64: str = None, mime_type: str = None) -> str:
        state = get_state(phone)
        fase = state.get("fase", FASE["triagem"])
        
        # ── Processar mídia (imagem ou áudio) ──
        media_description = ""
        if media_base64 and mime_type:
            if mime_type.startswith("image/") or mime_type.startswith("application/"):
                # OCR em imagem/documento
                print(f"DEBUG: [Agent] Processando imagem/documento OCR para {phone}", flush=True)
                ocr_result = ocr_service.process_base64_image(media_base64)
                if ocr_result["status"] == "success" and ocr_result["texto_extraido"]:
                    media_description = f"\n[DOCUMENTO ANEXADO - OCR]: {ocr_result['texto_extraido'][:500]}"
                    print(f"DEBUG: [Agent] OCR extraído: {ocr_result['texto_extraido'][:100]}...", flush=True)
                else:
                    media_description = "\n[DOCUMENTO/IMAGEM ANEXADO - OCR não conseguiu ler o texto]"
            elif mime_type.startswith("audio/"):
                # Transcrição de áudio
                print(f"DEBUG: [Agent] Transcrevendo áudio para {phone}", flush=True)
                trans_result = audio_transcription_service.transcribe_base64(media_base64, mime_type)
                if trans_result["texto"]:
                    media_description = f"\n[ÁUDIO TRANSCRITO]: {trans_result['texto']}"
                    print(f"DEBUG: [Agent] Áudio transcrito: {trans_result['texto'][:100]}...", flush=True)
                else:
                    media_description = "\n[ÁUDIO ENVIADO - não foi possível transcrever]"
            
            # Anexar descrição da mídia à mensagem
            if media_description:
                message = message + media_description if message else media_description.strip()
        
        print(f"DEBUG: [Agent Dr. Anderson] Fase: {fase} | Step: {state['step']} | Msg: {message[:60]}", flush=True)
        
        # Guardar mensagem do usuário no histórico
        add_to_history(phone, "user", message)

        # ── FASE 4: PÓS-ANAMNESE ──
        if fase == FASE["pos_anamnese"]:
            reply = self._handle_pos_anamnese(message, phone, media_base64, mime_type)
            add_to_history(phone, "assistant", reply)
            return reply

        # ── FASE 3: ANAMNESE ──
        if fase == FASE["anamnese"]:
            reply = self._handle_anamnese(message, phone, media_base64, mime_type)
            add_to_history(phone, "assistant", reply)
            return reply

        # ── FASE 2: PAGAMENTO ──
        if fase == FASE["pagamento"]:
            reply = self._handle_pagamento(message, phone, media_base64, mime_type)
            add_to_history(phone, "assistant", reply)
            return reply

        # ── FASE 1: TRIAGEM ──
        reply = self._handle_triagem(message, phone, media_base64, mime_type)
        add_to_history(phone, "assistant", reply)
        return reply

    # ──────────────────────────────────────────────
    # HANDLERS POR FASE
    # ──────────────────────────────────────────────

    def _handle_triagem(self, message: str, phone: str, media_base64, mime_type) -> str:
        """Fase 1: Tirar dúvidas, confirmar interesse. NÃO coletar dados médicos."""
        state = get_state(phone)
        is_first = not state.get("greeted", False)
        
        prompt = PROMPT_TRIAGEM
        if is_first:
            state["greeted"] = True
            set_state(phone, state)
            prompt += "\n\nIMPORTANTE: Primeira mensagem. Apresente-se brevemente e pergunte como pode ajudar."
        else:
            prompt += "\n\nREGRAS: SEM SAUDAÇÃO. Responda diretamente."

        # Detectar interesse em agendamento/consulta
        if self._detectar_interesse_consulta(message):
            # Transitar para fase de pagamento
            state["fase"] = FASE["pagamento"]
            state["interesse_confirmado"] = True
            set_state(phone, state)
            
            reply = ("Que ótimo! Fico feliz que você quer dar esse passo. 💚\n\n"
                    "A consulta inicial com o Dr. Anderson custa *R$ 350,00* e dura cerca de 30 a 45 minutos. "
                    "Posso te enviar o link para pagamento agora. Assim que confirmar, iniciamos sua anamnese completa.\n\n"
                    "Deseja prosseguir com o pagamento?")
            return reply

        # Keywords de agenda
        keywords = ["vaga", "horário", "agenda", "disponib", "segunda", "terça", "quarta", "quinta", "sexta", "amanhã", "próximos", "atendimento", "consulta", "marcar", "agendar"]
        if any(k in message.lower() for k in keywords):
            info = self._obter_info_agenda(message)
            prompt += f"\n\n--- DADOS REAIS DO SISTEMA AGORA ---\n{info}\n-----------------------------------"

        messages = [{"role": "system", "content": prompt}]
        if state["history"]:
            messages.extend(state["history"][:-1])
        messages.append({"role": "user", "content": message})
        
        resp = ai_manager.chat_completion(messages=messages, temperature=0.7)
        return resp.get("content", "Como posso ajudar você hoje?")

    def _handle_pagamento(self, message: str, phone: str, media_base64, mime_type) -> str:
        """Fase 2: Orientar pagamento. Simular confirmação para testes."""
        state = get_state(phone)
        
        # Detectar confirmação de pagamento (simulação para testes)
        # Em produção, isso viria de webhook de pagamento
        confirm_keywords = ["paguei", "pagamento confirmado", "pago", "confirma", "efetuei", "realizei", "ok", "sim", "confirmo"]
        if any(k in message.lower() for k in confirm_keywords):
            state["fase"] = FASE["anamnese"]
            state["pagamento_confirmado"] = True
            state["step"] = ANAMNESE_STEPS[0]
            set_state(phone, state)
            
            reply = ("Pagamento confirmado! 🎉\n\n"
                    "Agora vou coletar algumas informações para montar sua ficha completa antes da consulta com o Dr. Anderson. "
                    "Isso ajuda o médico a se preparar melhor para te atender.\n\n"
                    f"{PERGUNTA_ANAMNESE['nome_completo']}")
            state["last_asked"] = "nome_completo"
            set_state(phone, state)
            return reply

        # Ainda não pagou — orientar
        prompt = PROMPT_PAGAMENTO
        if state.get("history"):
            messages = [{"role": "system", "content": prompt}]
            messages.extend(state["history"][:-1])
            messages.append({"role": "user", "content": message})
            resp = ai_manager.chat_completion(messages=messages, temperature=0.7)
            return resp.get("content", "Assim que efetuar o pagamento de R$ 350,00, me avise para iniciarmos sua ficha! 💚")
        
        return ("Perfeito! Para prosseguir com a consulta, o valor é de *R$ 350,00*.\n\n"
                "Assim que você efetuar o pagamento, me avise aqui mesmo que iniciarei sua ficha completa "
                "e agendaremos seu horário com o Dr. Anderson. 💚")

    def _handle_anamnese(self, message: str, phone: str, media_base64, mime_type) -> str:
        """Fase 3: Coletar dados médicos completos estruturados."""
        state = get_state(phone)
        dados = state["dados"]
        dados["telefone"] = phone
        
        # Registrar resposta do passo anterior
        last_asked = state.get("last_asked")
        if last_asked and last_asked in ANAMNESE_STEPS:
            dados[last_asked] = message.strip()
            state["dados"] = dados
            state["step"] = next_anamnese_step(last_asked)
            set_state(phone, state)

        # Verificar se completou a anamnese
        if state["step"] == "completo":
            # Criar paciente no SIAP com dados completos
            paciente_id = criar_paciente_no_siap(dados)
            if paciente_id:
                dados["paciente_id_siap"] = paciente_id
                state["dados"] = dados
            
            state["fase"] = FASE["pos_anamnese"]
            state["leads_created"] = True
            set_state(phone, state)
            
            nome = dados.get("nome_completo", "Paciente")
            reply = (f"Perfeito, {nome.split()[0]}! ✅ Recebi todos os seus dados e já montei sua ficha completa.\n\n"
                    "O Dr. Anderson vai analisar seu caso antes da consulta. "
                    "Se tiver laudos, receitas ou exames em foto, pode enviar por aqui!\n\n"
                    "Também posso cadastrar seu reconhecimento facial para check-in automático na clínica. "
                    "Se quiser, é só enviar uma selfie bem iluminada. 📸\n\n"
                    "Vou verificar a agenda e te passo as opções de horário em seguida. 🌿📅")
            return reply

        # Próxima pergunta da anamnese
        proxima = state["step"]
        pergunta = PERGUNTA_ANAMNESE.get(proxima, "")
        state["last_asked"] = proxima
        set_state(phone, state)

        # Gerar resposta com contexto
        prompt = PROMPT_ANAMNESE + f"\n\nPRÓXIMA INFORMAÇÃO A COLETAR: {pergunta}\n"
        prompt += "Responda de forma natural, como uma conversa. Não seja robótica."

        messages = [{"role": "system", "content": prompt}]
        if state["history"]:
            messages.extend(state["history"][:-1])
        messages.append({"role": "user", "content": message})
        
        resp = ai_manager.chat_completion(messages=messages, temperature=0.7)
        content = resp.get("content", pergunta)
        
        # Garantir que a pergunta atual esteja incluída
        if pergunta and pergunta not in content:
            content += f"\n\n{pergunta}"
        
        return content

    def _handle_pos_anamnese(self, message: str, phone: str, media_base64, mime_type) -> str:
        """Fase 4: Pós-anamnese. Agendar, receber documentos, responder dúvidas.
        Integração com Visual Smart Flow para check-in por visão computacional."""
        state = get_state(phone)
        dados = state.get("dados", {})

        # Se enviou foto (mídia), cadastrar/atualizar paciente no VSF com reconhecimento facial
        if media_base64 and mime_type and mime_type.startswith("image/"):
            vsf_patient_id = state.get("vsf_patient_id")
            if not vsf_patient_id:
                # Criar paciente no VSF com a foto (cadastro facial)
                vsf_patient_id = _criar_paciente_vsf(dados, face_image_b64=media_base64)
                if vsf_patient_id:
                    state["vsf_patient_id"] = vsf_patient_id
                    set_state(phone, state)
                    
                    # Se já tem agendamento no VSF, sincronizar patient_id (recria agendamento)
                    if state.get("vsf_appointment_id"):
                        try:
                            # Aqui idealmente atualizaríamos o agendamento; por ora recriamos
                            from datetime import timezone
                            dt_str = state.get("vsf_scheduled_for")
                            if dt_str:
                                dt_obj = datetime.fromisoformat(dt_str)
                                vsf_apt_id = _sincronizar_agendamento_vsf(dados, dt_obj)
                                if vsf_apt_id:
                                    state["vsf_appointment_id"] = vsf_apt_id
                                    set_state(phone, state)
                        except Exception as e:
                            print(f"DEBUG: [Agent] Erro ao re-sincronizar agendamento VSF: {e}", flush=True)
                    
                    return "✅ Selfie recebida e cadastro facial realizado com sucesso! Ao chegar na clínica, basta passar pela recepção que nosso sistema de visão computacional vai reconhecê-lo(a) automaticamente."
                else:
                    return "Recebi sua foto, mas não consegui cadastrar o reconhecimento facial no momento. Pode tentar enviar outra selfie com mais luz e olhando para a câmera? 📸"
            else:
                # Paciente já existe no VSF, tentar atualizar face (recriar paciente com mesmos dados + nova foto)
                # O endpoint /patients/register pode reconhecer e retornar o existente; se não, cria novo
                try:
                    novo_id = _criar_paciente_vsf(dados, face_image_b64=media_base64)
                    if novo_id:
                        state["vsf_patient_id"] = novo_id
                        set_state(phone, state)
                        return "✅ Selfie atualizada! Seu cadastro facial foi atualizado com sucesso."
                except Exception as e:
                    logger.error(f"[VSF] Erro ao atualizar face: {e}")
                return "Recebi sua foto! Seu cadastro facial já está ativo. Se quiser atualizar, posso tentar novamente. 📸"

        # Tentar agendar se houver intenção clara
        agendamento = self._extrair_agendamento_ia(message)
        if agendamento and agendamento.get("data") and agendamento.get("hora"):
            try:
                dt_str = f"{agendamento['data']} {agendamento['hora']}"
                dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                
                paciente_nome = dados.get("nome_completo", "Paciente")
                summary = f"Consulta: {paciente_nome}"
                desc = f"Agendado automaticamente pela LIA via WhatsApp.\nTelefone: {phone}\nEmail: {dados.get('email', 'N/A')}\nCondição: {dados.get('condicao_principal', 'N/A')}"
                
                ev = calendar_service.create_event(dt_obj, dt_obj + timedelta(hours=1), summary, desc, dados.get('email'))
                if ev:
                    # Sincronizar com Visual Smart Flow para check-in por visão computacional
                    vsf_msg = ""
                    if dados.get("paciente_id_siap"):
                        try:
                            # Garantir que temos vsf_patient_id; se não, criar sem foto
                            if not state.get("vsf_patient_id"):
                                vsf_patient_id = _criar_paciente_vsf(dados)
                                if vsf_patient_id:
                                    state["vsf_patient_id"] = vsf_patient_id
                                    dados["vsf_patient_id"] = vsf_patient_id
                                    set_state(phone, state)
                            
                            vsf_apt_id = _sincronizar_agendamento_vsf(dados, dt_obj)
                            if vsf_apt_id:
                                state["vsf_appointment_id"] = vsf_apt_id
                                state["vsf_scheduled_for"] = dt_obj.isoformat()
                                set_state(phone, state)
                                vsf_msg = "\n\n🔮 Também cadastrei seu agendamento no sistema de check-in inteligente. Se enviar uma selfie, farei seu cadastro facial para reconhecimento automático na recepção."
                        except Exception as vsf_err:
                            print(f"DEBUG: [Agent] Erro VSF sync: {vsf_err}", flush=True)
                    
                    return f"Maravilha, {paciente_nome.split()[0]}! ✅ Sua consulta foi reservada para o dia {dt_obj.strftime('%d/%m/%Y')} às {dt_obj.strftime('%H:%M')}.{vsf_msg}\n\nO Dr. Anderson já está com sua ficha e vai te atender com todo cuidado. Até lá! 🌿📅"
            except Exception as e:
                print(f"DEBUG: [Agent Dr. Anderson] Erro no agendamento: {e}", flush=True)

        # Keywords de agenda
        prompt = PROMPT_POS_ANAMNESE
        keywords = ["vaga", "horário", "agenda", "disponib", "segunda", "terça", "quarta", "quinta", "sexta", "amanhã", "próximos", "atendimento", "consulta", "marcar", "agendar"]
        if any(k in message.lower() for k in keywords):
            info = self._obter_info_agenda(message)
            prompt += f"\n\n--- DADOS REAIS DO SISTEMA AGORA ---\n{info}\n-----------------------------------"

        messages = [{"role": "system", "content": prompt}]
        if state["history"]:
            messages.extend(state["history"][:-1])
        messages.append({"role": "user", "content": message})
        
        resp = ai_manager.chat_completion(messages=messages, temperature=0.7)
        return resp.get("content", "Obrigada! Entraremos em contato em breve para confirmar o horário.")

    # ──────────────────────────────────────────────
    # UTILITÁRIOS
    # ──────────────────────────────────────────────

    def _detectar_interesse_consulta(self, message: str) -> bool:
        """Detecta se o usuário quer marcar consulta ou mostrou interesse claro."""
        interesse_keywords = [
            "quero marcar", "quero agendar", "quero consulta", "vou marcar", "vou agendar",
            "queria marcar", "queria agendar", "gostaria de marcar", "gostaria de agendar",
            "como faço para marcar", "como faço para agendar", "vamos marcar", "vamos agendar",
            "pode agendar", "pode marcar", "quero começar", "quero tratar", "quero iniciar",
            "tenho interesse", "confirmo interesse", "quero prosseguir", "vou pagar"
        ]
        msg_lower = message.lower()
        return any(k in msg_lower for k in interesse_keywords)

    def _extrair_agendamento_ia(self, message: str) -> dict:
        """Usa o LLM para extrair data e hora de uma mensagem de agendamento."""
        now = datetime.now()
        prompt = f"""Extraia a data e hora de agendamento desejada pelo paciente.
Mensagem: "{message}"
Data de hoje: {now.strftime('%d/%m/%Y')} (Brasil/Maceió)

Responda APENAS em JSON no formato: {{"data": "YYYY-MM-DD", "hora": "HH:MM"}}.
Se não houver data/hora clara para agendamento, responda null.
"""
        resp = ai_manager.chat_completion(messages=[{"role": "system", "content": prompt}], temperature=0.1)
        content = resp.get("content", "").strip()
        try:
            clean_content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_content)
        except:
            return None

    def _obter_info_agenda(self, query: str) -> str:
        """Consulta o Google Calendar para verificar disponibilidade."""
        print(f"DEBUG: [Agent Dr. Anderson] Triggered agenda check for: {query[:30]}", flush=True)
        try:
            amanha = datetime.now() + timedelta(days=1)
            slots = calendar_service.list_free_slots(amanha)
            
            if not calendar_service.service:
                return "SISTEMA: Agenda do Dr. Anderson é de terça a sexta, das 09h às 18h. INSTRUÇÃO: Informe que o médico confirmará o horário exato após o cadastro."
            
            if slots:
                return f"SISTEMA: Horários disponíveis: {', '.join(slots[:5])}. INSTRUÇÃO: Sugira esses horários ao paciente."
            else:
                return "SISTEMA: Agenda cheia nas próximas datas. INSTRUÇÃO: Informe que buscaremos um encaixe."
        except Exception as e:
            print(f"DEBUG: [Agent Dr. Anderson] Erro na consulta da agenda: {e}", flush=True)
            return "SISTEMA: Problema ao ler agenda."


# Instância global
dr_anderson_agent = DrAndersonAgent()
