import sys
import os

# Adicionar diretório raiz ao path para importar módulos do projeto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_cors_livre import create_app
from models import db, Profissional
from models_ai import AIAgent, CrewConfig, CrewAgentAssociation

import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_agents():
    """Sincroniza agentes definidos no código com o banco de dados"""
    app = create_app()
    
    with app.app_context():
        logger.info("Iniciando sincronização de agentes...")
        
        # Obter um usuário admin para atribuir a criação (primeiro admin encontrado)
        admin_user = Profissional.query.filter_by(role='admin').first()
        if not admin_user:
            logger.error("Nenhum usuário admin encontrado para atribuir a criação dos agentes.")
            return
        
        creator_id = admin_user.id
        logger.info(f"Usando admin ID {creator_id} como criador dos agentes.")
        
        # Lista de definições de agentes hardcoded
        # Precisamos instanciar para pegar as propriedades ou definir manualmente aqui
        # Vou definir manualmente baseado no código para garantir precisão e evitar instanciar LLMs agora
        
        agents_data = [
            {
                "nome": "Agente Conversacional",
                "role": "Recepcionista Médica Inteligente",
                "goal": "Acolher pacientes, entender suas necessidades iniciais...",
                "backstory": "Você é a primeira interface de contato do paciente...",
                "max_iter": 3
            },
            {
                "nome": "Especialista em Prontuários",
                "role": "Organizador de Prontuários",
                "goal": "Estruturar e organizar dados clínicos desestruturados...",
                "backstory": "Especialista em organização de dados médicos...",
                "max_iter": 3
            },
            {
                "nome": "Biomédico",
                "role": "Analista de Exames Laboratoriais",
                "goal": "Analisar exames laboratoriais e identificar biomarcadores...",
                "backstory": "Você é um biomédico sênior com doutorado em patologia clínica...",
                "max_iter": 3
            },
            {
                "nome": "Especialista em Relatórios",
                "role": "Redator Médico Técnico",
                "goal": "Compilar todas as análises em um relatório coeso...",
                "backstory": "Você é especialista em comunicação científica médica...",
                "max_iter": 3
            },
            {
                "nome": "Farmacêutico Cannabis",
                "role": "Especialista em Canabinoides",
                "goal": "Sugerir ajustes posológicos e analisar interações medicamentosas...",
                "backstory": "Farmacêutico com especialização em sistema endocanabinoide...",
                "max_iter": 3
            },
            {
                "nome": "Supervisor",
                "role": "Supervisor de Equipe Médica",
                "goal": "Coordenar e supervisionar o trabalho de todos os agentes...",
                "backstory": "Gestor médico experiente, com décadas liderando equipes...",
                "allow_delegation": True,
                "max_iter": 5
            },
            {
                "nome": "Acompanhante Terapêutico",
                "role": "Acompanhante Terapêutico Cannabis",
                "goal": "Realizar follow-up clínico automatizado e gerar evoluções estruturadas...",
                "backstory": """Você é um Agente de Acompanhamento Terapêutico especializado em pacientes em tratamento com Cannabis Medicinal.
        Seu papel é realizar follow-up clínico automatizado, personalizado de acordo com a indicação terapêutica do paciente, acessando dados estruturados do prontuário eletrônico do sistema SIAP (Aracanabis).
        
        Você deve:
        1. Consultar o prontuário do paciente e identificar:
           - Indicação terapêutica principal (ex: dor crônica, ansiedade, insônia)
           - Escala basal do sintoma (baseline)
           - Posologia atual (ex: CBD 25mg/noite)
           - Data de início do tratamento
           - Tempo de uso em dias
           - Presença de comorbidades relevantes (se disponível)

        2. Formular perguntas de follow-up específicas de acordo com a indicação:
           Se dor: Perguntar intensidade média da dor nos últimos 3 dias (escala 0–10)
           Se ansiedade: Perguntar intensidade média da ansiedade na última semana (0–10)
           Se insônia: Perguntar qualidade do sono e número de noites com melhora desde início
           Evite perguntas genéricas. Seja objetivo e centrado no sintoma tratado.

        3. Perguntar adicionalmente:
           - Se houve efeitos adversos
           - Se houve dificuldade em manter a posologia prescrita

        4. Após receber as respostas (em uma segunda etapa), realizar raciocínio clínico considerando:
           - Baseline do sintoma
           - Escala atual
           - Tempo de uso
           - Dose atual
           - Presença ou ausência de efeitos adversos
           - Adesão ao tratamento

        5. Avaliar a resposta terapêutica como: Ausente, Parcial ou Adequada.

        6. Sugerir uma das seguintes condutas (para validação médica):
           - Manutenção da dose atual
           - Considerar titulação gradual
           - Considerar redução da dose
           - Reavaliação médica necessária

        IMPORTANTE: Você não está autorizado a prescrever, modificar ou ajustar doses diretamente.
        
        7. Gerar uma evolução clínica estruturada contendo:
           - Dia de acompanhamento (ex: D14)
           - Sintoma alvo
           - Baseline
           - Escala atual
           - Percentual estimado de melhora
           - Presença de efeitos adversos
           - Nível de adesão
           - Sugestão de conduta
        """,
                "max_iter": 3
            }
        ]
        
        agent_db_map = {}
        
        for agent_data in agents_data:
            existing_agent = AIAgent.query.filter_by(nome=agent_data["nome"]).first()
            
            if existing_agent:
                logger.info(f"Atualizando agente existente: {agent_data['nome']}")
                existing_agent.role = agent_data["role"]
                existing_agent.goal = agent_data["goal"]
                existing_agent.backstory = agent_data["backstory"]
                # Preservar configurações manuais se quiser, ou forçar update
                existing_agent.max_iter = agent_data.get("max_iter", 3)
                existing_agent.allow_delegation = agent_data.get("allow_delegation", False)
                agent_db_map[agent_data["nome"]] = existing_agent
            else:
                logger.info(f"Criando novo agente: {agent_data['nome']}")
                new_agent = AIAgent(
                    nome=agent_data["nome"],
                    role=agent_data["role"],
                    goal=agent_data["goal"],
                    backstory=agent_data["backstory"],
                    max_iter=agent_data.get("max_iter", 3),
                    allow_delegation=agent_data.get("allow_delegation", False),
                    created_by=creator_id,
                    is_active=True,
                    verbose=True,
                    memory=True,
                    temperature=0.7
                )
                db.session.add(new_agent)
                db.session.flush() # Para gerar ID
                agent_db_map[agent_data["nome"]] = new_agent
        
        db.session.commit()
        
        # Agora sincronizar a Crew "Aracannabis Core Team"
        crew_name = "Equipe Multidisciplinar Aracannabis"
        existing_crew = CrewConfig.query.filter_by(nome=crew_name).first()
        
        if not existing_crew:
            logger.info(f"Criando Crew: {crew_name}")
            existing_crew = CrewConfig(
                nome=crew_name,
                descricao="Equipe principal de atendimento e análise clínica multidisciplinar",
                process='hierarchical',
                created_by=creator_id,
                is_active=True,
                verbose=True,
                memory=True
            )
            db.session.add(existing_crew)
            db.session.commit()
        
        # Atualizar associações
        # Limpar existentes
        CrewAgentAssociation.query.filter_by(crew_id=existing_crew.id).delete()
        
        # Adicionar na ordem correta
        agent_order = [
            "Agente Conversacional",
            "Especialista em Prontuários",
            "Biomédico",
            "Especialista em Relatórios",
            "Farmacêutico Cannabis",
            "Acompanhante Terapêutico", # Nosso novo agente!
            "Supervisor"
        ]
        
        for idx, agent_name in enumerate(agent_order):
            if agent_name in agent_db_map:
                agent = agent_db_map[agent_name]
                assoc = CrewAgentAssociation(
                    crew_id=existing_crew.id,
                    agent_id=agent.id,
                    order=idx
                )
                db.session.add(assoc)
        
        db.session.commit()
        logger.info("Sincronização concluída com sucesso!")

if __name__ == "__main__":
    sync_agents()
