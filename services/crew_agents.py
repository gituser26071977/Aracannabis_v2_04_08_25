"""
Sistema multi-agente para AraOS usando CrewAI

Agentes implementados:
1. Agente Conversacional: Interface com usuário via chat e WhatsApp
2. Especialista em Prontuários: Organização e sistematização de informações médicas
3. Biomédico: Análise de exames complementares e clínicos
4. Especialista em Relatórios: Elaboração de relatórios ilustrados
5. Farmacêutico Cannabis: Especialista em cannabis medicinal e extração
6. Supervisor: Coordenação e supervisão de todos os agentes
"""

import os
import json
import logging
import contextvars
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)

# Tentativa de importação do CrewAI moderno (1.7.x) com fallback detalhado
CREWAI_AVAILABLE = False
CREW_IMPORT_ERROR: Optional[str] = None

try:
    import crewai  # type: ignore
    # Nas versões recentes, o decorator fica em crewai.tools
    from crewai import tools as crew_tools  # type: ignore
    tool = getattr(crew_tools, "tool", None)
    if tool is None:
        raise ImportError("decorator tool não encontrado em crewai.tools")

    # As versões mais novas do crewai ainda expõem essas classes no pacote raiz,
    # mas vamos ser defensivos e usar getattr.
    Agent = getattr(crewai, "Agent", None)
    Task = getattr(crewai, "Task", None)
    Crew = getattr(crewai, "Crew", None)
    Process = getattr(crewai, "Process", None)

    if all([Agent, Task, Crew, Process]):
        CREWAI_AVAILABLE = True
        logger.info("CrewAI detectado e classes Agent/Task/Crew/Process disponíveis")
    else:
        CREW_IMPORT_ERROR = (
            "Classes Agent/Task/Crew/Process não encontradas no módulo crewai. "
            "Verifique a versão da biblioteca e a compatibilidade da API."
        )
        logger.warning(f"CrewAI instalado mas API mudou: {CREW_IMPORT_ERROR}")
except Exception as e:  # noqa: BLE001 - queremos logar qualquer erro de import
    CREWAI_AVAILABLE = False
    CREW_IMPORT_ERROR = str(e)
    logger.warning(
        "CrewAI não disponível - usando sistema simulado. Erro de importação: %s",
        CREW_IMPORT_ERROR,
        exc_info=True,
    )

# Se não for possível usar CrewAI real, definimos classes/dummy tool para manter compatibilidade
if not CREWAI_AVAILABLE:
    # Define dummy classes for type hints and compatibility
    class Agent:  # type: ignore[no-redef]
        pass

    class Task:  # type: ignore[no-redef]
        pass

    class Crew:  # type: ignore[no-redef]
        pass

    class Process:  # type: ignore[no-redef]
        pass

    # Se o decorator tool não veio do crewai, criamos um dummy
    if "tool" not in globals():
        def tool(func):  # type: ignore[no-redef]
            return func

    logger.warning("Sistema multi-agente rodará em modo SIMULADO (sem CrewAI real)")

from .ai_agents import ai_manager
from .email_service import EmailService
from .db_tools import DatabaseTools
from .payment_service import payment_service
from .association_report_service import AssociationReportService
from models import db, Paciente, Evolucao, Dosagem, Sintoma, Prescricao, Profissional

CURRENT_PROFISSIONAL_ID = contextvars.ContextVar("current_profissional_id", default=None)

def _set_current_profissional_id(prof_id: Optional[int]):
    return CURRENT_PROFISSIONAL_ID.set(prof_id)

def _reset_current_profissional_id(token):
    if token is not None:
        CURRENT_PROFISSIONAL_ID.reset(token)

def _get_current_profissional_id() -> Optional[int]:
    return CURRENT_PROFISSIONAL_ID.get()

def _create_db_tools():
    from flask import g
    associacao_id = g.current_association.id if hasattr(g, 'current_association') and g.current_association else None
    return DatabaseTools(profissional_id=_get_current_profissional_id(), associacao_id=associacao_id)

# ========== FERRAMENTAS ==========

@tool
def buscar_paciente_por_id(paciente_id: int) -> Dict:
    """Busca informações de um paciente pelo ID"""
    try:
        db_tools = _create_db_tools()
        return db_tools.buscar_paciente(paciente_id)
    except Exception as e:
        return {"error": f"Erro ao buscar paciente: {str(e)}"}

@tool
def buscar_exames_paciente(paciente_id: int) -> List[Dict]:
    """Busca exames de um paciente"""
    try:
        db_tools = _create_db_tools()
        return db_tools.buscar_exames_paciente(paciente_id)
    except Exception as e:
        return {"error": f"Erro ao buscar exames: {str(e)}"}

@tool
def buscar_evolucoes_paciente(paciente_id: int) -> List[Dict]:
    """Busca evoluções clínicas de um paciente"""
    try:
        db_tools = _create_db_tools()
        return db_tools.buscar_evolucoes_paciente(paciente_id)
    except Exception as e:
        return {"error": f"Erro ao buscar evoluções: {str(e)}"}

@tool
def buscar_dosagens_paciente(paciente_id: int) -> List[Dict]:
    """Busca dosagens de medicamentos de um paciente"""
    try:
        db_tools = _create_db_tools()
        return db_tools.buscar_dosagens_paciente(paciente_id)
    except Exception as e:
        return {"error": f"Erro ao buscar dosagens: {str(e)}"}

@tool
def buscar_sintomas_paciente(paciente_id: int) -> List[Dict]:
    """Busca sintomas relatados por um paciente"""
    try:
        db_tools = _create_db_tools()
        return db_tools.buscar_sintomas_paciente(paciente_id)
    except Exception as e:
        return {"error": f"Erro ao buscar sintomas: {str(e)}"}

@tool
def analisar_exame_com_ia(texto_exame: str) -> Dict:
    """Analisa texto de exame usando IA para extrair informações relevantes"""
    try:
        system_prompt = """Você é um especialista biomédico. Analise o texto do exame e extraia:
        1. Parâmetros medidos e valores
        2. Resultados fora do normal (valores alterados)
        3. Interpretação clínica
        4. Recomendações possíveis
        
        Retorne um JSON estruturado."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analise este exame: {texto_exame}"}
        ]
        
        response = ai_manager.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        
        try:
            content = response['content']
            if content.startswith('```json'):
                content = content[7:-3]
            return json.loads(content)
        except:
            return {"analise_bruta": response['content']}
            
    except Exception as e:
        return {"error": f"Erro na análise de IA: {str(e)}"}

@tool
def enviar_email(destinatario: str, assunto: str, corpo_html: str, corpo_texto: str = None) -> Dict:
    """Envia email para destinatário especificado"""
    try:
        email_service = EmailService()
        sucesso = email_service.send_email(destinatario, assunto, corpo_html, corpo_texto)
        
        if sucesso:
            return {
                "status": "sucesso",
                "mensagem": f"Email enviado para {destinatario}",
                "assunto": assunto
            }
        else:
            return {
                "status": "erro",
                "mensagem": f"Falha ao enviar email para {destinatario}"
            }
    except Exception as e:
        return {"error": f"Erro ao enviar email: {str(e)}"}

@tool
def gerar_relatorio_paciente(paciente_id: int, tipo_relatorio: str = "clinico") -> Dict:
    """Gera relatório completo do paciente com formatação profissional"""
    from services.report_template import gerar_html_relatorio
    from flask import g
    import os
    import markdown
    
    # 1. Validar acesso ao paciente (multi-tenant)
    db_tools = _create_db_tools()
    paciente_obj, error = db_tools.obter_paciente_com_acesso(paciente_id)
    if error:
        return {"error": error}
        
    # 2. Obter profissional logado
    profissional_id = _get_current_profissional_id() or paciente_obj.profissional_responsavel_id
    profissional = Profissional.query.get(profissional_id)
    
    try:
        # Buscar todas as informações do paciente
        # Usando métodos internos do db_tools para garantir consistência
        exames = db_tools.buscar_exames_paciente(paciente_id)
        evolucoes = db_tools.buscar_evolucoes_paciente(paciente_id)
        dosagens = db_tools.buscar_dosagens_paciente(paciente_id)
        sintomas = db_tools.buscar_sintomas_paciente(paciente_id)
        
        # Preparar contexto para IA gerar relatório
        context = {
            "paciente": paciente_obj.to_dict(),
            "exames": exames[:5],  # Últimos 5 exames
            "evolucoes": evolucoes[:10],  # Últimas 10 evoluções
            "dosagens": dosagens[:10],  # Últimas 10 dosagens
            "sintomas": sintomas[:20],  # Últimos 20 sintomas
            "tipo_relatorio": tipo_relatorio,
            "data_geracao": datetime.now().isoformat()
        }
        
        # Usar IA para gerar relatório estruturado
        system_prompt = f"""Você é um especialista em relatórios médicos. Gere um relatório {tipo_relatorio} detalhado baseado nos dados fornecidos.
        
        Estruture o relatório com seções claras usando Markdown:
        # Resumo Clínico
        # Análise de Progresso
        # Exames Relevantes
        # Evolução e Sintomas
        # Plano Terapêutico
        # Recomendações
        
        Use linguagem técnica apropriada, seja objetivo mas completo."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Relatório para o paciente {paciente_obj.nome}: {json.dumps(context, ensure_ascii=False, default=str)}"}
        ]
        
        response = ai_manager.chat_completion(
            messages=messages,
            temperature=0.4,
            max_tokens=2500
        )
        
        conteudo_md = response['content']
        
        # Converter Markdown para HTML parcial
        conteudo_html_parcial = markdown.markdown(conteudo_md)
        
        # Preparar dados para o template final
        relatorio_data = {
            "paciente": paciente_obj.to_dict(),
            "profissional": profissional.to_dict() if profissional else {},
            "tipo_relatorio": f"Relatório {tipo_relatorio.capitalize()}",
            "conteudo_html": conteudo_html_parcial,
            "data_geracao": datetime.now(),
            "metricas": {
                "total_exames": len(exames),
                "total_evolucoes": len(evolucoes)
            }
        }
        
        # Gerar HTML final completo
        html_completo = gerar_html_relatorio(relatorio_data)
        
        # Salvar arquivo (isolado por associação)
        associacao_id = g.current_association.id if hasattr(g, 'current_association') and g.current_association else 'default'
        uploads_dir = os.path.join('/app/uploads', 'relatorios', str(associacao_id), str(paciente_id))
        os.makedirs(uploads_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"relatorio_{tipo_relatorio}_{timestamp}.html"
        filepath = os.path.join(uploads_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_completo)
        
        return {
            "success": True,
            "relatorio": conteudo_md, # Retorna texto para o chat
            "arquivo_path": filepath,
            "paciente_id": paciente_id,
            "mensagem": f"Relatório gerado e salvo em: {filepath}"
        }
        
    except Exception as e:
        return {"error": f"Erro ao gerar relatório: {str(e)}"}

@tool
def analisar_evolucao_clinica(texto_evolucao: str) -> Dict:
    """Analisa texto de evolução clínica para extrair insights"""
    try:
        system_prompt = """Você é um médico especialista em análise de evoluções clínicas. Analise o texto e identifique:
        1. Sintomas relatados
        2. Progresso do tratamento
        3. Eventos adversos
        4. Necessidades de ajuste
        5. Observações importantes
        
        Retorne um JSON estruturado com sua análise."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analise esta evolução clínica: {texto_evolucao}"}
        ]
        
        response = ai_manager.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=1200
        )
        
        try:
            content = response['content']
            if content.startswith('```json'):
                content = content[7:-3]
            return json.loads(content)
        except:
            return {"analise_bruta": response['content']}
            
    except Exception as e:
        return {"error": f"Erro na análise de evolução: {str(e)}"}

@tool
def sugerir_ajuste_dosagem(paciente_id: int, medicamento: str, contexto_atual: str) -> Dict:
    """Sugere ajuste de dosagem baseado no histórico do paciente"""
    try:
        # Buscar histórico do paciente
        paciente = buscar_paciente_por_id(paciente_id)
        dosagens = buscar_dosagens_paciente(paciente_id)
        sintomas = buscar_sintomas_paciente(paciente_id)
        
        # Filtrar dosagens do medicamento específico
        dosagens_medicamento = [
            d for d in dosagens 
            if medicamento.lower() in d.get('medicamento', '').lower()
        ]
        
        context = {
            "paciente": paciente,
            "dosagens_medicamento": dosagens_medicamento[-5:],  # Últimas 5 dosagens
            "sintomas_recentes": sintomas[-10:],  # Últimos 10 sintomas
            "contexto_atual": contexto_atual,
            "medicamento": medicamento
        }
        
        system_prompt = """Você é um farmacêutico especialista em cannabis medicinal. Analise o histórico do paciente e sugira ajustes de dosagem considerando:
        1. Resposta ao tratamento atual
        2. Efeitos colaterais relatados
        3. Objetivos terapêuticos
        4. Melhores práticas em cannabis medicinal
        
        Forneça recomendações específicas e justificadas."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Dados para análise de dosagem: {json.dumps(context, ensure_ascii=False)}"}
        ]
        
        response = ai_manager.chat_completion(
            messages=messages,
            temperature=0.4,
            max_tokens=1500
        )
        
        return {
            "sugestao_ajuste": response['content'],
            "paciente_id": paciente_id,
            "medicamento": medicamento,
            "historico_dosagens": len(dosagens_medicamento)
        }
        
    except Exception as e:
        return {"error": f"Erro ao sugerir ajuste: {str(e)}"}


def _parse_date(value: Any, fallback: Optional[datetime] = None):
    if value is None:
        if fallback is not None:
            return fallback
        raise ValueError("Data obrigatória não foi informada.")

    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)

    try:
        return date_parser.parse(value)
    except Exception:
        raise ValueError(f"Formato de data inválido: {value}")


@tool
def criar_paciente_chat(dados: Dict[str, Any]) -> Dict:
    """Cria um paciente diretamente pelo chat"""
    required = ['nome', 'data_nascimento']
    missing = [field for field in required if not dados.get(field)]
    if missing:
        return {"error": f"Faltando campos obrigatórios: {', '.join(missing)}"}

    try:
        data_nascimento = _parse_date(dados.get('data_nascimento')).date()
    except ValueError as exc:
        return {"error": str(exc)}

    profissional_id = _get_current_profissional_id() or dados.get('profissional_responsavel_id') or dados.get('profissional_id') or 1
    
    # CRÍTICO: Obter associacao_id do contexto (multi-tenant)
    from flask import g
    associacao_id = g.current_association.id if hasattr(g, 'current_association') and g.current_association else None
    
    paciente = Paciente(
        profissional_responsavel_id=profissional_id,
        associacao_id=associacao_id,  # CRÍTICO: Isolamento multi-tenant
        nome=dados.get('nome'),
        data_nascimento=data_nascimento,
        cpf=dados.get('cpf'),
        genero=dados.get('genero'),
        telefone=dados.get('telefone'),
        email=dados.get('email'),
        endereco=dados.get('endereco'),
        diagnostico=dados.get('diagnostico') or dados.get('condicao_medica'),
        condicao_medica=dados.get('condicao_medica') or dados.get('diagnostico'),
        observacoes=dados.get('observacoes'),
        em_tratamento=bool(dados.get('em_tratamento', True)),
        composicao=dados.get('composicao'),
        dosagem=dados.get('dosagem'),
        horarios=dados.get('horarios')
    )

    try:
        db.session.add(paciente)
        db.session.commit()
        return {"success": True, "paciente": paciente.to_dict()}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Não foi possível criar o paciente: {str(e)}"}


@tool
def atualizar_paciente_chat(paciente_id: int, updates: Dict[str, Any]) -> Dict:
    """Atualiza campos de um paciente existente"""
    db_tools = _create_db_tools()
    paciente, error = db_tools.obter_paciente_com_acesso(paciente_id)
    if error:
        return {"error": error}

    campos_permitidos = {
        'nome',
        'data_nascimento',
        'cpf',
        'genero',
        'telefone',
        'email',
        'endereco',
        'diagnostico',
        'condicao_medica',
        'observacoes',
        'em_tratamento',
        'composicao',
        'dosagem',
        'horarios',
        'profissional_responsavel_id',
        'tdah_positivo',
        'depressao_positiva'
    }

    try:
        for key, value in updates.items():
            if key not in campos_permitidos:
                continue
            if key == 'data_nascimento':
                paciente.data_nascimento = _parse_date(value).date()
            else:
                setattr(paciente, key, value)

        paciente.updated_at = datetime.utcnow()
        db.session.commit()
        return {"success": True, "paciente": paciente.to_dict()}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Erro ao atualizar o paciente: {str(e)}"}


@tool
def deletar_paciente_chat(paciente_id: int, motivo: str = None) -> Dict:
    """Remove um paciente via chat"""
    db_tools = _create_db_tools()
    paciente, error = db_tools.obter_paciente_com_acesso(paciente_id)
    if error:
        return {"error": error}

    try:
        db.session.delete(paciente)
        db.session.commit()
        return {
            "success": True,
            "message": f"Paciente {paciente.nome} removido. Motivo: {motivo or 'assistente via chat'}"
        }
    except Exception as e:
        db.session.rollback()
        return {"error": f"Não foi possível excluir o paciente: {str(e)}"}


@tool
def criar_evolucao_chat(paciente_id: int, profissional_id: int, nota: str, data_evolucao: Optional[str] = None) -> Dict:
    """Registra evolução clínica no banco via chat"""
    db_tools = _create_db_tools()
    paciente, error = db_tools.obter_paciente_com_acesso(paciente_id)
    if error:
        return {"error": error}

    try:
        data_obj = _parse_date(data_evolucao or datetime.utcnow()).date()
    except ValueError as exc:
        return {"error": str(exc)}

    evolucao = Evolucao(
        paciente_id=paciente_id,
        profissional_id=profissional_id,
        nota_evolucao=nota,
        data_evolucao=data_obj
    )

    try:
        db.session.add(evolucao)
        db.session.commit()
        return {"success": True, "evolucao": evolucao.to_dict()}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Erro ao salvar evolução: {str(e)}"}


@tool
def atualizar_evolucao_chat(evolucao_id: int, updates: Dict[str, Any]) -> Dict:
    """Atualiza uma evolução existente"""
    evolucao = Evolucao.query.get(evolucao_id)
    if not evolucao:
        return {"error": f"Evolução {evolucao_id} não encontrada"}

    db_tools = _create_db_tools()
    _, error = db_tools.obter_paciente_com_acesso(evolucao.paciente_id)
    if error:
        return {"error": error}

    try:
        if 'nota_evolucao' in updates:
            evolucao.nota_evolucao = updates['nota_evolucao']
        if 'data_evolucao' in updates:
            evolucao.data_evolucao = _parse_date(updates['data_evolucao'])
        db.session.commit()
        return {"success": True, "evolucao": evolucao.to_dict()}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Erro ao atualizar evolução: {str(e)}"}


@tool
def deletar_evolucao_chat(evolucao_id: int) -> Dict:
    """Remove uma evolução"""
    evolucao = Evolucao.query.get(evolucao_id)
    if not evolucao:
        return {"error": f"Evolução {evolucao_id} não encontrada"}

    try:
        db_tools = _create_db_tools()
        _, error = db_tools.obter_paciente_com_acesso(evolucao.paciente_id)
        if error:
            return {"error": error}

        db.session.delete(evolucao)
        db.session.commit()
        return {"success": True, "message": f"Evolução {evolucao_id} removida"}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Erro ao excluir evolução: {str(e)}"}


@tool
def criar_dosagem_chat(
    paciente_id: int,
    data: str,
    dosagem: str,
    gotas: Optional[int] = None,
    frequencia_diaria: Optional[int] = None,
    concentracao_cbd: Optional[float] = None,
    concentracao_thc: Optional[float] = None,
    concentracao_cbg: Optional[float] = None,
    concentracao_cbn: Optional[float] = None,
    gotas_por_ml: Optional[int] = None
) -> Dict:
    """Insere uma nova dosagem"""
    db_tools = _create_db_tools()
    paciente, error = db_tools.obter_paciente_com_acesso(paciente_id)
    if error:
        return {"error": error}

    try:
        data_obj = _parse_date(data).date()
    except ValueError as exc:
        return {"error": str(exc)}

    dosagem_obj = Dosagem(
        paciente_id=paciente_id,
        data=data_obj,
        dosagem=dosagem,
        gotas=int(gotas) if gotas is not None else None,
        frequencia_diaria=int(frequencia_diaria) if frequencia_diaria is not None else None,
        concentracao_cbd=float(concentracao_cbd) if concentracao_cbd is not None else None,
        concentracao_thc=float(concentracao_thc) if concentracao_thc is not None else None,
        concentracao_cbg=float(concentracao_cbg) if concentracao_cbg is not None else None,
        concentracao_cbn=float(concentracao_cbn) if concentracao_cbn is not None else None,
        gotas_por_ml=int(gotas_por_ml) if gotas_por_ml is not None else 30
    )

    try:
        db.session.add(dosagem_obj)
        db.session.commit()
        return {"success": True, "dosagem": dosagem_obj.to_dict()}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Erro ao criar dosagem: {str(e)}"}


@tool
def atualizar_dosagem_chat(dosagem_id: int, updates: Dict[str, Any]) -> Dict:
    """Atualiza os dados de dosagem"""
    dosagem = Dosagem.query.get(dosagem_id)
    if not dosagem:
        return {"error": f"Dosagem {dosagem_id} não encontrada"}

    try:
        db_tools = _create_db_tools()
        _, error = db_tools.obter_paciente_com_acesso(dosagem.paciente_id)
        if error:
            return {"error": error}

        if 'data' in updates:
            dosagem.data = _parse_date(updates['data']).date()
        for key in [
            'dosagem',
            'gotas',
            'frequencia_diaria',
            'concentracao_cbd',
            'concentracao_thc',
            'concentracao_cbg',
            'concentracao_cbn',
            'gotas_por_ml'
        ]:
            if key in updates:
                setattr(dosagem, key, updates[key])
        db.session.commit()
        return {"success": True, "dosagem": dosagem.to_dict()}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Erro ao atualizar dosagem: {str(e)}"}


@tool
def deletar_dosagem_chat(dosagem_id: int) -> Dict:
    """Exclui uma dosagem"""
    dosagem = Dosagem.query.get(dosagem_id)
    if not dosagem:
        return {"error": f"Dosagem {dosagem_id} não encontrada"}

    try:
        db_tools = _create_db_tools()
        _, error = db_tools.obter_paciente_com_acesso(dosagem.paciente_id)
        if error:
            return {"error": error}

        db.session.delete(dosagem)
        db.session.commit()
        return {"success": True, "message": f"Dosagem {dosagem_id} excluída"}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Erro ao excluir dosagem: {str(e)}"}


@tool
def gerar_prescricao_chat(
    paciente_id: int,
    medicamentos: List[Dict[str, Any]],
    observacoes: Optional[str] = None
) -> Dict:
    """
    Gera prescrição médica via chat
    
    Args:
        paciente_id: ID do paciente
        medicamentos: Lista de dicts com:
            - nome: str (nome do medicamento)
            - composicao: str (ex: "Canabidiol 200mg/ml")
            - posologia: str (ex: "3 gotas, 2x ao dia")
            - quantidade: str opcional (ex: "30ml")
        observacoes: str opcional
    
    Returns:
        Dict com {success, prescricao, arquivo_path} ou {error}
    """
    from services.prescription_template import gerar_html_prescricao
    from flask import g
    import os
    
    # 1. Validar acesso ao paciente (multi-tenant)
    db_tools = _create_db_tools()
    paciente, error = db_tools.obter_paciente_com_acesso(paciente_id)
    if error:
        return {"error": error}
    
    # 2. Obter profissional logado
    profissional_id = _get_current_profissional_id()
    if not profissional_id:
        return {"error": "Profissional não identificado"}
    
    profissional = Profissional.query.get(profissional_id)
    if not profissional:
        return {"error": "Profissional não encontrado"}
    
    # 3. Validar medicamentos
    if not medicamentos or len(medicamentos) == 0:
        return {"error": "Prescrição deve conter pelo menos 1 medicamento"}
    
    # 4. Preparar dados para template
    data_emissao = datetime.utcnow()
    
    prescricao_data = {
        "paciente": {
            "nome": paciente.nome,
            "data_nascimento": paciente.data_nascimento.strftime('%d/%m/%Y') if paciente.data_nascimento else '',
            "cpf": paciente.cpf or '',
            "telefone": paciente.telefone or '',
            "diagnostico": paciente.diagnostico or ''
        },
        "profissional": {
            "nome": profissional.nome,
            "crm": profissional.crm,
            "uf_crm": profissional.uf_crm,
            "email": profissional.email or ''
        },
        "medicamentos": medicamentos,
        "observacoes": observacoes or '',
        "data_emissao": data_emissao
    }
    
    # 5. Gerar HTML
    try:
        html_content = gerar_html_prescricao(prescricao_data)
    except Exception as e:
        return {"error": f"Erro ao gerar HTML: {str(e)}"}
    
    # 6. Criar diretório de prescrições (isolado por associação - multi-tenant)
    associacao_id = g.current_association.id if hasattr(g, 'current_association') and g.current_association else 'default'
    uploads_dir = os.path.join('/app/uploads', 'prescricoes', str(associacao_id), str(paciente_id))
    os.makedirs(uploads_dir, exist_ok=True)
    
    # 7. Salvar HTML
    timestamp = data_emissao.strftime('%Y%m%d_%H%M%S')
    filename = f"prescricao_{timestamp}.html"
    filepath = os.path.join(uploads_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
        return{"error": f"Erro ao salvar arquivo: {str(e)}"}
    
    # 8. Salvar registro no banco
    prescricao = Prescricao(
        paciente_id=paciente_id,
        profissional_id=profissional_id,
        data_emissao=data_emissao,
        arquivo_path=filepath,
        conteudo_json={"medicamentos": medicamentos},
        observacoes=observacoes
    )
    
    try:
        db.session.add(prescricao)
        db.session.commit()
        
        return {
            "success": True,
            "prescricao": prescricao.to_dict(),
            "arquivo_path": filepath,
            "message": "Prescrição gerada com sucesso!"
        }
    except Exception as e:
        db.session.rollback()
        try:
            os.remove(filepath)
        except:
            pass
        return {"error": f"Erro ao salvar prescrição: {str(e)}"}


@tool
def criar_sintoma_chat(paciente_id: int, data: str, sintoma: str, intensidade: int) -> Dict:
    """Registra um sintoma reportado"""
    db_tools = _create_db_tools()
    paciente, error = db_tools.obter_paciente_com_acesso(paciente_id)
    if error:
        return {"error": error}

    try:
        data_obj = _parse_date(data).date()
    except ValueError as exc:
        return {"error": str(exc)}

    intensidade = int(intensidade)
    if intensidade < 0 or intensidade > 10:
        return {"error": "Intensidade precisa ser entre 0 e 10"}

    sintoma_obj = Sintoma(
        paciente_id=paciente_id,
        data=data_obj,
        sintoma=sintoma,
        intensidade=intensidade
    )

    try:
        db.session.add(sintoma_obj)
        db.session.commit()
        return {"success": True, "sintoma": sintoma_obj.to_dict()}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Erro ao criar sintoma: {str(e)}"}


@tool
def atualizar_sintoma_chat(sintoma_id: int, updates: Dict[str, Any]) -> Dict:
    """Atualiza um sintoma existente"""
    sintoma = Sintoma.query.get(sintoma_id)
    if not sintoma:
        return {"error": f"Sintoma {sintoma_id} não encontrado"}

    try:
        db_tools = _create_db_tools()
        _, error = db_tools.obter_paciente_com_acesso(sintoma.paciente_id)
        if error:
            return {"error": error}

        if 'data' in updates:
            sintoma.data = _parse_date(updates['data']).date()
        if 'sintoma' in updates:
            sintoma.sintoma = updates['sintoma']
        if 'intensidade' in updates:
            intensidade = int(updates['intensidade'])
            if intensidade < 0 or intensidade > 10:
                raise ValueError("Intensidade tem que ser entre 0 e 10")
            sintoma.intensidade = intensidade
        db.session.commit()
        return {"success": True, "sintoma": sintoma.to_dict()}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Erro ao atualizar sintoma: {str(e)}"}


@tool
def deletar_sintoma_chat(sintoma_id: int) -> Dict:
    """Remove um sintoma reportado"""
    sintoma = Sintoma.query.get(sintoma_id)
    if not sintoma:
        return {"error": f"Sintoma {sintoma_id} não encontrado"}

    try:
        db_tools = _create_db_tools()
        _, error = db_tools.obter_paciente_com_acesso(sintoma.paciente_id)
        if error:
            return {"error": error}

        db.session.delete(sintoma)
        db.session.commit()
        return {"success": True, "message": f"Sintoma {sintoma_id} removido"}
    except Exception as e:
        db.session.rollback()
        return {"error": f"Erro ao deletar sintoma: {str(e)}"}


PACIENTE_CRUD_TOOLS = [
    criar_paciente_chat,
    atualizar_paciente_chat,
    deletar_paciente_chat
]

EVOLUCAO_CRUD_TOOLS = [
    criar_evolucao_chat,
    atualizar_evolucao_chat,
    deletar_evolucao_chat
]

DOSAGEM_CRUD_TOOLS = [
    criar_dosagem_chat,
    atualizar_dosagem_chat,
    deletar_dosagem_chat
]

SINTOMA_CRUD_TOOLS = [
    criar_sintoma_chat,
    atualizar_sintoma_chat,
    deletar_sintoma_chat
]

PRESCRICAO_TOOLS = [
    gerar_prescricao_chat
]

# ========== FERRAMENTAS DE RELATÓRIOS DE ASSOCIAÇÃO ==========

@tool
def obter_overview_associacao(associacao_id: int) -> Dict:
    """Obtém visão geral completa de uma associação com estatísticas"""
    try:
        return AssociationReportService.get_association_overview(associacao_id)
    except Exception as e:
        return {"error": f"Erro ao obter overview: {str(e)}"}

@tool
def gerar_relatorio_atividade_membros(associacao_id: int, membro_id: Optional[int] = None) -> Dict:
    """Gera relatório de atividade de membros de uma associação"""
    try:
        return AssociationReportService.get_member_activity_report(associacao_id, membro_id)
    except Exception as e:
        return {"error": f"Erro ao gerar relatório: {str(e)}"}

@tool
def analisar_dispensacoes_associacao(associacao_id: int, dias: int = 30) -> Dict:
    """Analisa dispensações da associação com estatísticas e gráficos"""
    try:
        return AssociationReportService.get_dispensation_analytics(associacao_id, dias)
    except Exception as e:
        return {"error": f"Erro ao analisar dispensações: {str(e)}"}

@tool
def REDACTED(associacao_id: int) -> Dict:
    """Consulta status atual do estoque da associação com alertas"""
    try:
        return AssociationReportService.get_stock_status(associacao_id)
    except Exception as e:
        return {"error": f"Erro ao consultar estoque: {str(e)}"}

@tool
def REDACTED(associacao_id: int, periodo_dias: int = 30) -> Dict:
    """Gera relatório completo consolidado da associação usando IA"""
    try:
        # Coletar todos os dados
        overview = AssociationReportService.get_association_overview(associacao_id)
        atividade = AssociationReportService.get_member_activity_report(associacao_id)
        dispensacoes = AssociationReportService.get_dispensation_analytics(associacao_id, periodo_dias)
        estoque = AssociationReportService.get_stock_status(associacao_id)
        
        # Preparar contexto para IA
        context = {
            "overview": overview,
            "atividade_membros": atividade,
            "analise_dispensacoes": dispensacoes,
            "status_estoque": estoque,
            "periodo_analise": periodo_dias
        }
        
        # Usar IA para gerar relatório estruturado
        system_prompt = """Você é um especialista em relatórios gerenciais para associações de cannabis medicinal.
        
        Gere um relatório executivo completo baseado nos dados fornecidos, estruturado com:
        
        1. **Resumo Executivo**: Principais indicadores e insights
        2. **Análise de Membros**: Atividade, engajamento e crescimento
        3. **Gestão de Dispensações**: Padrões, tendências e eficiência
        4. **Status de Estoque**: Disponibilidade, alertas e recomendações
        5. **Recomendações Estratégicas**: Ações prioritárias
        
        Use linguagem profissional, dados quantitativos e insights acionáveis.
        Formate em Markdown para fácil leitura."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Dados da associação para relatório: {json.dumps(context, ensure_ascii=False)}"}
        ]
        
        response = ai_manager.chat_completion(
            messages=messages,
            temperature=0.4,
            max_tokens=3000
        )
        
        return {
            "relatorio_ia": response['content'],
            "dados_brutos": context,
            "data_geracao": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {"error": f"Erro ao gerar relatório completo: {str(e)}"}

ASSOCIATION_REPORT_TOOLS = [
    obter_overview_associacao,
    gerar_relatorio_atividade_membros,
    analisar_dispensacoes_associacao,
    REDACTED,
    REDACTED
]

# ========== FERRAMENTAS DE VALIDAÇÃO DE PROFISSIONAIS ==========

@tool
def validar_crm_profissional(crm: str, uf: str) -> Dict:
    """Valida CRM de profissional usando API do CFM e conselhos regionais"""
    try:
        from services.crm_validator_service import CRMValidatorService
        return CRMValidatorService.validate_crm(crm, uf)
    except Exception as e:
        return {"error": f"Erro ao validar CRM: {str(e)}"}

@tool
def aprovar_cadastro_profissional(profissional_id: int, validation_data: Dict) -> Dict:
    """Aprova cadastro de profissional após validação bem-sucedida"""
    try:
        from models import Profissional
        from datetime import datetime
        
        prof = Profissional.query.get(profissional_id)
        if not prof:
            return {"error": f"Profissional {profissional_id} não encontrado"}
        
        prof.status_cadastro = 'aprovado'
        prof.data_aprovacao = datetime.utcnow()
        prof.aprovado_por = 'system'
        prof.validation_data = validation_data
        
        db.session.commit()
        
        return {
            "success": True,
            "profissional_id": profissional_id,
            "status": "aprovado",
            "message": f"Cadastro de {prof.nome} aprovado com sucesso"
        }
    except Exception as e:
        db.session.rollback()
        return {"error": f"Erro ao aprovar cadastro: {str(e)}"}

@tool
def rejeitar_cadastro_profissional(profissional_id: int, motivo: str, validation_data: Dict = None) -> Dict:
    """Rejeita cadastro de profissional com motivo específico"""
    try:
        from models import Profissional
        
        prof = Profissional.query.get(profissional_id)
        if not prof:
            return {"error": f"Profissional {profissional_id} não encontrado"}
        
        prof.status_cadastro = 'rejeitado'
        prof.motivo_rejeicao = motivo
        prof.validation_data = validation_data or {}
        
        db.session.commit()
        
        return {
            "success": True,
            "profissional_id": profissional_id,
            "status": "rejeitado",
            "motivo": motivo,
            "message": f"Cadastro de {prof.nome} rejeitado"
        }
    except Exception as e:
        db.session.rollback()
        return {"error": f"Erro ao rejeitar cadastro: {str(e)}"}

@tool
def gerar_senha_temporaria() -> Dict:
    """Gera senha temporária segura para profissional aprovado"""
    try:
        import secrets
        import string
        
        # Gera senha com 12 caracteres: letras maiúsculas, minúsculas, números e símbolos
        alphabet = string.ascii_letters + string.digits + "!@#$%&*"
        senha = ''.join(secrets.choice(alphabet) for _ in range(12))
        
        # Garante pelo menos 1 maiúscula, 1 minúscula, 1 número e 1 símbolo
        if (any(c.islower() for c in senha) and 
            any(c.isupper() for c in senha) and
            any(c.isdigit() for c in senha) and
            any(c in "!@#$%&*" for c in senha)):
            return {
                "success": True,
                "senha_temporaria": senha
            }
        else:
            # Recursão se não atender critérios
            return gerar_senha_temporaria()
    except Exception as e:
        return {"error": f"Erro ao gerar senha: {str(e)}"}

@tool
def REDACTED(profissional_id: int, senha_temporaria: str) -> Dict:
    """Envia email de aprovação com credenciais de acesso"""
    try:
        from models import Profissional
        
        prof = Profissional.query.get(profissional_id)
        if not prof or not prof.email:
            return {"error": "Profissional não encontrado ou sem email"}
        
        subject = "Cadastro Aprovado - AraOS"
        
        html_body = f"""
        <h2>Olá Dr(a). {prof.nome},</h2>
        
        <p>Seu cadastro foi <strong>aprovado</strong> com sucesso!</p>
        
        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>Credenciais de Acesso:</h3>
            <p><strong>Usuário:</strong> {prof.usuario}</p>
            <p><strong>Senha Temporária:</strong> <code style="background: #fff; padding: 5px 10px; border-radius: 4px;">{senha_temporaria}</code></p>
        </div>
        
        <p><strong>⚠️ IMPORTANTE:</strong> Esta é uma senha temporária. Você será solicitado a alterá-la no primeiro acesso.</p>
        
        <p><a href="http://localhost:3000/login" style="background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 20px 0;">Acessar Sistema</a></p>
        
        <p>Em caso de dúvidas, entre em contato conosco</p>
        
        <hr style="margin: 30px 0;">
        <p style="color: #666; font-size: 12px;">Este email foi gerado automaticamente pelo sistema AraOS.</p>
        """
        
        return enviar_email(
            destinatario=prof.email,
            assunto=subject,
            corpo_html=html_body,
            corpo_texto=f"Cadastro aprovado! Usuário: {prof.usuario}, Senha: {senha_temporaria}"
        )
    except Exception as e:
        return {"error": f"Erro ao enviar email de aprovação: {str(e)}"}

@tool
def enviar_email_rejeicao_profissional(profissional_id: int) -> Dict:
    """Envia email de rejeição com motivo"""
    try:
        from models import Profissional
        
        prof = Profissional.query.get(profissional_id)
        if not prof or not prof.email:
            return {"error": "Profissional não encontrado ou sem email"}
        
        subject = "Cadastro Não Aprovado - AraOS"
        
        html_body = f"""
        <h2>Olá {prof.nome},</h2>
        
        <p>Informamos que seu cadastro não foi aprovado.</p>
        
        <div style="background: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; margin: 20px 0;">
            <h3>Motivo:</h3>
            <p>{prof.motivo_rejeicao or 'Não especificado'}</p>
        </div>
        
        <p><strong>O que fazer:</strong></p>
        <ul>
            <li>Verifique se o CRM {prof.crm}/{prof.uf_crm} está correto</li>
            <li>Certifique-se de que o CRM está ativo e regular</li>
            <li>Entre em contato conosco para mais informações</li>
        </ul>
        
        <p>Email: contato@arapath.com.br</p>
        
        <hr style="margin: 30px 0;">
        <p style="color: #666; font-size: 12px;">Este email foi gerado automaticamente pelo sistema AraOS.</p>
        """
        
        return enviar_email(
            destinatario=prof.email,
            assunto=subject,
            corpo_html=html_body,
            corpo_texto=f"Cadastro não aprovado. Motivo: {prof.motivo_rejeicao}"
        )
    except Exception as e:
        return {"error": f"Erro ao enviar email de rejeição: {str(e)}"}

PROFESSIONAL_VALIDATION_TOOLS = [
    validar_crm_profissional,
    aprovar_cadastro_profissional,
    rejeitar_cadastro_profissional,
    gerar_senha_temporaria,
    REDACTED,
    enviar_email_rejeicao_profissional
]

ALL_CRUD_TOOLS = PACIENTE_CRUD_TOOLS + EVOLUCAO_CRUD_TOOLS + DOSAGEM_CRUD_TOOLS + SINTOMA_CRUD_TOOLS + PRESCRICAO_TOOLS


# ========== AGENTES ==========

def criar_agente_conversacional(llm_config: Optional[Dict] = None) -> Agent:
    """Cria agente conversacional para interface com usuário"""
    if not CREWAI_AVAILABLE:
        return None
    
    agent = Agent(
        role="Agente Conversacional",
        goal="""Interagir com usuários através de chat e WhatsApp de forma natural e útil.
        Compreender as necessidades do usuário e direcionar para os agentes especializados apropriados.
        Manter conversas envolventes e produtivas.""",
        backstory="""Você é um assistente virtual especializado em saúde, com anos de experiência 
        em comunicação médica. Sabe como explicar conceitos complexos de forma simples e 
        empatizar com pacientes e profissionais. Domina português brasileiro e jargão médico apropriado.""",
        verbose=True,
        allow_delegation=True,
        tools=[
            buscar_paciente_por_id,
            buscar_exames_paciente,
            buscar_evolucoes_paciente,
            *ALL_CRUD_TOOLS
        ],
        llm_config=llm_config
    )
    
    return agent

def criar_especialista_prontuarios(llm_config: Optional[Dict] = None) -> Agent:
    """Cria agente especialista em organização de prontuários"""
    if not CREWAI_AVAILABLE:
        return None
    
    agent = Agent(
        role="Especialista em Prontuários Médicos",
        goal="""Organizar, sistematizar e estruturar informações médicas em prontuários.
        Garantir que todas as informações estejam bem documentadas, categorizadas e facilmente acessíveis.
        Identificar gaps no registro de informações.""",
        backstory="""Você tem décadas de experiência em administração médica e organização de prontuários.
        Trabalhou em grandes hospitais e clínicas, implementando sistemas de documentação que são referência.
        Sua atenção aos detalhes e paixão por organização são lendárias no meio médico.""",
        verbose=True,
        allow_delegation=False,
        tools=[
            buscar_paciente_por_id,
            buscar_evolucoes_paciente,
            buscar_exames_paciente,
            buscar_dosagens_paciente,
            buscar_sintomas_paciente,
            analisar_evolucao_clinica,
            *PACIENTE_CRUD_TOOLS,
            *EVOLUCAO_CRUD_TOOLS
        ],
        llm_config=llm_config
    )
    
    return agent

def criar_biomedico(llm_config: Optional[Dict] = None) -> Agent:
    """Cria agente biomédico especialista em exames"""
    if not CREWAI_AVAILABLE:
        return None
    
    agent = Agent(
        role="Biomédico Especialista em Exames Complementares",
        goal="""Analisar e interpretar exames de análises clínicas e complementares.
        Identificar alterações relevantes, correlacionar resultados e sugerir investigações adicionais.
        Explicar resultados de exames de forma clínica.""",
        backstory="""Você é um biomédico com especialização em análises clínicas e patologia.
        Trabalhou por anos em laboratórios de referência, analisando milhares de exames.
        Tem experiência em hematologia, bioquímica, imunologia e microbiologia.
        Sabe relacionar resultados de exames com condições clínicas.""",
        verbose=True,
        allow_delegation=False,
        tools=[
            buscar_exames_paciente,
            analisar_exame_com_ia,
            buscar_paciente_por_id,
            buscar_evolucoes_paciente,
            *EVOLUCAO_CRUD_TOOLS
        ],
        llm_config=llm_config
    )
    
    return agent

def criar_especialista_relatorios(llm_config: Optional[Dict] = None) -> Agent:
    """Cria agente especialista em elaboração de relatórios"""
    if not CREWAI_AVAILABLE:
        return None
    
    agent = Agent(
        role="Especialista em Relatórios Médicos",
        goal="""Elaborar relatórios médicos completos, bem estruturados e ilustrados.
        Transformar dados clínicos em narrativas coerentes e informativas.
        Criar visualizações e resumos que facilitem a tomada de decisão.""",
        backstory="""Você é um redator médico premiado, com formação em medicina e jornalismo científico.
        Escreveu centenas de relatórios para hospitais, pesquisas clínicas e publicações médicas.
        Tem talento especial para transformar dados complexos em narrativas claras e persuasivas.
        Seus relatórios são conhecidos por sua clareza e utilidade prática.""",
        verbose=True,
        allow_delegation=False,
        tools=[
            gerar_relatorio_paciente,
            buscar_paciente_por_id,
            buscar_exames_paciente,
            buscar_evolucoes_paciente,
            enviar_email,
            *PACIENTE_CRUD_TOOLS
        ],
        llm_config=llm_config
    )
    
    return agent

def criar_farmaceutico_cannabis(llm_config: Optional[Dict] = None) -> Agent:
    """Cria agente farmacêutico especialista em cannabis medicinal"""
    if not CREWAI_AVAILABLE:
        return None
    
    agent = Agent(
        role="Farmacêutico Especialista em Cannabis Medicinal",
        goal="""Orientar sobre uso terapêutico de cannabis, dosagens, interações e processos de extração.
        Sugerir protocolos personalizados baseados em evidências científicas.
        Acompanhar eficácia e segurança do tratamento com cannabis.""",
        backstory="""Você é farmacêutico com pós-graduação em fitoterapia e especialização em cannabis medicinal.
        Trabalhou em clínicas especializadas e participou de pesquisas clínicas com cannabis.
        Domina química dos canabinoides, farmacocinética e técnicas de extração.
        Tem experiência prática com centenas de pacientes tratados com cannabis.""",
        verbose=True,
        allow_delegation=False,
        tools=[
            buscar_dosagens_paciente,
            buscar_sintomas_paciente,
            sugerir_ajuste_dosagem,
            buscar_paciente_por_id,
            buscar_evolucoes_paciente,
            *DOSAGEM_CRUD_TOOLS,
            *SINTOMA_CRUD_TOOLS,
            *PRESCRICAO_TOOLS
        ],
        llm_config=llm_config
    )
    
    return agent

def criar_especialista_associacoes(llm_config: Optional[Dict] = None) -> Agent:
    """Cria agente especialista em relatórios e gestão de associações"""
    if not CREWAI_AVAILABLE:
        return None
    
    agent = Agent(
        role="Especialista em Gestão de Associações de Cannabis Medicinal",
        goal="""Gerar relatórios executivos e análises estratégicas para associações de cannabis medicinal.
        Analisar dados de membros, dispensações e estoque para fornecer insights acionáveis.
        Identificar padrões, tendências e oportunidades de melhoria na gestão da associação.
        Criar visualizações de dados e dashboards informativos.""",
        backstory="""Você é um consultor especializado em gestão de associações sem fins lucrativos no setor de cannabis medicinal.
        Possui mestrado em Administração com foco em gestão de associações de saúde.
        Trabalhou como analista de dados e gestor em várias associações de cannabis medicinal,
        implementando sistemas de BI, dashboards e relatórios que melhoraram significativamente a eficiência operacional.
        É expert em análise de dados, KPIs, indicadores de performance e visualização de informações.
        Combina conhecimento técnico em análise de dados com profundo entendimento das necessidades
        específicas de associações de pacientes. Suas recomendações são sempre baseadas em dados
        e focadas em melhorar o atendimento aos membros da associação.""",
        verbose=True,
        allow_delegation=False,
        tools=[
            *ASSOCIATION_REPORT_TOOLS,
            enviar_email  # Pode enviar relatórios por email
        ],
        llm_config=llm_config
    )
    
    return agent

def criar_validador_profissionais(llm_config: Optional[Dict] = None) -> Agent:
    """Cria agente validador de cadastro de profissionais de saúde"""
    if not CREWAI_AVAILABLE:
        return None
    
    agent = Agent(
        role="Validador de Cadastros de Profissionais de Saúde",
        goal="""Validar automaticamente cadastros de profissionais de saúde verificando autenticidade do CRM,
        aprovando ou rejeitando cadastros baseado em dados oficiais, e enviando notificações apropriadas.
        Detectar possíveis fraudes e garantir que apenas profissionais legítimos tenham acesso ao sistema.""",
        backstory="""Você é um especialista em regulamentação médica brasileira com profundo conhecimento sobre:
        - Conselhos Regionais de Medicina (CRMs) e Conselho Federal de Medicina (CFM)
        - Processos de registro e validação de profissionais de saúde
        - Detecção de fraudes em credenciais médicas
        - Legislação sobre exercício profissional da medicina no Brasil
        
        Trabalhou por anos no departamento de registro do CFM, realizando validações de credenciais
        e identificando tentativas de fraude. Possui expertise em consultar sistemas oficiais e
        interpretar dados de validação. Sua análise é meticulosa e baseada em evidências concretas.
        
        Você segue um protocolo rigoroso:
        1. Validar CRM em múltiplas fontes (CFM, Regional)
        2. Analisar dados retornados (situação ativa, especialidades, etc)
        3. Decidir: aprovar (CRM válido), rejeitar (CRM inválido), ou revisar manualmente (dados inconclusivos)
        4. Gerar senha temporária segura para aprovados
        5. Enviar emails informativos (aprovação com credenciais ou rejeição com motivo)
        6. Documentar todo o processo de validação
        
        Sua prioridade é a segurança: em caso de dúvida, sempre optar por revisão manual.""",
        verbose=True,
        allow_delegation=False,
        tools=[
            *PROFESSIONAL_VALIDATION_TOOLS
        ],
        llm_config=llm_config
    )
    
    return agent

def criar_supervisor(llm_config: Optional[Dict] = None) -> Agent:
    """Cria agente supervisor para coordenar outros agentes"""
    if not CREWAI_AVAILABLE:
        return None
    
    agent = Agent(
        role="Supervisor de Equipe Médica",
        goal="""Coordenar e supervisionar o trabalho de todos os agentes especializados.
        Garantir que as tarefas sejam executadas corretamente e no tempo adequado.
        Resolver conflitos e otimizar a colaboração entre agentes.
        Assegurar que nada saia do planejamento.""",
        backstory="""Você é um gestor médico experiente, com décadas liderando equipes multidisciplinares.
        Trabalhou como diretor clínico em grandes hospitais, coordenando médicos, enfermeiros e terapeutas.
        É conhecido por sua capacidade de organizar fluxos de trabalho complexos e garantir qualidade.
        Sua supervisão é meticulosa e respeitada por todos os profissionais.""",
        verbose=True,
        allow_delegation=True,
        tools=[],  # Supervisor não usa ferramentas diretas, delega
        llm_config=llm_config
    )
    
    return agent

# ========== CREW COMPLETA ==========

def criar_crew_araos(llm_config: Optional[Dict] = None) -> Crew:
    """Cria a crew completa do AraOS com todos os agentes"""
    if not CREWAI_AVAILABLE:
        return None
    
    # Criar todos os agentes
    agente_conversacional = criar_agente_conversacional(llm_config)
    especialista_prontuarios = criar_especialista_prontuarios(llm_config)
    biomedico = criar_biomedico(llm_config)
    especialista_relatorios = criar_especialista_relatorios(llm_config)
    farmaceutico_cannabis = criar_farmaceutico_cannabis(llm_config)
    supervisor = criar_supervisor(llm_config)
    
    # Definir tarefas principais
    tarefa_recepcao = Task(
        description="""Receber solicitação do usuário, entender suas necessidades e direcionar para o agente apropriado.
        Manter conversa natural e acolhedora.""",
        agent=agente_conversacional,
        expected_output="""Análise da solicitação do usuário e direcionamento para agente especializado."""
    )
    
    tarefa_organizacao = Task(
        description="""Organizar e sistematizar informações médicas do paciente.
        Identificar gaps na documentação e sugerir melhorias.""",
        agent=especialista_prontuarios,
        expected_output="""Prontuário organizado com todas as informações categorizadas e acessíveis."""
    )
    
    tarefa_analise_exames = Task(
        description="""Analisar exames do paciente, identificar alterações relevantes e correlacionar com quadro clínico.""",
        agent=biomedico,
        expected_output="""Relatório de análise de exames com interpretação clínica."""
    )
    
    tarefa_relatorio = Task(
        description="""Elaborar relatório completo do paciente com base em todos os dados disponíveis.""",
        agent=especialista_relatorios,
        expected_output="""Relatório médico completo e bem estruturado."""
    )
    
    tarefa_ajuste_tratamento = Task(
        description="""Analisar tratamento atual e sugerir ajustes baseados em evidências.""",
        agent=farmaceutico_cannabis,
        expected_output="""Recomendações de ajuste de tratamento com justificativa científica."""
    )

    # Novo Agente Follow-Up
    acompanhante_terapeutico = AgentFollowUp(llm_config).agent()

    tarefa_followup = Task(
        description="""Realizar follow-up clínico automatizado com pacientes.
        Analisar evolução, adesão e resposta ao tratamento.
        Gerar perguntas personalizadas e registrar evoluções estruturadas no prontuário.""",
        agent=acompanhante_terapeutico,
        expected_output="""Relatório de acompanhamento com evolução clínica registrada e sugestões de conduta."""
    )
    
    tarefa_supervisao = Task(
        description="""Coordenar todas as tarefas, garantir qualidade e cumprimento de prazos.""",
        agent=supervisor,
        expected_output="""Relatório de supervisão com status de todas as tarefas."""
    )
    
    # Criar crew
    crew = Crew(
        agents=[
            agente_conversacional,
            especialista_prontuarios,
            biomedico,
            especialista_relatorios,
            farmaceutico_cannabis,
            acompanhante_terapeutico
        ],
        tasks=[
            tarefa_recepcao,
            tarefa_organizacao,
            tarefa_analise_exames,
            tarefa_relatorio,
            tarefa_ajuste_tratamento,
            tarefa_followup,
            tarefa_supervisao
        ],
        process=Process.hierarchical,
        manager_agent=supervisor,
        verbose=True,
        memory=True
    )
    
    return crew

# ========== INTERFACE SIMPLIFICADA ==========

class SistemaMultiAgente:
    """Interface simplificada para o sistema multi-agente"""

    def __init__(self):
        self.crew = None
        self.crew_simulada = not CREWAI_AVAILABLE
        # Evita erros de permissão ao inicializar storage da CrewAI
        os.environ.setdefault("CREWAI_STORAGE_PATH", "/tmp/crewai_storage")
        try:
            os.makedirs(os.environ["CREWAI_STORAGE_PATH"], exist_ok=True)
        except Exception:
            logger.warning("Não foi possível criar pasta de storage da CrewAI, seguindo sem memória persistente.")

        if CREWAI_AVAILABLE:
            try:
                provider = os.getenv('DEFAULT_LLM_PROVIDER', 'groq')
                if provider in ("ollama_local", "ollama_cloud"):
                    provider = "ollama"
                llm_config = {
                    "provider": provider,
                    "model": os.getenv('DEFAULT_LLM_MODEL', 'llama-3.3-70b-versatile'),
                    "temperature": 0.7
                }
                self.crew = criar_crew_araos(llm_config)
                logger.info("Crew de agentes criada com sucesso")
            except Exception as e:
                logger.error(f"Erro ao criar crew: {str(e)}")
                self.crew_simulada = True
        else:
            logger.warning("Usando sistema multi-agente simulado")

    def processar_solicitacao(
        self,
        solicitacao: str,
        paciente_id: Optional[int] = None,
        contexto: Optional[Dict] = None,
        profissional_id: Optional[int] = None
    ) -> Dict:
        """Processa solicitação do usuário usando sistema multi-agente"""
        contexto = contexto or {}
        profissional_id = profissional_id or contexto.get("profissional_id")
        token = _set_current_profissional_id(profissional_id)
        if profissional_id and "profissional_id" not in contexto:
            contexto["profissional_id"] = profissional_id

        try:
            if self.crew_simulada or not self.crew:
                return self._processar_simulado(solicitacao, paciente_id, contexto)

            inputs = {
                "solicitacao": solicitacao,
                "paciente_id": paciente_id,
                "contexto": contexto
            }
            resultado = self.crew.kickoff(inputs=inputs)
            return {
                "resultado": str(resultado),
                "modo": "real",
                "agentes_envolvidos": 6,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erro ao executar crew: {str(e)}")
            return self._processar_simulado(solicitacao, paciente_id, contexto)
        finally:
            _reset_current_profissional_id(token)

    def _processar_simulado(self, solicitacao: str, paciente_id: Optional[int] = None, contexto: Optional[Dict] = None) -> Dict:
        """Processamento simulado quando CrewAI não está disponível"""
        context = contexto or {}
        if paciente_id:
            try:
                db_tools = DatabaseTools(profissional_id=_get_current_profissional_id())
                paciente = db_tools.buscar_paciente(paciente_id)
                if paciente and not paciente.get("error"):
                    context["paciente"] = paciente
            except Exception:
                pass

        system_prompt = """Você é um sistema multi-agente simulado composto por 6 especialistas:
        1. Agente Conversacional: Interface com usuário
        2. Especialista em Prontuários: Organização de informações
        3. Biomédico: Análise de exames
        4. Especialista em Relatórios: Elaboração de relatórios
        5. Farmacêutico Cannabis: Tratamento com cannabis
        6. Supervisor: Coordenação da equipe
        7. Acompanhante Terapêutico: Follow-up clínico automatizado

        Use somente os agentes relevantes para a demanda; se não pedirem relatório, não envolva o agente de relatórios.
        Se a solicitação for criação de paciente, crie e retorne JSON mínimo: nome, condicao_medica, tratamento (se houver)."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Solicitação: {solicitacao}\n\nContexto: {json.dumps(context, ensure_ascii=False)}"}
        ]

        response = ai_manager.chat_completion(
            messages=messages,
            temperature=0.6,
            max_tokens=2000
        )
        resultado_texto = response['content']

        created = _tentar_criar_paciente(solicitacao, context)
        if created.get("created"):
            extra = f"\n\n[Paciente criado: {created['paciente']['nome']} (id {created['paciente']['id']})]"
            resultado_texto = f"{resultado_texto}{extra}"

        return {
            "resultado": resultado_texto,
            "modo": "simulado",
            "agentes_envolvidos": 6,
            "timestamp": datetime.now().isoformat(),
            "provider": response.get('provider', 'unknown'),
            "model": response.get('model', 'unknown'),
            "paciente_criado": created if created.get("created") else None
        }

    def gerar_relatorio(self, paciente_id: int, tipo_relatorio: str = "clinico") -> Dict:
        """Gera relatório completo usando sistema multi-agente"""
        return gerar_relatorio_paciente(paciente_id, tipo_relatorio)

    def analisar_exame(self, texto_exame: str) -> Dict:
        """Analisa exame usando agente biomédico"""
        return analisar_exame_com_ia(texto_exame)

    def sugerir_ajuste_tratamento(self, paciente_id: int, medicamento: str, contexto: str) -> Dict:
        """Sugere ajuste de tratamento usando agente farmacêutico"""
        return sugerir_ajuste_dosagem(paciente_id, medicamento, contexto)
def _tentar_criar_paciente(solicitacao: str, contexto: Dict) -> Dict:
    """Se a solicitação pede criação de paciente, cria no BD."""
    texto_lower = solicitacao.lower()
    gatilhos = ["criar paciente", "novo paciente", "cadastre", "cadastro de paciente", "novo prontuário"]
    if not any(g in texto_lower for g in gatilhos):
        return {"created": False}

    system_prompt = """Extraia dados de paciente de forma estruturada.
Retorne APENAS um JSON:
{
 "nome": "...",
 "data_nascimento": "YYYY-MM-DD" ou null,
 "condicao_medica": "...",
 "telefone": "...",
 "email": "...",
 "diagnostico": "...",
 "observacoes": "..."
}"""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": solicitacao}
    ]
    try:
        resp = ai_manager.chat_completion(messages=messages, temperature=0.1, max_tokens=400)
        content = resp.get("content", "")
        if content.startswith("```"):
            content = content.strip("`").replace("json", "", 1).strip()
        data = json.loads(content)
    except Exception:
        return {"created": False, "error": "Não foi possível extrair dados para criação"}

    nome = data.get("nome")
    if not nome:
        return {"created": False, "error": "Nome não identificado"}

    prof_id = contexto.get("profissional_id") or 1

    dn_raw = data.get("data_nascimento")
    dn = None
    if dn_raw:
        try:
            dn = date_parser.parse(dn_raw).date()
        except Exception:
            dn = None

    paciente = Paciente(
        profissional_responsavel_id=prof_id,
        nome=nome,
        data_nascimento=dn or datetime.utcnow().date(),
        cpf=None,
        genero=None,
        telefone=data.get("telefone"),
        email=data.get("email"),
        endereco=None,
        diagnostico=data.get("diagnostico") or data.get("condicao_medica"),
        condicao_medica=data.get("condicao_medica") or data.get("diagnostico"),
        observacoes=data.get("observacoes"),
        em_tratamento=True
    )
    try:
        db.session.add(paciente)
        db.session.commit()
        return {"created": True, "paciente": paciente.to_dict()}
    except Exception as e:
        db.session.rollback()
        return {"created": False, "error": str(e)}




# ========== PAGAMENTOS (AGENTE FINANCEIRO) ==========

@tool
def gerar_cobranca_pix(cliente_nome: str, cliente_email: str, valor: float, descricao: str = "") -> Dict:
    """Gera cobrança PIX para um cliente (stub)."""
    try:
        charge = payment_service.create_charge(
            customer_name=cliente_nome,
            customer_email=cliente_email,
            amount=valor,
            method="pix",
            description=descricao or "Consulta/serviço AraOS",
        )
        return charge
    except Exception as e:
        return {"error": f"Erro ao gerar cobrança PIX: {str(e)}"}


@tool
def gerar_cobranca_boleto(cliente_nome: str, cliente_email: str, valor: float, descricao: str = "") -> Dict:
    """Gera boleto para um cliente (stub)."""
    try:
        charge = payment_service.create_charge(
            customer_name=cliente_nome,
            customer_email=cliente_email,
            amount=valor,
            method="boleto",
            description=descricao or "Consulta/serviço AraOS",
        )
        return charge
    except Exception as e:
        return {"error": f"Erro ao gerar boleto: {str(e)}"}


@tool
def gerar_cobranca_cartao(cliente_nome: str, cliente_email: str, valor: float, descricao: str = "") -> Dict:
    """Gera intenção de cobrança em cartão (stub)."""
    try:
        charge = payment_service.create_charge(
            customer_name=cliente_nome,
            customer_email=cliente_email,
            amount=valor,
            method="card",
            description=descricao or "Consulta/serviço AraOS",
        )
        charge["checkout_url"] = f"https://pagamentos.exemplo/checkout/{charge['id']}"
        return charge
    except Exception as e:
        return {"error": f"Erro ao gerar cobrança de cartão: {str(e)}"}


@tool
def checar_status_pagamento(cobranca_id: str) -> Dict:
    """Consulta status de uma cobrança (stub)."""
    try:
        return payment_service.get_status(cobranca_id)
    except Exception as e:
        return {"error": f"Erro ao consultar status: {str(e)}"}


@tool
def atualizar_status_pagamento(cobranca_id: str, status: str) -> Dict:
    """Atualiza status da cobrança (paid, canceled, failed) (stub)."""
    try:
        return payment_service.update_status(cobranca_id, status)
    except Exception as e:
        return {"error": f"Erro ao atualizar status: {str(e)}"}

class AgentFollowUp:
    def __init__(self, llm_config):
        self.llm = llm_config
        self.role = "Acompanhante Terapêutico Cannabis"
        self.goal = "Realizar follow-up clínico automatizado e gerar evoluções estruturadas para pacientes em tratamento com Cannabis Medicinal"
        self.backstory = """Você é um Agente de Acompanhamento Terapêutico especializado em pacientes em tratamento com Cannabis Medicinal.
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
        """

    def agent(self):
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[
                buscar_paciente_por_id,
                buscar_evolucoes_paciente,
                buscar_dosagens_paciente,
                buscar_sintomas_paciente
            ]
        )

# Instância global do sistema multi-agente
sistema_agentes = SistemaMultiAgente()
