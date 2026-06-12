import logging
import os
import json
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

class DynamicTenantAgent:
    """
    Agente SDR Genérico para Plataforma Multi-Tenant.
    Ele carrega o System Prompt dinamicamente do banco de dados (tabela ConfiguracaoIA)
    e interage com os agendamentos nativos da plataforma SIAP (tabela Consulta).
    
    SEGURANÇA: Valida que o profissional_id pertence ao usuário autenticado
    antes de processar qualquer mensagem.
    """
    def __init__(self, profissional_id: int, validating_user_id: int = None):
        self.profissional_id = profissional_id
        self.validating_user_id = validating_user_id or profissional_id
        # Cria context local para funcionar em threads isoladas de webhook
        self.app = create_app()
        
    def _validar_profissional(self) -> bool:
        """
        Valida se o profissional_id do agente pode ser usado pelo validating_user_id.
        Apenas o próprio profissional ou admins podem usar este agente.
        
        Returns:
            True se válido, False caso contrário
        """
        from models import Profissional
        
        with self.app.app_context():
            # Buscar profissional dono do agente
            agente_profissional = Profissional.query.get(self.profissional_id)
            if not agente_profissional:
                logger.error(f"[Multi-Tenant Agent] Profissional {self.profissional_id} não encontrado")
                return False
            
            # Buscar usuário que está fazendo a requisição
            requesting_user = Profissional.query.get(self.validating_user_id)
            if not requesting_user:
                logger.error(f"[Multi-Tenant Agent] Usuário {self.validating_user_id} não encontrado")
                return False
            
            # Admin e superadmin podem usar qualquer agente
            if requesting_user.role in ('admin', 'superadmin'):
                logger.info(f"[Multi-Tenant Agent] Admin {self.validating_user_id} usando agente do profissional {self.profissional_id}")
                return True
            
            # Apenas o próprio profissional pode usar seu agente
            if self.profissional_id == self.validating_user_id:
                logger.info(f"[Multi-Tenant Agent] Profissional {self.validating_user_id} usando seu próprio agente")
                return True
            
            logger.warning(f"[Multi-Tenant Agent] Acesso negado: usuário {self.validating_user_id} tentou usar agente do profissional {self.profissional_id}")
            return False

    def get_state(self, phone: str) -> Dict:
        key = f"ia_state:tenant_{self.profissional_id}:{phone}"
        state_json = r.get(key)
        if state_json:
            state = json.loads(state_json)
            if "history" not in state: state["history"] = []
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
        """
        Processa mensagem do WhatsApp com validação de acesso.
        
        Args:
            message: Texto da mensagem
            phone: Telefone do paciente
            media_base64: Mídia opcional (imagem)
            mime_type: Tipo da mídia
            
        Returns:
            Resposta do agente ou mensagem de erro
        """
        # PRIMEIRO: Validar acesso
        if not self._validar_profissional():
            logger.warning(f"[Multi-Tenant Agent] Acesso negado para profissional_id={self.profissional_id}, validating_user_id={self.validating_user_id}")
            return "Desculpe, você não tem permissão para usar este assistente virtual."
        
        with self.app.app_context():
            config = ConfiguracaoIA.query.filter_by(profissional_id=self.profissional_id).first()
            profissional = Profissional.query.get(self.profissional_id)
            
            if not config or not config.ativo:
                logger.info(f"[Multi-Tenant Agent] Agente do profissional {self.profissional_id} está desativado")
                return "Desculpe, o Assistente de Inteligência Artificial desta clínica está desativado no momento."

            state = self.get_state(phone)
            state["history"].append({"role": "user", "content": message})
            if len(state["history"]) > 10: state["history"] = state["history"][-10:]

            # Consultar disponibilidades dos proximos 7 dias para evitar overbooking
            agora = datetime.now()
            fim = agora + timedelta(days=7)
            consultas_existentes = Consulta.query.filter(
                Consulta.profissional_id == self.profissional_id,
                Consulta.data_hora >= agora,
                Consulta.data_hora <= fim,
                Consulta.status.in_(['agendada', 'confirmada'])
            ).all()
            
            horarios_ocupados = [c.data_hora.strftime("%d/%m/%Y %H:%M") for c in consultas_existentes]
            logger.info(f"[Multi-Tenant Agent] Profissional {self.profissional_id}: {len(horarios_ocupados)} horários ocupados")

            system_prompt = f"""
Você é {config.nome_assistente}, assistente virtual de atendimento de {profissional.nome}.
Seu tom de voz é: {config.tom_de_voz}.

REGRAS E INFORMAÇÕES DA CLÍNICA:
Valor da consulta: {config.valor_consulta or 'Não informado'}
Informações adicionais do doutor:
{config.regras_adicionais or 'Sem informações adicionais no momento.'}

HORÁRIOS OCUPADOS NESTA SEMANA (NÃO OFEREÇA ESTES):
{horarios_ocupados}
Você atende presencialmente/online em horário comercial. Ofereça horários sugestivos durante essa semana que não estejam na lista de ocupados. Atendemos de Seg a Sex, 09h as 18h.

OBJETIVO DA CONVERSA:
1. Tirar duvidas iniciais e demonstrar empatia.
2. Se o paciente quiser agendar, ofereça horários livres baseando-se no horário comercial e ignorando a lista de horários ocupados.
3. Quando o paciente aprovar o dia e horário, você DEVE retornar a string exata no formato: "[MARCAR_CONSULTA: YYYY-MM-DD HH:MM]" no final de sua mensagem. Exemplo: "Perfeito, vou confirmar para você agora! [MARCAR_CONSULTA: 2026-03-24 10:00]".
* APENAS emita a tag [MARCAR_CONSULTA] se o paciente TIVER CONFIRMADO CLARAMENTE a data E hora.

Lembre-se: Hoje é {agora.strftime("%d/%m/%Y")}.
Mantenha as respostas curtas, como mensagens normais de WhatsApp. Não seja prolixo.
"""
            
            # Montar histórico para Gemini
            texto_historico = "\n".join([f"{msg['role']}: {msg['content']}" for msg in state["history"]])
            prompt_final = f"{system_prompt}\n\nHistórico do Paciente:\n{texto_historico}\n\nResponda agora ao paciente:"

            ai_response = ai_manager.chat_completion(prompt_final, system_instruction=system_prompt)
            
            # Interceptar intento de Agendamento
            import re
            match = re.search(r"\[MARCAR_CONSULTA:\s*(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2})\]", ai_response)
            if match:
                data_str = match.group(1)
                
                try:
                    # Tenta criar o Lead (Nome genérico inicial, caso não tenha extraído)
                    # Idealmente fariamos um sub-prompt aqui para extrair o nome, mas simplificaremos por agora
                    novo_paciente = Paciente(
                        profissional_responsavel_id=self.profissional_id,
                        nome=f"Lead WhatsApp ({phone})",
                        telefone=phone,
                        consentimento_lgpd=True
                    )
                    db.session.add(novo_paciente)
                    db.session.flush()

                    # Criar Consulta Local no SIAP
                    da_hora = datetime.strptime(data_str, "%Y-%m-%d %H:%M")
                    nova_consulta = Consulta(
                        paciente_id=novo_paciente.id,
                        profissional_id=self.profissional_id,
                        data_hora=da_hora,
                        tipo_consulta='presencial',
                        observacoes="Agendado remotamente pelo Assistente Virtual (IA)"
                    )
                    db.session.add(nova_consulta)
                    db.session.commit()
                    
                    logger.info(f"[Multi-Tenant Agent] Consulta marcada para Profissional {self.profissional_id} em {data_str}")
                    
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"[Multi-Tenant Agent] Erro ao marcar consulta automatica: {e}")

                # Limpar a tag para não ir pro whatsApp
                ai_response = ai_response.replace(match.group(0), "").strip()

            state["history"].append({"role": "model", "content": ai_response})
            self.set_state(phone, state)

            return ai_response
