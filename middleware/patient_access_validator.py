"""
Middleware de Validação de Acesso a Pacientes (Multi-Tenant)

Este módulo fornece funções utilitárias para validar acesso a pacientes
em todo o sistema, garantindo isolamento correto de dados entre contas.

Uso:
    from middleware.patient_access_validator import validate_patient_access
    
    @jwt_required()
    def minha_rota():
        user_id = int(get_jwt_identity())
        if not validate_patient_access(paciente_id, user_id):
            return jsonify({'error': 'Acesso negado'}), 403
        # Continuar com a lógica...
"""

import logging
from functools import wraps
from typing import Optional, Tuple

from flask import jsonify, g
from flask_jwt_extended import get_jwt_identity

from models import Paciente, CompartilhamentoPaciente, Profissional

logger = logging.getLogger(__name__)


def get_profissional_logado() -> Optional[Profissional]:
    """
    Obtém o profissional logado atualmente.
    Deve ser usado dentro de um contexto de requisição Flask.
    
    Returns:
        Profissional ou None se não autenticado
    """
    try:
        profissional_id = get_jwt_identity()
        if profissional_id:
            return Profissional.query.get(int(profissional_id))
    except Exception as e:
        logger.error(f"Erro ao obter profissional logado: {e}")
    return None


def validate_patient_access(paciente_id: int, profissional_id: int) -> bool:
    """
    Valida se o profissional tem acesso ao paciente.
    
    Regras de acesso:
    1. Admin/Superadmin: acesso total
    2. Profissional responsável: acesso total
    3. Compartilhamento ativo: acesso total
    4. Mesma associação: acesso total (para modelos com associacao_id)
    
    Args:
        paciente_id: ID do paciente a ser acessado
        profissional_id: ID do profissional que solicita acesso
        
    Returns:
        True se tem acesso, False caso contrário
    """
    # Buscar paciente
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        logger.warning(f"Paciente {paciente_id} não encontrado")
        return False
    
    # Buscar profissional
    profissional = Profissional.query.get(profissional_id)
    if not profissional:
        logger.warning(f"Profissional {profissional_id} não encontrado")
        return False
    
    # Admin e superadmin têm acesso total
    if profissional.role in ('admin', 'superadmin'):
        logger.debug(f"Admin {profissional_id} acessando paciente {paciente_id}")
        return True
    
    # Verificar se é o profissional responsável
    if paciente.profissional_responsavel_id == profissional_id:
        logger.debug(f"Profissional {profissional_id} é responsável pelo paciente {paciente_id}")
        return True
    
    # Verificar se tem compartilhamento ativo
    compartilhamento = CompartilhamentoPaciente.query.filter_by(
        paciente_id=paciente_id,
        profissional_id=profissional_id,
        ativo=True
    ).first()
    
    if compartilhamento:
        logger.debug(f"Profissional {profissional_id} tem compartilhamento do paciente {paciente_id}")
        return True
    
    # Verificar se é da mesma associação (se ambos tiverem associacao_id)
    if hasattr(paciente, 'associacao_id') and paciente.associacao_id:
        if hasattr(profissional, 'associacao_id') and profissional.associacao_id:
            if paciente.associacao_id == profissional.associacao_id:
                logger.debug(f"Profissional {profissional_id} e paciente {paciente_id} são da mesma associação")
                return True
    
    logger.warning(f"Acesso negado: Profissional {profissional_id} tentou acessar paciente {paciente_id}")
    return False


def check_patient_access(paciente_id: int) -> Tuple[bool, Optional[str]]:
    """
    Verifica acesso ao paciente e retorna tuple com resultado e mensagem.
    
    Args:
        paciente_id: ID do paciente
        
    Returns:
        Tuple (tem_acesso, mensagem_erro)
    """
    profissional = get_profissional_logado()
    if not profissional:
        return False, "Usuário não autenticado"
    
    if validate_patient_access(paciente_id, profissional.id):
        return True, None
    
    return False, "Você não tem permissão para acessar este paciente"


def require_patient_access(f):
    """
    Decorator que exige acesso válido ao paciente para a rota.
    
    Espera que a rota tenha um parâmetro 'paciente_id' na URL ou no body JSON.
    
    Uso:
        @require_patient_access
        def minha_rota(paciente_id):
            # paciente_id é válido e o usuário tem acesso
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        profissional = get_profissional_logado()
        
        if not profissional:
            logger.warning("Tentativa de acesso sem autenticação")
            return jsonify({
                'error': 'Autenticação necessária',
                'codigo': 'NAO_AUTENTICADO'
            }), 401
        
        # Tentar obter paciente_id de diferentes fontes
        paciente_id = None
        
        # Do kwargs (URL parameters)
        if 'paciente_id' in kwargs:
            paciente_id = kwargs['paciente_id']
        
        # Do request (JSON body)
        from flask import request
        if not paciente_id and request.is_json:
            data = request.get_json()
            if data and 'paciente_id' in data:
                paciente_id = data['paciente_id']
        
        if not paciente_id:
            return jsonify({
                'error': 'paciente_id é obrigatório',
                'codigo': 'PACIENTE_ID_OBRIGATORIO'
            }), 400
        
        # Validar acesso
        if not validate_patient_access(paciente_id, profissional.id):
            logger.warning(f"Profissional {profissional.id} tentou acessar paciente {paciente_id} sem permissão")
            return jsonify({
                'error': 'Paciente não encontrado ou você não tem permissão para acessar',
                'codigo': 'ACESSO_NEGADO'
            }), 403
        
        # Armazenar paciente validado no contexto para uso na rota
        g.validated_paciente_id = paciente_id
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_accessible_patients_query(profissional_id: int, base_query):
    """
    Filtra uma query de pacientes para retornar apenas os que o profissional
    tem acesso.
    
    Args:
        profissional_id: ID do profissional
        base_query: Query base de pacientes (ex: Paciente.query)
        
    Returns:
        Query filtrada com apenas pacientes acessíveis
    """
    profissional = Profissional.query.get(profissional_id)
    if not profissional:
        return base_query.filter(Paciente.id == -1)  # Nenhum resultado
    
    # Admin tem acesso a todos
    if profissional.role in ('admin', 'superadmin'):
        return base_query
    
    # Filtrar por responsabilidade ou compartilhamento
    from models import CompartilhamentoPaciente
    
    # Pacientes do profissional
    responsavel_ids = [paciente_id[0] for paciente_id in 
        db.session.query(Paciente.id).filter(
            Paciente.profissional_responsavel_id == profissional_id
        ).all()]
    
    # Pacientes compartilhados
    compartilhados_ids = [c.paciente_id for c in 
        CompartilhamentoPaciente.query.filter_by(
            profissional_id=profissional_id,
            ativo=True
        ).all()]
    
    # Unir IDs
    acessiveis_ids = set(responsavel_ids + compartilhados_ids)
    
    if acessiveis_ids:
        return base_query.filter(Paciente.id.in_(acessiveis_ids))
    
    return base_query.filter(Paciente.id == -1)  # Nenhum resultado


def log_patient_access(paciente_id: int, profissional_id: int, acao: str):
    """
    Registra log de acesso ao paciente para auditoria.
    
    Args:
        paciente_id: ID do paciente
        profissional_id: ID do profissional
        acao: Descrição da ação (ex: 'visualizacao', 'edicao', 'chat_ia')
    """
    from models import LogAtividade
    
    try:
        log = LogAtividade(
            profissional_id=profissional_id,
            acao=f"ACESSO_PACIENTE_IA:{acao}",
            detalhes=f"Paciente {paciente_id}",
            data_hora=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.error(f"Erro ao registrar log de acesso: {e}")


# Import datetime para log
from datetime import datetime

# Import db
from models import db