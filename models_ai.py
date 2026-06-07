"""
Modelos de dados para o sistema de gerenciamento de agentes CrewAI
"""

from datetime import datetime
from models import db

class AIAgent(db.Model):
    __tablename__ = 'ai_agents'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    role = db.Column(db.String(200), nullable=False)  # Papel do agente (ex: "Analista Médico")
    goal = db.Column(db.Text, nullable=False)  # Objetivo do agente
    backstory = db.Column(db.Text)  # Histórico/contexto do agente
    llm_config_id = db.Column(db.Integer, db.ForeignKey('llm_configs.id'), nullable=True)
    allow_delegation = db.Column(db.Boolean, default=True)
    max_iter = db.Column(db.Integer, default=3)
    verbose = db.Column(db.Boolean, default=True)
    memory = db.Column(db.Boolean, default=True)
    max_tokens = db.Column(db.Integer, default=1000)
    temperature = db.Column(db.Float, default=0.7)
    tools_config = db.Column(db.JSON)  # Configuração de ferramentas em JSON
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    llm_config = db.relationship('LLMConfig', backref='agents')
    creator = db.relationship('Profissional', backref='created_agents')
    prompts = db.relationship('AIPrompt', backref='agent', lazy=True, cascade="all, delete-orphan")
    crew_configs = db.relationship('CrewConfig', secondary='crew_agent_association', back_populates='agents')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'role': self.role,
            'goal': self.goal,
            'backstory': self.backstory,
            'llm_config_id': self.llm_config_id,
            'llm_config': self.llm_config.to_dict() if self.llm_config else None,
            'allow_delegation': self.allow_delegation,
            'max_iter': self.max_iter,
            'verbose': self.verbose,
            'memory': self.memory,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'tools_config': self.tools_config,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'creator_name': self.creator.nome if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'prompts_count': len(self.prompts)
        }

class LLMConfig(db.Model):
    __tablename__ = 'llm_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # groq, openai, anthropic, google, ollama
    model = db.Column(db.String(100), nullable=False)
    api_key_env_var = db.Column(db.String(100))  # Nome da variável de ambiente para API key
    base_url = db.Column(db.String(500))  # URL base para APIs customizadas
    temperature = db.Column(db.Float, default=0.7)
    max_tokens = db.Column(db.Integer, default=1000)
    top_p = db.Column(db.Float, default=1.0)
    frequency_penalty = db.Column(db.Float, default=0.0)
    presence_penalty = db.Column(db.Float, default=0.0)
    timeout = db.Column(db.Integer, default=30)  # Timeout em segundos
    max_retries = db.Column(db.Integer, default=3)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    creator = db.relationship('Profissional', backref='created_llm_configs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'provider': self.provider,
            'model': self.model,
            'api_key_env_var': self.api_key_env_var,
            'base_url': self.base_url,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'creator_name': self.creator.nome if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AIPrompt(db.Model):
    __tablename__ = 'ai_prompts'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    template = db.Column(db.Text, nullable=False)  # Template do prompt com variáveis
    variables = db.Column(db.JSON)  # Lista de variáveis disponíveis no template
    categoria = db.Column(db.String(50))  # medical, analysis, report, etc.
    agent_id = db.Column(db.Integer, db.ForeignKey('ai_agents.id'), nullable=True)
    is_system_prompt = db.Column(db.Boolean, default=False, nullable=False)
    version = db.Column(db.String(20), default='1.0.0')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    creator = db.relationship('Profissional', backref='created_prompts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'template': self.template,
            'variables': self.variables,
            'categoria': self.categoria,
            'agent_id': self.agent_id,
            'agent_nome': self.agent.nome if self.agent else None,
            'is_system_prompt': self.is_system_prompt,
            'version': self.version,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'creator_name': self.creator.nome if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CrewConfig(db.Model):
    __tablename__ = 'crew_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    process = db.Column(db.String(50), default='sequential')  # sequential, hierarchical
    verbose = db.Column(db.Boolean, default=True)
    memory = db.Column(db.Boolean, default=True)
    max_iter = db.Column(db.Integer, default=3)
    share_crew = db.Column(db.Boolean, default=False)  # Se a crew pode ser compartilhada
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    creator = db.relationship('Profissional', backref='created_crews')
    agents = db.relationship('AIAgent', secondary='crew_agent_association', back_populates='crew_configs')
    tasks = db.relationship('CrewTask', backref='crew', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'process': self.process,
            'verbose': self.verbose,
            'memory': self.memory,
            'max_iter': self.max_iter,
            'share_crew': self.share_crew,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'creator_name': self.creator.nome if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'agents': [agent.to_dict() for agent in self.agents],
            'tasks_count': len(self.tasks)
        }

class CrewAgentAssociation(db.Model):
    __tablename__ = 'crew_agent_association'
    
    crew_id = db.Column(db.Integer, db.ForeignKey('crew_configs.id'), primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('ai_agents.id'), primary_key=True)
    order = db.Column(db.Integer, default=0)  # Ordem dos agentes na crew
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CrewTask(db.Model):
    __tablename__ = 'crew_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    crew_id = db.Column(db.Integer, db.ForeignKey('crew_configs.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    expected_output = db.Column(db.Text, nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('ai_agents.id'), nullable=True)  # Agente responsável
    prompt_id = db.Column(db.Integer, db.ForeignKey('ai_prompts.id'), nullable=True)
    context = db.Column(db.JSON)  # Contexto adicional para a tarefa
    async_execution = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)  # Ordem na crew
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    agent = db.relationship('AIAgent', backref='assigned_tasks')
    prompt = db.relationship('AIPrompt', backref='tasks')
    
    def to_dict(self):
        return {
            'id': self.id,
            'crew_id': self.crew_id,
            'nome': self.nome,
            'descricao': self.descricao,
            'expected_output': self.expected_output,
            'agent_id': self.agent_id,
            'agent_nome': self.agent.nome if self.agent else None,
            'prompt_id': self.prompt_id,
            'prompt_nome': self.prompt.nome if self.prompt else None,
            'context': self.context,
            'async_execution': self.async_execution,
            'order': self.order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AIExecutionLog(db.Model):
    __tablename__ = 'ai_execution_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    crew_id = db.Column(db.Integer, db.ForeignKey('crew_configs.id'), nullable=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('ai_agents.id'), nullable=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey('ai_prompts.id'), nullable=True)
    input_data = db.Column(db.JSON)  # Dados de entrada
    output_data = db.Column(db.JSON)  # Dados de saída
    status = db.Column(db.String(20), default='success')  # success, error, partial
    error_message = db.Column(db.Text)
    execution_time_ms = db.Column(db.Integer)  # Tempo de execução em milissegundos
    tokens_used = db.Column(db.Integer)
    cost_estimate = db.Column(db.Float)  # Custo estimado da execução
    llm_config_id = db.Column(db.Integer, db.ForeignKey('llm_configs.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    crew = db.relationship('CrewConfig', backref='execution_logs')
    agent = db.relationship('AIAgent', backref='execution_logs')
    prompt = db.relationship('AIPrompt', backref='execution_logs')
    llm_config = db.relationship('LLMConfig', backref='execution_logs')
    executor = db.relationship('Profissional', backref='ai_executions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'crew_id': self.crew_id,
            'crew_nome': self.crew.nome if self.crew else None,
            'agent_id': self.agent_id,
            'agent_nome': self.agent.nome if self.agent else None,
            'prompt_id': self.prompt_id,
            'prompt_nome': self.prompt.nome if self.prompt else None,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'status': self.status,
            'error_message': self.error_message,
            'execution_time_ms': self.execution_time_ms,
            'tokens_used': self.tokens_used,
            'cost_estimate': self.cost_estimate,
            'llm_config_id': self.llm_config_id,
            'llm_config_nome': self.llm_config.nome if self.llm_config else None,
            'created_by': self.created_by,
            'executor_name': self.executor.nome if self.executor else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
