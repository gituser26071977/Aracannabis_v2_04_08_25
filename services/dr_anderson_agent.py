import logging
import os
import requests
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from services.ai_agents import ai_manager
from services.google_calendar_service import calendar_service

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Gerenciador de Estado de Conversa (Redis)
# ──────────────────────────────────────────────

REDIS_HOST = os.getenv("REDIS_HOST", "siap-redis")
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

# Expiração do estado (24 horas)
STATE_EXPIRY = 86400

# Passos estruturados de coleta de dados (SDR)
SDR_STEPS = [
    "condicao_saude",     # 1. Qual condição de saúde deseja tratar?
    "historico_cannabis", # 2. Já usou ou usa cannabis medicinal?
    "idade",              # 3. Qual a sua idade?
    "nome",               # 4. Qual é o seu nome completo?
    "email",              # 5. E o seu email?
    "completo",           # Fim: dados suficientes para criar a ficha
]

def get_state(phone: str) -> Dict:
    key = f"lia_state:{phone}"
    state_json = r.get(key)
    if state_json:
        state = json.loads(state_json)
        # Garantir que campos novos existam
        if "history" not in state: state["history"] = []
        return state
    
    # Estado inicial se não existir
    new_state = {
        "step": "triagem",
        "dados": {},
        "greeted": False,
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
    # Manter apenas as últimas 10 mensagens
    if len(state["history"]) > 10:
        state["history"] = state["history"][-10:]
    set_state(phone, state)

def next_step(current: str) -> str:
    if current == "triagem":
        return SDR_STEPS[0]
    if current in SDR_STEPS:
        idx = SDR_STEPS.index(current)
        if idx + 1 < len(SDR_STEPS):
            return SDR_STEPS[idx + 1]
    return "completo"


# ──────────────────────────────────────────────
# Registrar Lead no SIAP via API Interna
# ──────────────────────────────────────────────

SIAP_INTERNAL_URL = os.getenv("SIAP_INTERNAL_URL", "http://siap-backend:5002")
INTERNAL_SERVICE_KEY = os.getenv("INTERNAL_SERVICE_KEY", "dr-anderson-internal-key")

def _calcular_data_nascimento(idade: str) -> str:
    try:
        anos = int(''.join(filter(str.isdigit, str(idade))))
        ano_nasc = datetime.now().year - anos
        return f"{ano_nasc}-01-01"
    except Exception:
        return "1990-01-01"

def criar_lead_no_siap(dados: Dict) -> bool:
    try:
        url = f"{SIAP_INTERNAL_URL}/api/dr-anderson/criar-lead"
        headers = {
            "Content-Type": "application/json",
            "X-Internal-Key": INTERNAL_SERVICE_KEY,
        }
        payload = {
            "nome": dados.get("nome", "Paciente Dr. Anderson"),
            "telefone": dados.get("telefone", ""),
            "email": dados.get("email", ""),
            "diagnostico": dados.get("condicao_saude", ""),
            "observacoes": f"Idade: {dados.get('idade')}. Histórico de cannabis: {dados.get('historico_cannabis', 'Não informado')}. Lead captado via WhatsApp.",
            "data_nascimento": _calcular_data_nascimento(dados.get("idade", "30")),
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        return resp.status_code in (200, 201)
    except Exception as e:
        logger.error(f"Exceção ao criar lead no SIAP: {e}")
        return False


# ──────────────────────────────────────────────
# Agente de IA
# ──────────────────────────────────────────────

SYSTEM_PROMPT_BASE = """Você é a LIA, assistente SDR dedicada do Dr. Anderson Holzwarth, especialista em Cannabis Medicinal pela Aracannabis.

PERFIL DO MÉDICO:
- Dr. Anderson Holzwarth
- Especialista em tratamentos com canabinóides.
- Atendimento via Telemedicina e presencial.

SUAS DIRETRIZES DE OURO:
1. **NUNCA CUMPRIMENTE MAIS DE UMA VEZ.**
2. **AGENDA:** Você tem acesso à disponibilidade do Google Calendar do Dr. Anderson. Se perguntarem se tem vaga para um dia específico (ex: "tem vaga para segunda?"), você deve informar o status (ex: "temos horários livres!") e dizer que está coletando os dados para o médico confirmar o horário exato.
3. **RESPOSTAS CURTAS:** Seja direta. Não escreva parágrafos longos.
4. **FOCO NO SDR:** Colete os dados necessários: Condição de saúde, Histórico, Idade, Nome completo e Email.
"""

class DrAndersonAgent:
    def process_message(self, message: str, phone: str, media_base64: str = None, mime_type: str = None) -> str:
        state = get_state(phone)
        print(f"DEBUG: [Agent Dr. Anderson] Estado: {state['step']} | Greeted: {state['greeted']} | Recebido: {message[:30]}", flush=True)
        
        # Guardar mensagem do usuário no histórico
        add_to_history(phone, "user", message)

        # Se já completou, apenas responde dúvidas normais ou agradece novos documentos
        if state.get("leads_created"):
            reply = self._handle_post_registration(message, phone, media_base64, mime_type)
            add_to_history(phone, "assistant", reply)
            return reply

        # Detectar agendamento e transitar estado se necessário
        if state["step"] == "triagem" and self._detectar_interesse_agendamento(message):
            state["step"] = SDR_STEPS[0]
            set_state(phone, state)

        if state["step"] == "triagem":
            reply = self._handle_triagem(message, phone, media_base64, mime_type)
            add_to_history(phone, "assistant", reply)
            return reply

        # --- FLUXO DE COLETA (SDR) ---
        dados = state["dados"]
        dados["telefone"] = phone
        
        last_asked = state.get("last_asked")
        if last_asked in SDR_STEPS:
            dados[last_asked] = message.strip()
            state["step"] = next_step(last_asked)
            state["dados"] = dados
            set_state(phone, state)

        # Verificar se completou agora
        if state["step"] == "completo":
            criar_lead_no_siap(dados)
            state["leads_created"] = True
            set_state(phone, state)
            reply = (f"Perfeito, {dados.get('nome', 'Paciente')}! Recebi seus dados e criei sua ficha. "
                    "Vou repassar ao Dr. Anderson para que ele verifique a agenda e te ligue para confirmar o horário exato. "
                    "Se tiver documentos ou laudos, pode mandar a foto por aqui! 🌿")
            add_to_history(phone, "assistant", reply)
            return reply

        # --- Gerar Resposta / Próxima Pergunta ---
        reply = self._generate_ai_reply(message, phone, media_base64, mime_type)
        add_to_history(phone, "assistant", reply)
        return reply

    def _extrair_agendamento_ia(self, message: str) -> dict:
        """
        Usa o LLM para extrair data e hora de uma mensagem de agendamento.
        Retorna: {"data": "YYYY-MM-DD", "hora": "HH:MM"} ou None.
        """
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
            import json
            # Limpar markdown se houver
            clean_content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_content)
        except:
            return None

    def _obter_info_agenda(self, query: str) -> str:
        """
        Consulta o Google Calendar para verificar disponibilidade simplificada.
        """
        print(f"DEBUG: [Agent Dr. Anderson] Triggered agenda check for: {query[:30]}", flush=True)
        try:
            amanha = datetime.now() + timedelta(days=1)
            slots = calendar_service.list_free_slots(amanha)
            
            if not calendar_service.service:
                return "SISTEMA: A agenda do Dr. Anderson é de terça a sexta, das 09h às 18h. INSTRUÇÃO: Informe que o médico confirmará o horário exato após o cadastro."
            
            if slots:
                return f"SISTEMA: Agenda consultada! Horários disponíveis encontrados: {', '.join(slots[:3])}. INSTRUÇÃO: Sugira esses horários ao paciente."
            else:
                return "SISTEMA: Agenda cheia! Informe que buscaremos um encaixe."
        except Exception as e:
            print(f"DEBUG: [Agent Dr. Anderson] Erro na consulta da agenda: {e}", flush=True)
            return "SISTEMA: Problema ao ler agenda."

    def _handle_triagem(self, message: str, phone: str, media_base64, mime_type) -> str:
        state = get_state(phone)
        is_first = not state.get("greeted", False)
        prompt = SYSTEM_PROMPT_BASE
        if is_first:
            state["greeted"] = True
            set_state(phone, state)
            prompt += "\n\nIMPORTANTE: Primeira mensagem. Cumprimente e pergunte sobre agendamento."
        else:
            prompt += "\n\nREGRAS: SEM SAUDAÇÃO."

        keywords = ["vaga", "horário", "agenda", "disponib", "segunda", "terça", "quarta", "quinta", "sexta", "amanhã", "próximos", "atendimento", "consulta", "marcar", "agendar"]
        if any(k in message.lower() for k in keywords):
            info = self._obter_info_agenda(message)
            prompt += f"\n\n--- DADOS REAIS DO SISTEMA AGORA ---\n{info}\REDACTED"

        messages = [{"role": "system", "content": prompt}]
        if state["history"]: messages.extend(state["history"][:-1])
        messages.append({"role": "user", "content": message})
        resp = ai_manager.chat_completion(messages=messages, temperature=0.3)
        return resp.get("content", "Deseja agendar uma consulta?")

    def _handle_post_registration(self, message: str, phone: str, media_base64, mime_type) -> str:
        state = get_state(phone)
        prompt = SYSTEM_PROMPT_BASE + "\n\nPaciente já cadastrado. "
        
        # Tentar agendar se houver intenção clara
        agendamento = self._extrair_agendamento_ia(message)
        if agendamento and agendamento.get("data") and agendamento.get("hora"):
            try:
                dt_str = f"{agendamento['data']} {agendamento['hora']}"
                dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                
                # Criar evento
                dados = state.get("dados", {})
                paciente_nome = dados.get("nome", "Paciente")
                summary = f"Consulta: {paciente_nome}"
                desc = f"Agendado automaticamente pela LIA via WhatsApp.\nTelefone: {phone}\nEmail: {dados.get('email', 'N/A')}"
                
                ev = calendar_service.create_event(dt_obj, dt_obj + timedelta(hours=1), summary, desc, dados.get('email'))
                if ev:
                    reply = f"Maravilha, {paciente_nome}! Sua consulta foi reservada no sistema para o dia {dt_obj.strftime('%d/%m/%Y')} às {dt_obj.strftime('%H:%M')}. Até lá! 🌿📅"
                    add_to_history(phone, "assistant", reply)
                    return reply
            except Exception as e:
                print(f"DEBUG: [Agent Dr. Anderson] Erro no agendamento: {e}", flush=True)

        prompt += "Use os dados de agenda abaixo para responder diretamente à dúvida."
        
        # Injetar info de agenda com detecção mais ampla
        keywords = ["vaga", "horário", "agenda", "disponib", "segunda", "terça", "quarta", "quinta", "sexta", "amanhã", "próximos", "atendimento", "consulta", "marcar", "agendar"]
        if any(k in message.lower() for k in keywords):
            info = self._obter_info_agenda(message)
            prompt += f"\n\n--- DADOS REAIS DO SISTEMA AGORA ---\n{info}\REDACTED"

        messages = [{"role": "system", "content": prompt}]
        if state["history"]: messages.extend(state["history"][:-1])
        messages.append({"role": "user", "content": message})
            
        resp = ai_manager.chat_completion(messages=messages, temperature=0.3)
        return resp.get("content", "Obrigada! Entraremos em contato em breve para confirmar o horário.")

    def _generate_ai_reply(self, message: str, phone: str, media_base64, mime_type) -> str:
        state = get_state(phone)
        step = state["step"]
        
        pergunta_map = {
            "condicao_saude": "Qual condição de saúde ou problema clínico você pretende tratar?",
            "historico_cannabis": "Você já fez ou faz uso de algum medicamento à base de cannabis medicinal?",
            "idade": "Qual é a sua idade?",
            "nome": "Qual é o seu nome completo?",
            "email": "Qual é o seu melhor e-mail?",
        }
        
        proxima_pergunta = pergunta_map.get(step, "")
        state["last_asked"] = step
        set_state(phone, state)

        prompt = SYSTEM_PROMPT_BASE + f"\n\nFLUXO SDR: Não saude. Pergunta AGORA: \"{proxima_pergunta}\""
        if "vaga" in message.lower() or "horário" in message.lower():
            prompt += f"\n\nCONTEXTO AGENDA: {self._obter_info_agenda(message)}"

        messages = [{"role": "system", "content": prompt}]
        if state["history"]: messages.extend(state["history"][:-1])
        messages.append({"role": "user", "content": message})

        resp = ai_manager.chat_completion(messages=messages, temperature=0.3)
        return resp.get("content", proxima_pergunta)

# Instância global
dr_anderson_agent = DrAndersonAgent()
