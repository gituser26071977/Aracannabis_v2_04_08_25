import json
import logging
from typing import Dict, Any

from services.ai_agents import ai_manager
from models import db, Profissional, Paciente # Imports do SIAP
from sqlalchemy import or_

logger = logging.getLogger(__name__)

class DrAndersonAgent:
    """Secretária Virtual de IA para o Dr. Anderson"""
    
    SYSTEM_PROMPT = """Você é a LIA, secretária virtual exclusiva do Dr. Anderson Holzwarth, especialista em tratamentos avançados com Cannabis Medicinal pela Aracannabis.

Seu objetivo é:
1. Atender pacientes interessados em consulta de forma acolhedora e empática.
2. Tirar dúvidas frequentes sobre o tratamento com cannabis medicinal, custos, retornos e documentação.
3. Coletar dados preliminares do paciente para o sistema (Nome completo, CPF, RG, Endereço e e-mail).
4. Auxiliar no recebimento de laudos prévios ou documentos de identidade (via imagem/documento).

INFORMAÇÕES ÚTEIS:
- Consultas são realizadas por telemedicina ou presencial (conforme combinação prévia).
- O Dr. Anderson atende pacientes em todo o Brasil.
- Custos de consulta: informar que enviará o link de pagamento ou os dados bancários na sequência do atendimento para confirmar a agenda.
- Retorno: incluso em até 30 dias.

COMPORTAMENTO:
- Seja sempre poli, cordial e mantenha uma linguagem acessível.
- Responda de forma concisa no WhatsApp, evitando blocos gigantes de texto.
- Não prescreva medicamentos nem dê diagnósticos concretos, sempre direcione para a consulta médica.
- Faça no máximo UMA pergunta por vez para coletar dados do paciente.
- AGENDAMENTO DE CONSULTAS: Quando o paciente decidir pelo agendamento, indique os horários na agenda ou colete detalhes para agendamento direto na nossa integração via calendário `lia.visualsmartflow@gmail.com`.
"""

    def process_message(self, message: str, phone: str, media_base64: str = None, mime_type: str = None) -> str:
        """
        Processa uma mensagem recebida e retorna a resposta da IA.
        """
        # Obter paciente se existir
        paciente = Paciente.query.filter(Paciente.telefone.like(f"%{phone[-8:]}%")).first()
        paciente_nome = paciente.nome if paciente else "Novo Paciente"

        # Adicionar contexto dinâmico
        dynamic_prompt = self.SYSTEM_PROMPT + f"\n\nContexto Atual:\n- Paciente detectado: {paciente_nome}\n- O paciente já está cadastrado? {'Sim' if paciente else 'Não'}\n"
        
        # Histórico de mensagens simplificado (em produção, o ideal é usar o DB ou redis)
        messages = [
            {"role": "system", "content": dynamic_prompt}
        ]

        if media_base64:
            # Temos imagem/documento!
            # Podemos usar a visão computacional
            user_msg = f"{message}\n[O usuário enviou uma imagem/documento associada]"
            try:
                vision_resp = ai_manager.vision_completion(
                    prompt="Extraia os dados deste documento (RG, CNH, Receita ou Laudo). Liste os campos principais encontrados e um resumo clínico se for laudo.",
                    image_data=f"data:{mime_type};base64,{media_base64}" if mime_type else media_base64
                )
                extra_context = vision_resp.get('content', '')
                user_msg += f"\n\nExtração do documento: {extra_context}\n\nResponda ao paciente confirmando o recebimento e continuidade do cadastro."
            except Exception as e:
                logger.error(f"Erro ao processar imagem para Dr Anderson: {e}")
                user_msg += "\n\n(A imagem não pôde ser processada pela IA, peça para enviar em PDF ou digitar os dados)."

            messages.append({"role": "user", "content": user_msg})
        else:
            messages.append({"role": "user", "content": message})

        # Processar com IA
        response = ai_manager.chat_completion(
            messages=messages,
            temperature=0.4,
            max_tokens=500
        )
        
        reply = response.get('content', "Desculpe, estou com instabilidade no momento. Pode repetir?")
        return reply

