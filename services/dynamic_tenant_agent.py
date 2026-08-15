import logging
import os
import json
import re
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app_cors_livre import create_app
from models import db, ConfiguracaoIA, Profissional, Consulta, Paciente
from services.ai_agents import ai_manager

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "siap-redis")
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
STATE_EXPIRY = 86400

# Identidade institucional padrão (usada quando ConfiguracaoIA não tem
# regras_adicionais preenchidas). Cada tenant pode sobrescrever via ConfiguracaoIA.
IDENTIDADE_PADRAO = (
    "INSTITUTO VITTALIS — onde a saúde e o bem-estar se encontram para moldar "
    "a sua melhor versão!\n"
    "Apresente o instituto com orgulho e acolhimento.\n"
    "Você NÃO deve dizer que somos uma clínica de Cannabis Medicinal, nem "
    "mencionar cannabis como identidade da instituição.\n"
)


class DynamicTenantAgent:
    """
    Agente SDR Genérico para Plataforma Multi-Tenant.

    - Carrega a identidade do tenant de ConfiguracaoIA (nome, tom de voz,
      posicionamento/regras).
    - Faz pré-atendimento: tira dúvidas sobre o instituto e coleta os dados
      essenciais do paciente (nome, telefone, queixa).
    - Agenda na tabela Consulta do SIAP (por tenant/profissional).
    """

    def __init__(self, profissional_id: int):
        self.profissional_id = profissional_id
        self.app = create_app()

    def get_state(self, phone: str) -> Dict:
        key = f"ia_state:tenant_{self.profissional_id}:{phone}"
        state_json = r.get(key)
        if state_json:
            state = json.loads(state_json)
            if "history" not in state:
                state["history"] = []
            return state

        new_state = {
            "step": "triagem",
            "dados": {},
            "history": [],
        }
        self.set_state(phone, new_state)
        return new_state

    def set_state(self, phone: str, state: Dict):
        key = f"ia_state:tenant_{self.profissional_id}:{phone}"
        r.set(key, json.dumps(state), ex=STATE_EXPIRY)

    def process_message(self, message: str, phone: str, media_base64: str = None, mime_type: str = None) -> str:
        with self.app.app_context():
            config = ConfiguracaoIA.query.filter_by(profissional_id=self.profissional_id).first()
            profissional = Profissional.query.get(self.profissional_id)

            if not config or not config.ativo:
                return "Desculpe, o Assistente de Inteligência Artificial desta clínica está desativado no momento."

            state = self.get_state(phone)
            state["history"].append({"role": "user", "content": message})
            if len(state["history"]) > 10:
                state["history"] = state["history"][-10:]

            agora = datetime.now()
            fim = agora + timedelta(days=7)
            consultas_existentes = Consulta.query.filter(
                Consulta.profissional_id == self.profissional_id,
                Consulta.data_hora >= agora,
                Consulta.data_hora <= fim,
                Consulta.status.in_(['agendada', 'confirmada'])
            ).all()

            horarios_ocupados = [c.data_hora.strftime("%d/%m/%Y %H:%M") for c in consultas_existentes]

            # Identidade do tenant: posicionamento institucional + regras adicionais.
            identidade = (config.regras_adicionais or "").strip() or IDENTIDADE_PADRAO
            nome_assistente = config.nome_assistente or "Assistente Virtual"
            valor_consulta = config.valor_consulta or "Não informado"

            # Coleta de pré-atendimento (dados essenciais) — simples e acolhedor.
            dados = state.get("dados", {})
            if not dados.get("nome"):
                nome = self._extrair_nome(message)
                if nome:
                    dados["nome"] = nome
            if not dados.get("telefone"):
                dados["telefone"] = phone

            system_prompt = f"""
Você é {nome_assistente}, assistente virtual do {profissional.nome} — Instituto Vittalis.

POSICIONAMENTO INSTITUCIONAL:
{identidade}

REGRAS E INFORMAÇÕES:
- Valor da consulta: {valor_consulta}
- Atendemos de Seg a Sex, 09h às 18h.
- Informações adicionais:
{config.regras_adicionais or 'Sem informações adicionais no momento.'}

HORÁRIOS OCUPADOS NESTA SEMANA (NÃO OFEREÇA ESTES):
{horarios_ocupados}

OBJETIVO DA CONVERSA:
1. Tirar dúvidas iniciais sobre o instituto e seus serviços, demonstrando empatia.
2. Fazer o PRÉ-ATENDIMENTO: coletar os dados essenciais do paciente de forma
   acolhedora (nome completo, telefone, motivo da consulta / queixa principal).
3. Se o paciente quiser agendar, ofereça horários livres baseando-se no horário
   comercial e ignorando a lista de horários ocupados.
4. Quando o paciente aprovar o dia e horário, você DEVE retornar a string exata
   no formato: "[MARCAR_CONSULTA: YYYY-MM-DD HH:MM]" no final de sua mensagem.
   Exemplo: "Perfeito, vou confirmar para você agora! [MARCAR_CONSULTA: 2026-03-24 10:00]".
* APENAS emita a tag [MARCAR_CONSULTA] se o paciente TIVER CONFIRMADO CLARAMENTE
  a data E hora.

IMPORTANTE:
- NUNCA se apresente como uma clínica de Cannabis Medicinal.
- NUNCA dê diagnósticos ou prescrições.
- Mantenha as respostas curtas, como mensagens normais de WhatsApp. Não seja prolixo.

Lembre-se: Hoje é {agora.strftime("%d/%m/%Y")}.
"""

            texto_historico = "\n".join([f"{msg['role']}: {msg['content']}" for msg in state["history"]])
            prompt_final = f"{system_prompt}\n\nHistórico do Paciente:\n{texto_historico}\n\nResponda agora ao paciente:"

            ai_response = ai_manager.chat_completion(prompt_final, system_instruction=system_prompt)

            match = re.search(r"\[MARCAR_CONSULTA:\s*(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2})\]", ai_response)
            if match:
                data_str = match.group(1)

                try:
                    nome_paciente = dados.get("nome") or f"Lead WhatsApp ({phone})"
                    novo_paciente = Paciente(
                        profissional_responsavel_id=self.profissional_id,
                        nome=nome_paciente,
                        telefone=phone,
                        consentimento_lgpd=True,
                    )
                    db.session.add(novo_paciente)
                    db.session.flush()

                    da_hora = datetime.strptime(data_str, "%Y-%m-%d %H:%M")
                    nova_consulta = Consulta(
                        paciente_id=novo_paciente.id,
                        profissional_id=self.profissional_id,
                        data_hora=da_hora,
                        tipo_consulta='presencial',
                        observacoes="Agendado remotamente pelo Assistente Virtual (IA)",
                    )
                    db.session.add(nova_consulta)
                    db.session.commit()

                    logger.info(f"[Multi-Tenant Agent] Consulta marcada para Profissional {self.profissional_id} em {data_str}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"[Multi-Tenant Agent] Erro ao marcar consulta automatica: {e}")

                ai_response = ai_response.replace(match.group(0), "").strip()

            state["dados"] = dados
            state["history"].append({"role": "model", "content": ai_response})
            self.set_state(phone, state)

            return ai_response

    def _extrair_nome(self, message: str) -> Optional[str]:
        """Tentativa simples de extrair o nome em mensagens como 'Meu nome é X'."""
        m = re.search(r"(?:meu nome é|me chamo|sou)\s+([A-Za-zÀ-ú]+(?:\s+[A-Za-zÀ-ú]+){0,3})", message, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return None
