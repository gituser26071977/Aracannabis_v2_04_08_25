from models import db, Evolucao, Paciente, Dosagem, LogAtividade 
from datetime import datetime
# from langchain_core.tools import tool # Remover importação do decorador @tool

# É importante que estas funções sejam chamadas dentro de um contexto de aplicação Flask
# para que db.session funcione. A CrewAI precisará ser configurada para rodar
# dentro desse contexto ou as funções precisarão de alguma forma de obter o app_context.
# Por simplicidade inicial, vamos assumir que o contexto está disponível quando a rota chama.

# @tool # Remover decorador
def save_evolution_to_db(paciente_id: int, profissional_id: int, narrative_evolution: str, data_evolucao_str: str) -> dict:
    """Salva a narrativa da evolução de um paciente no banco de dados.
    Argumentos:
        paciente_id (int): ID do paciente.
        profissional_id (int): ID do profissional que registra.
        narrative_evolution (str): O texto da evolução.
        data_evolucao_str (str): Data da evolução no formato 'YYYY-MM-DD'.
    Retorna um dicionário com a evolução salva ou um erro.
    """
    try:
        data_evolucao_obj = datetime.strptime(data_evolucao_str, '%Y-%m-%d').date()
        
        nova_evolucao = Evolucao(
            paciente_id=paciente_id,
            profissional_id=profissional_id,
            nota_evolucao=narrative_evolution,
            data_evolucao=data_evolucao_obj
        )
        db.session.add(nova_evolucao)
        db.session.commit()

        return {"success": True, "evolucao_id": nova_evolucao.id, "message": "Evolução salva com sucesso."}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Erro ao salvar evolução no BD: {str(e)}"}

# @tool # Remover decorador
def save_dosage_to_db(paciente_id: int, data_dosagem_str: str, dosage_text: str, 
                        drops: int = None, daily_frequency: int = None, 
                        cbd_concentration_mg_ml: float = None, thc_concentration_mg_ml: float = None,
                        cbg_concentration_mg_ml: float = None, cbn_concentration_mg_ml: float = None) -> dict:
    """Salva os detalhes de uma dosagem de cannabis medicinal no banco de dados e atualiza o resumo no paciente.
    Argumentos:
        paciente_id (int): ID do paciente.
        data_dosagem_str (str): Data da dosagem no formato 'YYYY-MM-DD'.
        dosage_text (str): Descrição textual completa da dosagem.
        drops (int, opcional): Número de gotas por dose.
        daily_frequency (int, opcional): Número de vezes ao dia.
        cbd_concentration_mg_ml (float, opcional): Concentração de CBD em mg/ml.
        thc_concentration_mg_ml (float, opcional): Concentração de THC em mg/ml.
        cbg_concentration_mg_ml (float, opcional): Concentração de CBG em mg/ml.
        cbn_concentration_mg_ml (float, opcional): Concentração de CBN em mg/ml.
    Retorna um dicionário com a dosagem salva ou um erro.
    """
    try:
        data_dosagem_obj = datetime.strptime(data_dosagem_str, '%Y-%m-%d').date()

        if not dosage_text: # Descrição textual é crucial
            return {"success": False, "error": "Descrição textual da dosagem (dosage_text) é obrigatória."}

        nova_dosagem = Dosagem(
            paciente_id=paciente_id,
            data=data_dosagem_obj,
            dosagem=dosage_text, # Descrição textual principal
            gotas=drops,
            frequencia_diaria=daily_frequency,
            concentracao_cbd=cbd_concentration_mg_ml,
            concentracao_thc=thc_concentration_mg_ml,
            concentracao_cbg=cbg_concentration_mg_ml,
            concentracao_cbn=cbn_concentration_mg_ml
        )
        db.session.add(nova_dosagem)
        # O commit será feito após todas as operações de banco de dados relacionadas à evolução.
        # Se esta ferramenta for chamada independentemente, um commit seria necessário aqui.
        # Por enquanto, vamos assumir que o commit principal acontece na rota ou no final da crew.
        # Para maior robustez, cada ferramenta que modifica o BD deveria fazer seu próprio commit
        # ou a lógica da crew/rota deve gerenciar a transação.
        # Vamos adicionar um commit aqui para tornar a ferramenta mais autônoma.
        db.session.commit()


        # Atualizar o campo 'dosagem' no modelo Paciente
        paciente = Paciente.query.get(paciente_id)
        if paciente:
            paciente.dosagem = dosage_text # Atualiza o resumo da dosagem no paciente
            paciente.updated_at = datetime.utcnow()
            db.session.commit() # Commit da atualização do paciente
        else:
            # Isso não deveria acontecer se o paciente_id for válido
            return {"success": False, "dosagem_id": nova_dosagem.id, "warning": "Dosagem salva, mas paciente não encontrado para atualizar resumo."}


        return {"success": True, "dosagem_id": nova_dosagem.id, "message": "Dosagem salva e resumo do paciente atualizado."}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Erro ao salvar dosagem no BD: {str(e)}"}

# Nota: A função de atualizar o resumo da dosagem do paciente foi integrada em save_dosage_to_db.
# Se precisarmos dela separadamente, podemos criar update_patient_dosage_summary_tool.

# Exemplo de como você poderia usar essas ferramentas com CrewAI (ilustrativo):
# from crewai import Tool
#
# evolution_db_tool = Tool(
# name="Save Evolution to Database",
# func=save_evolution_to_db,
# description="Salva a narrativa da evolução de um paciente no banco de dados. "
# "Input: paciente_id (int), profissional_id (int), narrative_evolution (str), data_evolucao_str (str 'YYYY-MM-DD')."
# )
#
# dosage_db_tool = Tool(
# name="Save Dosage to Database",
# func=save_dosage_to_db,
#     description="Salva os detalhes de uma dosagem de cannabis medicinal no banco de dados e atualiza o resumo no paciente. "
#                 "Input: paciente_id (int), data_dosagem_str (str 'YYYY-MM-DD'), dosage_text (str), "
#                 "drops (int, opcional), daily_frequency (int, opcional), "
#                 "cbd_concentration_mg_ml (float, opcional), thc_concentration_mg_ml (float, opcional), "
#                 "cbg_concentration_mg_ml (float, opcional), cbn_concentration_mg_ml (float, opcional)."
# )
