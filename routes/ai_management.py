"""
Rotas para gerenciamento de agentes CrewAI, LLMs e prompts
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc, or_
import json
import datetime

from models import db, Profissional, LogAtividade
from models_ai import (
    AIAgent, LLMConfig, AIPrompt, CrewConfig, 
    CrewTask, CrewAgentAssociation, AIExecutionLog
)
from security_config import sanitize_input
from services.ai_agents import ai_manager

ai_management_bp = Blueprint('ai_management', __name__)

# Middleware para verificar permissões
def ai_management_required(f):
    """Decorator para verificar se o usuário pode gerenciar IA"""
    from functools import wraps
    
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        profissional = Profissional.query.get(int(current_user_id))
        
        if not profissional or profissional.role not in ['admin', 'profissional']:
            return jsonify({'error': 'Acesso negado. Permissão necessária.'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@ai_management_bp.route('/dashboard-stats', methods=['GET'])
@ai_management_required
def ai_dashboard_stats():
    """Retorna estatísticas do dashboard de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Contagem total (visão global) e por usuário
        total_agents = AIAgent.query.count()
        total_prompts = AIPrompt.query.count()
        total_crews = CrewConfig.query.count()
        total_llms = LLMConfig.query.count()
        my_agents = AIAgent.query.filter_by(created_by=current_user_id).count()
        my_prompts = AIPrompt.query.filter_by(created_by=current_user_id).count()
        my_crews = CrewConfig.query.filter_by(created_by=current_user_id).count()
        my_llms = LLMConfig.query.filter_by(created_by=current_user_id).count()
        
        # Execuções recentes (últimos 7 dias)
        sete_dias_atras = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        recent_executions = AIExecutionLog.query.filter(
            AIExecutionLog.created_by == current_user_id,
            AIExecutionLog.created_at >= sete_dias_atras
        ).count()
        
        # Provedores disponíveis
        available_providers = ai_manager.get_available_providers()
        
        return jsonify({
            'stats': {
                'agents': total_agents,
                'prompts': total_prompts,
                'crews': total_crews,
                'llm_configs': total_llms,
                'recent_executions': recent_executions
            },
            'stats_my': {
                'agents': my_agents,
                'prompts': my_prompts,
                'crews': my_crews,
                'llm_configs': my_llms
            },
            'ai_status': {
                'available_providers': available_providers,
                'default_provider': ai_manager.default_provider,
                'default_model': ai_manager.default_model,
                'default_vision_provider': ai_manager.default_vision_provider,
                'default_vision_model': ai_manager.default_vision_model,
                'default_multimodal_provider': ai_manager.default_multimodal_provider,
                'default_multimodal_model': ai_manager.default_multimodal_model
            },
            'updated_at': datetime.datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter estatísticas de IA: {str(e)}'}), 500

# ========== LLM CONFIGS ==========

@ai_management_bp.route('/llm-configs', methods=['GET'])
@ai_management_required
def list_llm_configs():
    """Lista configurações de LLM"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Filtrar por usuário ou compartilhados
        llm_configs = LLMConfig.query.filter(
            or_(
                LLMConfig.created_by == current_user_id,
                LLMConfig.is_default == True
            )
        ).order_by(desc(LLMConfig.created_at)).all()
        
        return jsonify({
            'llm_configs': [config.to_dict() for config in llm_configs],
            'total': len(llm_configs)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao listar configurações de LLM: {str(e)}'}), 500

@ai_management_bp.route('/llm-configs', methods=['POST'])
@ai_management_required
def create_llm_config():
    """Cria uma nova configuração de LLM"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        # Validação básica
        required_fields = ['nome', 'provider', 'model']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Campos obrigatórios: {", ".join(required_fields)}'}), 400
        
        # Verificar se já existe configuração com mesmo nome
        existing = LLMConfig.query.filter_by(
            nome=data['nome'],
            created_by=current_user_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Já existe uma configuração com este nome'}), 409
        
        # Criar nova configuração
        llm_config = LLMConfig(
            nome=data['nome'],
            provider=data['provider'],
            model=data['model'],
            api_key_env_var=data.get('api_key_env_var'),
            base_url=data.get('base_url'),
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens', 1000),
            top_p=data.get('top_p', 1.0),
            frequency_penalty=data.get('frequency_penalty', 0.0),
            presence_penalty=data.get('presence_penalty', 0.0),
            timeout=data.get('timeout', 30),
            max_retries=data.get('max_retries', 3),
            is_default=data.get('is_default', False),
            is_active=data.get('is_active', True),
            created_by=current_user_id
        )
        
        db.session.add(llm_config)
        
        # Se for marcado como default, remover default de outras configurações do usuário
        if llm_config.is_default:
            LLMConfig.query.filter(
                LLMConfig.created_by == current_user_id,
                LLMConfig.id != llm_config.id,
                LLMConfig.is_default == True
            ).update({'is_default': False})
        
        db.session.commit()
        
        # Registrar log
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='CRIAR_LLM_CONFIG',
            detalhes=f'Configuração de LLM criada: {llm_config.nome} ({llm_config.provider}/{llm_config.model})'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Configuração de LLM criada com sucesso',
            'llm_config': llm_config.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar configuração de LLM: {str(e)}'}), 500

@ai_management_bp.route('/llm-configs/<int:config_id>', methods=['PUT'])
@ai_management_required
def update_llm_config(config_id):
    """Atualiza uma configuração de LLM"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        llm_config = LLMConfig.query.get(config_id)
        if not llm_config:
            return jsonify({'error': 'Configuração de LLM não encontrada'}), 404
        
        # Verificar permissão
        if llm_config.created_by != current_user_id and not llm_config.is_default:
            return jsonify({'error': 'Permissão negada para editar esta configuração'}), 403
        
        # Atualizar campos
        update_fields = ['nome', 'provider', 'model', 'api_key_env_var', 'base_url',
                        'temperature', 'max_tokens', 'top_p', 'frequency_penalty',
                        'presence_penalty', 'timeout', 'max_retries', 'is_default', 'is_active']
        
        for field in update_fields:
            if field in data:
                setattr(llm_config, field, data[field])
        
        llm_config.updated_at = datetime.datetime.utcnow()
        
        # Se for marcado como default, remover default de outras configurações do usuário
        if llm_config.is_default and llm_config.created_by == current_user_id:
            LLMConfig.query.filter(
                LLMConfig.created_by == current_user_id,
                LLMConfig.id != config_id,
                LLMConfig.is_default == True
            ).update({'is_default': False})
        
        db.session.commit()
        
        # Registrar log
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='ATUALIZAR_LLM_CONFIG',
            detalhes=f'Configuração de LLM atualizada: {llm_config.nome} (ID: {config_id})'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Configuração de LLM atualizada com sucesso',
            'llm_config': llm_config.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar configuração de LLM: {str(e)}'}), 500

@ai_management_bp.route('/llm-configs/<int:config_id>', methods=['DELETE'])
@ai_management_required
def delete_llm_config(config_id):
    """Remove uma configuração de LLM"""
    try:
        current_user_id = int(get_jwt_identity())
        
        llm_config = LLMConfig.query.get(config_id)
        if not llm_config:
            return jsonify({'error': 'Configuração de LLM não encontrada'}), 404
        
        # Verificar permissão
        if llm_config.created_by != current_user_id:
            return jsonify({'error': 'Permissão negada para remover esta configuração'}), 403
        
        # Verificar se está sendo usada por algum agente
        agents_using = AIAgent.query.filter_by(llm_config_id=config_id).count()
        if agents_using > 0:
            return jsonify({
                'error': 'Não é possível remover configuração em uso por agentes',
                'agents_using': agents_using
            }), 400
        
        # Registrar log antes de deletar
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='REMOVER_LLM_CONFIG',
            detalhes=f'Configuração de LLM removida: {llm_config.nome} (ID: {config_id})'
        )
        db.session.add(log)
        
        db.session.delete(llm_config)
        db.session.commit()
        
        return jsonify({
            'message': 'Configuração de LLM removida com sucesso',
            'config_id': config_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover configuração de LLM: {str(e)}'}), 500

# ========== AI AGENTS ==========

@ai_management_bp.route('/agents', methods=['GET'])
@ai_management_required
def list_agents():
    """Lista agentes de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        
        agents = AIAgent.query.filter_by(created_by=current_user_id).order_by(desc(AIAgent.created_at)).all()
        
        return jsonify({
            'agents': [agent.to_dict() for agent in agents],
            'total': len(agents)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao listar agentes: {str(e)}'}), 500

@ai_management_bp.route('/agents', methods=['POST'])
@ai_management_required
def create_agent():
    """Cria um novo agente de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        # Validação básica
        required_fields = ['nome', 'role', 'goal']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Campos obrigatórios: {", ".join(required_fields)}'}), 400
        
        # Verificar se já existe agente com mesmo nome
        existing = AIAgent.query.filter_by(
            nome=data['nome'],
            created_by=current_user_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Já existe um agente com este nome'}), 409
        
        # Verificar LLM config se fornecida
        llm_config_id = data.get('llm_config_id')
        if llm_config_id:
            llm_config = LLMConfig.query.get(llm_config_id)
            if not llm_config or (llm_config.created_by != current_user_id and not llm_config.is_default):
                return jsonify({'error': 'Configuração de LLM não encontrada ou sem permissão'}), 404
        
        # Criar novo agente
        agent = AIAgent(
            nome=data['nome'],
            descricao=data.get('descricao'),
            role=data['role'],
            goal=data['goal'],
            backstory=data.get('backstory'),
            llm_config_id=llm_config_id,
            allow_delegation=data.get('allow_delegation', True),
            max_iter=data.get('max_iter', 3),
            verbose=data.get('verbose', True),
            memory=data.get('memory', True),
            max_tokens=data.get('max_tokens', 1000),
            temperature=data.get('temperature', 0.7),
            tools_config=data.get('tools_config'),
            is_active=data.get('is_active', True),
            created_by=current_user_id
        )
        
        db.session.add(agent)
        db.session.commit()
        
        # Registrar log
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='CRIAR_AGENTE_IA',
            detalhes=f'Agente de IA criado: {agent.nome} (Role: {agent.role})'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Agente criado com sucesso',
            'agent': agent.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar agente: {str(e)}'}), 500

@ai_management_bp.route('/agents/<int:agent_id>', methods=['PUT'])
@ai_management_required
def update_agent(agent_id):
    """Atualiza um agente de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        agent = AIAgent.query.get(agent_id)
        if not agent:
            return jsonify({'error': 'Agente não encontrado'}), 404
        
        # Verificar permissão
        if agent.created_by != current_user_id:
            return jsonify({'error': 'Permissão negada para editar este agente'}), 403
        
        # Atualizar campos
        update_fields = ['nome', 'descricao', 'role', 'goal', 'backstory', 'llm_config_id',
                        'allow_delegation', 'max_iter', 'verbose', 'memory', 'max_tokens',
                        'temperature', 'tools_config', 'is_active']
        
        for field in update_fields:
            if field in data:
                setattr(agent, field, data[field])
        
        agent.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        # Registrar log
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='ATUALIZAR_AGENTE_IA',
            detalhes=f'Agente de IA atualizado: {agent.nome} (ID: {agent_id})'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Agente atualizado com sucesso',
            'agent': agent.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar agente: {str(e)}'}), 500

@ai_management_bp.route('/agents/<int:agent_id>', methods=['DELETE'])
@ai_management_required
def delete_agent(agent_id):
    """Remove um agente de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        
        agent = AIAgent.query.get(agent_id)
        if not agent:
            return jsonify({'error': 'Agente não encontrado'}), 404
        
        # Verificar permissão
        if agent.created_by != current_user_id:
            return jsonify({'error': 'Permissão negada para remover este agente'}), 403
        
        # Verificar se está em uso por crews
        crews_using = CrewAgentAssociation.query.filter_by(agent_id=agent_id).count()
        if crews_using > 0:
            return jsonify({
                'error': 'Não é possível remover agente em uso por crews',
                'crews_using': crews_using
            }), 400
        
        # Registrar log antes de deletar
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='REMOVER_AGENTE_IA',
            detalhes=f'Agente de IA removido: {agent.nome} (ID: {agent_id})'
        )
        db.session.add(log)
        
        db.session.delete(agent)
        db.session.commit()
        
        return jsonify({
            'message': 'Agente removido com sucesso',
            'agent_id': agent_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover agente: {str(e)}'}), 500

# ========== AI PROMPTS ==========

@ai_management_bp.route('/prompts', methods=['GET'])
@ai_management_required
def list_prompts():
    """Lista prompts de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        
        prompts = AIPrompt.query.filter_by(created_by=current_user_id).order_by(desc(AIPrompt.created_at)).all()
        
        return jsonify({
            'prompts': [prompt.to_dict() for prompt in prompts],
            'total': len(prompts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao listar prompts: {str(e)}'}), 500

@ai_management_bp.route('/prompts', methods=['POST'])
@ai_management_required
def create_prompt():
    """Cria um novo prompt de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        # Validação básica
        required_fields = ['nome', 'template']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Campos obrigatórios: {", ".join(required_fields)}'}), 400
        
        # Verificar se já existe prompt com mesmo nome
        existing = AIPrompt.query.filter_by(
            nome=data['nome'],
            created_by=current_user_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Já existe um prompt com este nome'}), 409
        
        # Verificar agente se fornecido
        agent_id = data.get('agent_id')
        if agent_id:
            agent = AIAgent.query.get(agent_id)
            if not agent or agent.created_by != current_user_id:
                return jsonify({'error': 'Agente não encontrado ou sem permissão'}), 404
        
        # Criar novo prompt
        prompt = AIPrompt(
            nome=data['nome'],
            descricao=data.get('descricao'),
            template=data['template'],
            variables=data.get('variables', []),
            categoria=data.get('categoria'),
            agent_id=agent_id,
            is_system_prompt=data.get('is_system_prompt', False),
            version=data.get('version', '1.0.0'),
            is_active=data.get('is_active', True),
            created_by=current_user_id
        )
        
        db.session.add(prompt)
        db.session.commit()
        
        # Registrar log
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='CRIAR_PROMPT_IA',
            detalhes=f'Prompt de IA criado: {prompt.nome} (Categoria: {prompt.categoria})'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Prompt criado com sucesso',
            'prompt': prompt.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar prompt: {str(e)}'}), 500

@ai_management_bp.route('/prompts/<int:prompt_id>', methods=['PUT'])
@ai_management_required
def update_prompt(prompt_id):
    """Atualiza um prompt de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        prompt = AIPrompt.query.get(prompt_id)
        if not prompt:
            return jsonify({'error': 'Prompt não encontrado'}), 404
        
        # Verificar permissão
        if prompt.created_by != current_user_id:
            return jsonify({'error': 'Permissão negada para editar este prompt'}), 403
        
        # Atualizar campos
        update_fields = ['nome', 'descricao', 'template', 'variables', 'categoria',
                        'agent_id', 'is_system_prompt', 'version', 'is_active']
        
        for field in update_fields:
            if field in data:
                setattr(prompt, field, data[field])
        
        prompt.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        # Registrar log
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='ATUALIZAR_PROMPT_IA',
            detalhes=f'Prompt de IA atualizado: {prompt.nome} (ID: {prompt_id})'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Prompt atualizado com sucesso',
            'prompt': prompt.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar prompt: {str(e)}'}), 500

@ai_management_bp.route('/prompts/<int:prompt_id>', methods=['DELETE'])
@ai_management_required
def delete_prompt(prompt_id):
    """Remove um prompt de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        
        prompt = AIPrompt.query.get(prompt_id)
        if not prompt:
            return jsonify({'error': 'Prompt não encontrado'}), 404
        
        # Verificar permissão
        if prompt.created_by != current_user_id:
            return jsonify({'error': 'Permissão negada para remover este prompt'}), 403
        
        # Verificar se está em uso por tarefas
        tasks_using = CrewTask.query.filter_by(prompt_id=prompt_id).count()
        if tasks_using > 0:
            return jsonify({
                'error': 'Não é possível remover prompt em uso por tarefas',
                'tasks_using': tasks_using
            }), 400
        
        # Registrar log antes de deletar
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='REMOVER_PROMPT_IA',
            detalhes=f'Prompt de IA removido: {prompt.nome} (ID: {prompt_id})'
        )
        db.session.add(log)
        
        db.session.delete(prompt)
        db.session.commit()
        
        return jsonify({
            'message': 'Prompt removido com sucesso',
            'prompt_id': prompt_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover prompt: {str(e)}'}), 500

# ========== CREW CONFIGS ==========

@ai_management_bp.route('/crews', methods=['GET'])
@ai_management_required
def list_crews():
    """Lista crews de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        
        crews = CrewConfig.query.filter_by(created_by=current_user_id).order_by(desc(CrewConfig.created_at)).all()
        
        return jsonify({
            'crews': [crew.to_dict() for crew in crews],
            'total': len(crews)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao listar crews: {str(e)}'}), 500

@ai_management_bp.route('/crews', methods=['POST'])
@ai_management_required
def create_crew():
    """Cria uma nova crew de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        # Validação básica
        required_fields = ['nome']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Campos obrigatórios: {", ".join(required_fields)}'}), 400
        
        # Verificar se já existe crew com mesmo nome
        existing = CrewConfig.query.filter_by(
            nome=data['nome'],
            created_by=current_user_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Já existe uma crew com este nome'}), 409
        
        # Criar nova crew
        crew = CrewConfig(
            nome=data['nome'],
            descricao=data.get('descricao'),
            process=data.get('process', 'sequential'),
            verbose=data.get('verbose', True),
            memory=data.get('memory', True),
            max_iter=data.get('max_iter', 3),
            share_crew=data.get('share_crew', False),
            is_active=data.get('is_active', True),
            created_by=current_user_id
        )
        
        db.session.add(crew)
        db.session.commit()
        
        # Adicionar agentes se fornecidos
        agent_ids = data.get('agent_ids', [])
        for order, agent_id in enumerate(agent_ids):
            agent = AIAgent.query.get(agent_id)
            if agent and agent.created_by == current_user_id:
                association = CrewAgentAssociation(
                    crew_id=crew.id,
                    agent_id=agent_id,
                    order=order
                )
                db.session.add(association)
        
        db.session.commit()
        
        # Registrar log
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='CRIAR_CREW_IA',
            detalhes=f'Crew de IA criada: {crew.nome} com {len(agent_ids)} agentes'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Crew criada com sucesso',
            'crew': crew.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar crew: {str(e)}'}), 500

@ai_management_bp.route('/crews/<int:crew_id>', methods=['PUT'])
@ai_management_required
def update_crew(crew_id):
    """Atualiza uma crew de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        crew = CrewConfig.query.get(crew_id)
        if not crew:
            return jsonify({'error': 'Crew não encontrada'}), 404
        
        # Verificar permissão
        if crew.created_by != current_user_id:
            return jsonify({'error': 'Permissão negada para editar esta crew'}), 403
        
        # Atualizar campos básicos
        update_fields = ['nome', 'descricao', 'process', 'verbose', 'memory',
                        'max_iter', 'share_crew', 'is_active']
        
        for field in update_fields:
            if field in data:
                setattr(crew, field, data[field])
        
        crew.updated_at = datetime.datetime.utcnow()
        
        # Atualizar agentes se fornecidos
        if 'agent_ids' in data:
            # Remover associações existentes
            CrewAgentAssociation.query.filter_by(crew_id=crew_id).delete()
            
            # Adicionar novas associações
            agent_ids = data['agent_ids']
            for order, agent_id in enumerate(agent_ids):
                agent = AIAgent.query.get(agent_id)
                if agent and agent.created_by == current_user_id:
                    association = CrewAgentAssociation(
                        crew_id=crew_id,
                        agent_id=agent_id,
                        order=order
                    )
                    db.session.add(association)
        
        db.session.commit()
        
        # Registrar log
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='ATUALIZAR_CREW_IA',
            detalhes=f'Crew de IA atualizada: {crew.nome} (ID: {crew_id})'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Crew atualizada com sucesso',
            'crew': crew.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar crew: {str(e)}'}), 500

@ai_management_bp.route('/crews/<int:crew_id>', methods=['DELETE'])
@ai_management_required
def delete_crew(crew_id):
    """Remove uma crew de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        
        crew = CrewConfig.query.get(crew_id)
        if not crew:
            return jsonify({'error': 'Crew não encontrada'}), 404
        
        # Verificar permissão
        if crew.created_by != current_user_id:
            return jsonify({'error': 'Permissão negada para remover esta crew'}), 403
        
        # Registrar log antes de deletar
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='REMOVER_CREW_IA',
            detalhes=f'Crew de IA removida: {crew.nome} (ID: {crew_id})'
        )
        db.session.add(log)
        
        db.session.delete(crew)
        db.session.commit()
        
        return jsonify({
            'message': 'Crew removida com sucesso',
            'crew_id': crew_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover crew: {str(e)}'}), 500

# ========== CREW TASKS ==========

@ai_management_bp.route('/crews/<int:crew_id>/tasks', methods=['GET'])
@ai_management_required
def list_crew_tasks(crew_id):
    """Lista tarefas de uma crew"""
    try:
        current_user_id = int(get_jwt_identity())
        
        crew = CrewConfig.query.get(crew_id)
        if not crew or crew.created_by != current_user_id:
            return jsonify({'error': 'Crew não encontrada ou sem permissão'}), 404
        
        tasks = CrewTask.query.filter_by(crew_id=crew_id).order_by(CrewTask.order).all()
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks],
            'total': len(tasks)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao listar tarefas: {str(e)}'}), 500

@ai_management_bp.route('/crews/<int:crew_id>/tasks', methods=['POST'])
@ai_management_required
def create_crew_task(crew_id):
    """Cria uma nova tarefa para uma crew"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        # Verificar crew
        crew = CrewConfig.query.get(crew_id)
        if not crew or crew.created_by != current_user_id:
            return jsonify({'error': 'Crew não encontrada ou sem permissão'}), 404
        
        # Validação básica
        required_fields = ['nome', 'expected_output']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Campos obrigatórios: {", ".join(required_fields)}'}), 400
        
        # Verificar agente se fornecido
        agent_id = data.get('agent_id')
        if agent_id:
            agent = AIAgent.query.get(agent_id)
            if not agent or agent.created_by != current_user_id:
                return jsonify({'error': 'Agente não encontrado ou sem permissão'}), 404
        
        # Verificar prompt se fornecido
        prompt_id = data.get('prompt_id')
        if prompt_id:
            prompt = AIPrompt.query.get(prompt_id)
            if not prompt or prompt.created_by != current_user_id:
                return jsonify({'error': 'Prompt não encontrado ou sem permissão'}), 404
        
        # Criar nova tarefa
        task = CrewTask(
            crew_id=crew_id,
            nome=data['nome'],
            descricao=data.get('descricao'),
            expected_output=data['expected_output'],
            agent_id=agent_id,
            prompt_id=prompt_id,
            context=data.get('context'),
            async_execution=data.get('async_execution', False),
            order=data.get('order', 0),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Registrar log
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='CRIAR_TAREFA_CREW',
            detalhes=f'Tarefa criada para crew {crew.nome}: {task.nome}'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Tarefa criada com sucesso',
            'task': task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao criar tarefa: {str(e)}'}), 500

@ai_management_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@ai_management_required
def update_crew_task(task_id):
    """Atualiza uma tarefa de crew"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        task = CrewTask.query.get(task_id)
        if not task:
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        
        # Verificar permissão através da crew
        crew = CrewConfig.query.get(task.crew_id)
        if not crew or crew.created_by != current_user_id:
            return jsonify({'error': 'Permissão negada para editar esta tarefa'}), 403
        
        # Atualizar campos
        update_fields = ['nome', 'descricao', 'expected_output', 'agent_id',
                        'prompt_id', 'context', 'async_execution', 'order', 'is_active']
        
        for field in update_fields:
            if field in data:
                setattr(task, field, data[field])
        
        task.updated_at = datetime.datetime.utcnow()
        db.session.commit()
        
        # Registrar log
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='ATUALIZAR_TAREFA_CREW',
            detalhes=f'Tarefa de crew atualizada: {task.nome} (ID: {task_id})'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Tarefa atualizada com sucesso',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar tarefa: {str(e)}'}), 500

@ai_management_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@ai_management_required
def delete_crew_task(task_id):
    """Remove uma tarefa de crew"""
    try:
        current_user_id = int(get_jwt_identity())
        
        task = CrewTask.query.get(task_id)
        if not task:
            return jsonify({'error': 'Tarefa não encontrada'}), 404
        
        # Verificar permissão através da crew
        crew = CrewConfig.query.get(task.crew_id)
        if not crew or crew.created_by != current_user_id:
            return jsonify({'error': 'Permissão negada para remover esta tarefa'}), 403
        
        # Registrar log antes de deletar
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='REMOVER_TAREFA_CREW',
            detalhes=f'Tarefa de crew removida: {task.nome} (ID: {task_id})'
        )
        db.session.add(log)
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'message': 'Tarefa removida com sucesso',
            'task_id': task_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao remover tarefa: {str(e)}'}), 500

# ========== AI EXECUTION ==========

@ai_management_bp.route('/execute/crew/<int:crew_id>', methods=['POST'])
@ai_management_required
def execute_crew(crew_id):
    """Executa uma crew de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        # Verificar crew
        crew = CrewConfig.query.get(crew_id)
        if not crew or crew.created_by != current_user_id:
            return jsonify({'error': 'Crew não encontrada ou sem permissão'}), 404
        
        # Verificar se a crew está ativa
        if not crew.is_active:
            return jsonify({'error': 'Crew não está ativa'}), 400
        
        # Verificar se a crew tem agentes
        if not crew.agents:
            return jsonify({'error': 'Crew não tem agentes configurados'}), 400
        
        # Dados de entrada
        input_data = data.get('input_data', {})
        
        # TODO: Implementar execução real da crew usando CrewAI
        # Por enquanto, retornar simulação
        execution_log = AIExecutionLog(
            crew_id=crew_id,
            input_data=input_data,
            output_data={'simulation': True, 'message': 'Execução de crew simulada'},
            status='success',
            execution_time_ms=500,
            tokens_used=100,
            cost_estimate=0.01,
            created_by=current_user_id
        )
        
        db.session.add(execution_log)
        
        # Registrar log de atividade
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='EXECUTAR_CREW_IA',
            detalhes=f'Crew de IA executada: {crew.nome} (ID: {crew_id})'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Crew executada com sucesso (simulação)',
            'execution_id': execution_log.id,
            'output': execution_log.output_data,
            'execution_time_ms': execution_log.execution_time_ms
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao executar crew: {str(e)}'}), 500

@ai_management_bp.route('/execute/agent/<int:agent_id>', methods=['POST'])
@ai_management_required
def execute_agent(agent_id):
    """Executa um agente de IA individualmente"""
    try:
        current_user_id = int(get_jwt_identity())
        data = request.get_json()
        data = sanitize_input(data)
        
        # Verificar agente
        agent = AIAgent.query.get(agent_id)
        if not agent or agent.created_by != current_user_id:
            return jsonify({'error': 'Agente não encontrado ou sem permissão'}), 404
        
        # Verificar se o agente está ativo
        if not agent.is_active:
            return jsonify({'error': 'Agente não está ativo'}), 400
        
        # Dados de entrada
        input_data = data.get('input_data', {})
        prompt_text = data.get('prompt')
        
        # TODO: Implementar execução real do agente usando CrewAI
        # Por enquanto, retornar simulação
        execution_log = AIExecutionLog(
            agent_id=agent_id,
            input_data=input_data,
            output_data={
                'simulation': True,
                'message': f'Agente {agent.nome} executado',
                'role': agent.role,
                'response': 'Esta é uma resposta simulada do agente.'
            },
            status='success',
            execution_time_ms=300,
            tokens_used=50,
            cost_estimate=0.005,
            created_by=current_user_id
        )
        
        db.session.add(execution_log)
        
        # Registrar log de atividade
        log = LogAtividade(
            profissional_id=current_user_id,
            acao='EXECUTAR_AGENTE_IA',
            detalhes=f'Agente de IA executado: {agent.nome} (ID: {agent_id})'
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'message': 'Agente executado com sucesso (simulação)',
            'execution_id': execution_log.id,
            'output': execution_log.output_data,
            'execution_time_ms': execution_log.execution_time_ms
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao executar agente: {str(e)}'}), 500

# ========== EXECUTION LOGS ==========

@ai_management_bp.route('/execution-logs', methods=['GET'])
@ai_management_required
def list_execution_logs():
    """Lista logs de execução de IA"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Filtros
        crew_id = request.args.get('crew_id', type=int)
        agent_id = request.args.get('agent_id', type=int)
        status = request.args.get('status', type=str)
        
        query = AIExecutionLog.query.filter_by(created_by=current_user_id)
        
        if crew_id:
            query = query.filter_by(crew_id=crew_id)
        if agent_id:
            query = query.filter_by(agent_id=agent_id)
        if status:
            query = query.filter_by(status=status)
        
        # Ordenar por data mais recente
        logs = query.order_by(desc(AIExecutionLog.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs_list = [log.to_dict() for log in logs.items]
        
        return jsonify({
            'logs': logs_list,
            'pagination': {
                'page': logs.page,
                'per_page': logs.per_page,
                'total': logs.total,
                'pages': logs.pages
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao listar logs de execução: {str(e)}'}), 500

@ai_management_bp.route('/execution-logs/<int:log_id>', methods=['GET'])
@ai_management_required
def get_execution_log(log_id):
    """Obtém detalhes de um log de execução"""
    try:
        current_user_id = int(get_jwt_identity())
        
        log = AIExecutionLog.query.get(log_id)
        if not log or log.created_by != current_user_id:
            return jsonify({'error': 'Log de execução não encontrado ou sem permissão'}), 404
        
        return jsonify({
            'log': log.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter log de execução: {str(e)}'}), 500

# ========== AI PROVIDERS INTEGRATION ==========

@ai_management_bp.route('/providers/available', methods=['GET'])
@ai_management_required
def get_available_providers():
    """Retorna provedores de IA disponíveis"""
    try:
        available_providers = ai_manager.get_available_providers()
        
        providers_info = []
        for provider in available_providers:
            provider_info = {
                'name': provider,
                'models': ai_manager.providers[provider]['models'],
                'available': True
            }
            providers_info.append(provider_info)
        
        return jsonify({
            'providers': providers_info,
            'default_provider': ai_manager.default_provider,
            'default_model': ai_manager.default_model
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter provedores disponíveis: {str(e)}'}), 500

@ai_management_bp.route('/providers/test', methods=['POST'])
@ai_management_required
def test_ai_provider():
    """Testa conexão com um provedor de IA"""
    try:
        data = request.get_json()
        provider = data.get('provider', ai_manager.default_provider)
        model = data.get('model', ai_manager.default_model)
        
        test_messages = [
            {"role": "system", "content": "Você é um assistente útil. Responda apenas 'Teste de conexão bem-sucedido!'."},
            {"role": "user", "content": "Teste de conexão"}
        ]
        
        try:
            response = ai_manager.chat_completion(
                messages=test_messages,
                provider=provider,
                model=model,
                temperature=0.1,
                max_tokens=50
            )
            
            return jsonify({
                'success': True,
                'provider': provider,
                'model': model,
                'response': response.get('content', ''),
                'used_provider': response.get('provider', 'unknown'),
                'used_model': response.get('model', 'unknown')
            })
            
        except Exception as ai_error:
            return jsonify({
                'success': False,
                'provider': provider,
                'model': model,
                'error': str(ai_error),
                'available_providers': ai_manager.get_available_providers()
            }), 400
            
    except Exception as e:
        return jsonify({'error': f'Erro no teste de conexão: {str(e)}'}), 500
