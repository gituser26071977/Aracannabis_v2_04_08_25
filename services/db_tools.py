from sqlalchemy import or_
from models import (
    db,
    Evolucao,
    Paciente,
    Dosagem,
    Sintoma,
    Exame,
    CompartilhamentoPaciente,
    Profissional
)
from models_extra import UsuarioAssociacao
from datetime import datetime
from flask import g
from typing import Dict, List, Any, Optional, Tuple
# from langchain_core.tools import tool # Remover importação do decorador @tool

# É importante que estas funções sejam chamadas dentro de um contexto de aplicação Flask
# para que db.session funcione. A CrewAI precisará ser configurada para rodar
# dentro desse contexto ou as funções precisarão de alguma forma de obter o app_context.
# Por simplicidade inicial, vamos assumir que o contexto está disponível quando a rota chama.

# @tool # Remover decorador
def save_evolution_to_db(
    paciente_id: int,
    profissional_id: int,
    narrative_evolution: str,
    data_evolucao_str: str,
    anamnese: str = None,
    exame_fisico: str = None,
    sinais_vitais: dict = None,
    exames_resultados: str = None,
    avaliacao: str = None,
    plano: str = None,
) -> dict:
    """Salva a evolução (padrão SOAP estruturado) de um paciente no banco.

    Argumentos:
        paciente_id (int): ID do paciente.
        profissional_id (int): ID do profissional que registra.
        narrative_evolution (str): Texto livre (visão geral) da evolução.
        data_evolucao_str (str): Data no formato 'YYYY-MM-DD'.
        anamnese (str): Subjetivo — queixa/HPI/sintomas.
        exame_fisico (str): Objetivo — achados do exame físico.
        sinais_vitais (dict): Objetivo — PA/FC/FR/temperatura/SpO2/peso/altura.
        exames_resultados (str): Objetivo — resultados dos últimos exames.
        avaliacao (str): Avaliação — hipóteses/diagnóstico/impressão.
        plano (str): Plano — conduta/exames/retorno.
    Retorna um dicionário com a evolução salva ou um erro.
    """
    try:
        # Obter paciente para herdar associacao_id (multi-tenant)
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return {"success": False, "error": "Paciente não encontrado"}

        data_evolucao_obj = datetime.strptime(data_evolucao_str, '%Y-%m-%d')

        nova_evolucao = Evolucao(
            paciente_id=paciente_id,
            associacao_id=paciente.associacao_id,
            profissional_id=profissional_id,
            nota_evolucao=narrative_evolution,
            anamnese=anamnese,
            exame_fisico=exame_fisico,
            sinais_vitais=sinais_vitais,
            exames_resultados=exames_resultados,
            avaliacao=avaliacao,
            plano=plano,
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

        # Obter paciente para herdar associacao_id (multi-tenant)
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return {"success": False, "error": "Paciente não encontrado"}

        nova_dosagem = Dosagem(
            paciente_id=paciente_id,
            associacao_id=paciente.associacao_id,
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

# ========== DatabaseTools Class for CrewAI ==========

class DatabaseTools:
    """Classe para ferramentas de banco de dados usadas pelo sistema multi-agente"""
    
    def __init__(self, profissional_id: Optional[int] = None, associacao_id: Optional[int] = None):
        self.profissional_id = profissional_id or None
        self.associacao_id = associacao_id or (g.current_association.id if hasattr(g, 'current_association') and g.current_association else None)

    def _paciente_acessivel(self, paciente: Paciente) -> bool:
        if not paciente:
            return False

        # 1. Validar isolamento de associação (CRÍTICO - multi-tenant)
        if self.associacao_id:
            # Verificar se paciente pertence à associação do profissional
            if not paciente.profissional_responsavel_id:
                return False
            
            profissional_paciente = Profissional.query.get(paciente.profissional_responsavel_id)
            if not profissional_paciente:
                return False
            
            # Verificar se o profissional do paciente pertence à mesma associação
            link_paciente = UsuarioAssociacao.query.filter_by(
                profissional_id=profissional_paciente.id,
                associacao_id=self.associacao_id,
                status='active'
            ).first()
            
            if not link_paciente:
                return False  # Paciente de outra associação - BLOQUEADO

        # 2. Validar permissão do profissional
        if not self.profissional_id:
            return True

        if paciente.profissional_responsavel_id == self.profissional_id:
            return True

        compartilhado = CompartilhamentoPaciente.query.filter_by(
            paciente_id=paciente.id,
            profissional_id=self.profissional_id,
            ativo=True
        ).first()
        if compartilhado:
            return True

        return False

    def obter_paciente_com_acesso(self, paciente_id: int) -> Tuple[Optional[Paciente], Optional[str]]:
        """Retorna o paciente se o profissional tiver acesso, caso contrário sinaliza erro."""
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return None, f"Paciente com ID {paciente_id} não encontrado"
        if not self._paciente_acessivel(paciente):
            return None, "Acesso negado ao paciente solicitado"
        return paciente, None
   
    def buscar_paciente(self, paciente_id: int) -> Dict:
        """Busca informações de um paciente pelo ID"""
        paciente, error = self.obter_paciente_com_acesso(paciente_id)
        if error:
            return {"error": error}

        return {
            "id": paciente.id,
            "nome": paciente.nome,
            "email": paciente.email,
            "telefone": paciente.telefone,
            "data_nascimento": paciente.data_nascimento.isoformat() if paciente.data_nascimento else None,
            "condicao_medica": paciente.condicao_medica,
            "dosagem": paciente.dosagem,
            "created_at": paciente.created_at.isoformat() if paciente.created_at else None
        }
    
    def buscar_exames_paciente(self, paciente_id: int) -> List[Dict]:
        """Busca exames de um paciente"""
        paciente = Paciente.query.get(paciente_id)
        if not paciente or not self._paciente_acessivel(paciente):
            return [{"error": "Acesso negado ao paciente"}]

        try:
            exames = Exame.query.filter_by(paciente_id=paciente_id).order_by(Exame.data.desc()).all()
            return [
                {
                    "id": exame.id,
                    "titulo": exame.titulo,
                    "data": exame.data.isoformat() if exame.data else None,
                    "resultados": exame.resultados,
                    "observacoes": exame.observacoes,
                    "created_at": exame.created_at.isoformat() if exame.created_at else None
                }
                for exame in exames
            ]
        except Exception as e:
            return [{"error": f"Erro ao buscar exames: {str(e)}"}]
    
    def buscar_evolucoes_paciente(self, paciente_id: int) -> List[Dict]:
        """Busca evoluções clínicas de um paciente"""
        paciente = Paciente.query.get(paciente_id)
        if not paciente or not self._paciente_acessivel(paciente):
            return [{"error": "Acesso negado ao paciente"}]

        try:
            evolucoes = Evolucao.query.filter_by(paciente_id=paciente_id).order_by(Evolucao.data_evolucao.desc()).all()
            return [
                {
                    "id": evolucao.id,
                    "data_evolucao": evolucao.data_evolucao.isoformat() if evolucao.data_evolucao else None,
                    "nota_evolucao": evolucao.nota_evolucao,
                    "created_at": evolucao.created_at.isoformat() if evolucao.created_at else None
                }
                for evolucao in evolucoes
            ]
        except Exception as e:
            return [{"error": f"Erro ao buscar evoluções: {str(e)}"}]
    
    def buscar_dosagens_paciente(self, paciente_id: int) -> List[Dict]:
        """Busca dosagens de medicamentos de um paciente"""
        paciente = Paciente.query.get(paciente_id)
        if not paciente or not self._paciente_acessivel(paciente):
            return [{"error": "Acesso negado ao paciente"}]

        try:
            dosagens = Dosagem.query.filter_by(paciente_id=paciente_id).order_by(Dosagem.data.desc()).all()
            return [
                {
                    "id": dosagem.id,
                    "data": dosagem.data.isoformat() if dosagem.data else None,
                    "dosagem": dosagem.dosagem,
                    "gotas": dosagem.gotas,
                    "frequencia_diaria": dosagem.frequencia_diaria,
                    "concentracao_cbd": dosagem.concentracao_cbd,
                    "concentracao_thc": dosagem.concentracao_thc,
                    "concentracao_cbg": dosagem.concentracao_cbg,
                    "concentracao_cbn": dosagem.concentracao_cbn,
                    "created_at": dosagem.created_at.isoformat() if dosagem.created_at else None
                }
                for dosagem in dosagens
            ]
        except Exception as e:
            return [{"error": f"Erro ao buscar dosagens: {str(e)}"}]
    
    def buscar_sintomas_paciente(self, paciente_id: int) -> List[Dict]:
        """Busca sintomas relatados por um paciente"""
        paciente = Paciente.query.get(paciente_id)
        if not paciente or not self._paciente_acessivel(paciente):
            return [{"error": "Acesso negado ao paciente"}]

        try:
            sintomas = Sintoma.query.filter_by(paciente_id=paciente_id).order_by(Sintoma.data.desc()).all()
            return [
                {
                    "id": sintoma.id,
                    "data": sintoma.data.isoformat() if sintoma.data else None,
                    "descricao": sintoma.descricao,
                    "intensidade": sintoma.intensidade,
                    "created_at": sintoma.created_at.isoformat() if sintoma.created_at else None
                }
                for sintoma in sintomas
            ]
        except Exception as e:
            return [{"error": f"Erro ao buscar sintomas: {str(e)}"}]

    def listar_pacientes_profissional(self, limit: int = 50) -> List[Dict]:
        """Lista pacientes atribuídos ou compartilhados com o profissional"""
        query = Paciente.query
        if self.profissional_id:
            query = query.filter(
                or_(
                    Paciente.profissional_responsavel_id == self.profissional_id,
                    Paciente.compartilhamentos.any(
                        CompartilhamentoPaciente.profissional_id == self.profissional_id,
                        CompartilhamentoPaciente.ativo == True
                    )
                )
            )

        pacientes = query.order_by(Paciente.nome.asc()).limit(limit).all()
        result = []
        for paciente in pacientes:
            result.append({
                "id": paciente.id,
                "nome": paciente.nome,
                "condicao_medica": paciente.condicao_medica,
                "profissional_responsavel": paciente.profissional_responsavel_id,
                "email": paciente.email
            })
        return result
    
    def execute_query(self, query: str) -> Any:
        """Executa uma query SQL direta"""
        try:
            result = db.session.execute(query)
            if result.returns_rows:
                return [dict(row) for row in result]
            else:
                return {"rows_affected": result.rowcount}
        except Exception as e:
            return {"error": f"Erro ao executar query: {str(e)}"}

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
