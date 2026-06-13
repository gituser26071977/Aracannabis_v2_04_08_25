"""
Middleware de Planos - Verificação de Features e Acesso

Este middleware verifica se o usuário tem acesso às features
do sistema baseado no seu plano (Básico, Premium, Enterprise).
"""

from functools import wraps
from flask import request, jsonify, g, redirect, url_for
from models_planos import (
    Assinatura, 
    Plano, 
    get_plano_do_usuario, 
    usuario_tem_feature
)


def get_current_user_plano():
    """Obtém o plano do usuário atual"""
    if not hasattr(g, 'current_user') or not g.current_user:
        return None
    
    usuario_id = g.current_user.get('id')
    if not usuario_id:
        return None
    
    return get_plano_do_usuario(usuario_id)


def requires_feature(feature: str):
    """
    Decorator que verifica se o usuário tem acesso a uma feature específica.
    
    Uso:
        @requires_feature("agentes_sdr")
        def criar_agente():
            ...
    
    Se o usuário não tiver acesso, retorna erro 403 com mensagem de upgrade.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificar se há usuário autenticado
            if not hasattr(g, 'current_user') or not g.current_user:
                return jsonify({
                    "error": "Não autenticado",
                    "code": "UNAUTHORIZED"
                }), 401
            
            usuario_id = g.current_user.get('id')
            if not usuario_id:
                return jsonify({
                    "error": "Usuário não identificado",
                    "code": "INVALID_USER"
                }), 401
            
            # Verificar se usuário tem a feature
            if not usuario_tem_feature(usuario_id, feature):
                # Buscar informações do plano para mensagem
                plano = get_plano_do_usuario(usuario_id)
                plano_nome = plano.titulo if plano else "Básico"
                
                return jsonify({
                    "error": f"Feature '{feature}' não disponível no seu plano",
                    "code": "FEATURE_NOT_ALLOWED",
                    "current_plan": plano_nome,
                    "upgrade_url": "/planos",
                    "message": f"Faça upgrade para {plano_nome} ou superior para acessar esta funcionalidade."
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def requires_plan(plan_name: str):
    """
    Decorator que verifica se o usuário tem um plano específico ou superior.
    
    Uso:
        @requires_plan("premium")
        def acessar_dashboard():
            ...
    
    Planos Hierarchy: basic < premium < enterprise
    """
    plan_hierarchy = {"basico": 0, "premium": 1, "enterprise": 2}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user') or not g.current_user:
                return jsonify({
                    "error": "Não autenticado",
                    "code": "UNAUTHORIZED"
                }), 401
            
            usuario_id = g.current_user.get('id')
            if not usuario_id:
                return jsonify({
                    "error": "Usuário não identificado",
                    "code": "INVALID_USER"
                }), 401
            
            plano = get_plano_do_usuario(usuario_id)
            
            if not plano:
                return jsonify({
                    "error": "Você não possui um plano ativo",
                    "code": "NO_PLAN",
                    "upgrade_url": "/planos"
                }), 403
            
            user_plan_level = plan_hierarchy.get(plano.nome, -1)
            required_level = plan_hierarchy.get(plan_name, 99)
            
            if user_plan_level < required_level:
                return jsonify({
                    "error": f"Plano '{plan_name}' ou superior necessário",
                    "code": "PLAN_REQUIRED",
                    "current_plan": plano.titulo,
                    "required_plan": plan_name.title(),
                    "upgrade_url": "/planos"
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def add_plan_info_to_response(f):
    """
    Decorator que adiciona informações do plano à resposta.
    
    Uso:
        @add_plan_info_to_response
        def get_dashboard_data():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Adicionar info do plano se existir
        plano = get_current_user_plano()
        if plano:
            if isinstance(response, tuple):
                data, status = response[0], response[1] if len(response) > 1 else 200
                if isinstance(data, dict):
                    data['_plan_info'] = {
                        'nome': plano.nome,
                        'titulo': plano.titulo,
                        'features': {
                            'permite_ia': plano.permite_ia,
                            'permite_agentes': plano.permite_agentes,
                            'permite_vsf': plano.permite_vsf,
                            'permite_reconhecimento_facial': plano.permite_reconhecimento_facial,
                            'permite_metricas_fluxo': plano.permite_metricas_fluxo,
                        }
                    }
                return data, status
            elif isinstance(response, dict):
                response['_plan_info'] = {
                    'nome': plano.nome,
                    'titulo': plano.titulo,
                    'features': {
                        'permite_ia': plano.permite_ia,
                        'permite_agentes': plano.permite_agentes,
                        'permite_vsf': plano.permite_vsf,
                        'permite_reconhecimento_facial': plano.permite_reconhecimento_facial,
                        'permite_metricas_fluxo': plano.permite_metricas_fluxo,
                    }
                }
        
        return response
    return decorated_function


def check_plan_middleware(app):
    """
    Registra o middleware global de verificação de planos.
    
    Este middleware é executado antes de cada request e verifica
    se o usuário tem acesso às features necessárias.
    """
    
    @app.before_request
    def verify_plan_access():
        """Verifica acesso baseado no plano antes de cada request"""
        
        # Rotas que não precisam de verificação
        public_routes = [
            '/', '/login', '/cadastro', '/planos', '/api/status',
            '/api/auth', '/api/planos',  # Listar planos é público
            '/static', '/favicon.ico'
        ]
        
        # Verificar se rota é pública
        path = request.path
        for public_route in public_routes:
            if path.startswith(public_route):
                return None
        
        # Verificar autenticação
        if not hasattr(g, 'current_user') or not g.current_user:
            return None  # Deixe o auth middleware cuidar disso
        
        # Verificar trial expirado
        usuario_id = g.current_user.get('id')
        if not usuario_id:
            return None
        
        assinatura = Assinatura.query.filter_by(
            usuario_id=usuario_id
        ).filter(
            Assinatura.status.in_(["ativa", "trial"])
        ).first()
        
        if assinatura and assinatura.status == "trial" and assinatura.trial_expirou():
            # Trial expirou - verificar se quer redirecionar para upgrade
            # Por ora, apenas adiciona warning na response
            pass
        
        return None  # Continua normalmente


def register_plan_middleware(app):
    """Função de registro do middleware de planos"""
    check_plan_middleware(app)
    print("✅ Plan middleware registered")


# ──────────────────────────────────────────────────────────────
# HELPERS PARA FRONTEND
# ──────────────────────────────────────────────────────────────

def get_features_disponiveis(usuario_id: int) -> dict:
    """Retorna as features disponíveis para o usuário"""
    plano = get_plano_do_usuario(usuario_id)
    
    if not plano:
        return {
            "basico": True,  # Todos têm acesso ao básico
            "premium": False,
            "enterprise": False,
            "features": {
                "agentes_sdr": False,
                "chatbot_ia": False,
                "evolucao_ia": False,
                "vsf": False,
                "reconhecimento_facial": False,
                "metricas_fluxo": False,
            }
        }
    
    return {
        "basico": True,
        "premium": plano.nome in ["premium", "enterprise"],
        "enterprise": plano.nome == "enterprise",
        "features": {
            "agentes_sdr": plano.permite_agentes,
            "chatbot_ia": plano.permite_chatbot,
            "evolucao_ia": plano.permite_evolucao_ia,
            "vsf": plano.permite_vsf,
            "reconhecimento_facial": plano.permite_reconhecimento_facial,
            "metricas_fluxo": plano.permite_metricas_fluxo,
        },
        "plano_nome": plano.titulo,
        "limites": {
            "max_agentes": plano.max_agentes,
            "max_usuarios": plano.max_usuarios,
        }
    }


def pode_acessar(usuario_id: int, feature: str) -> bool:
    """Verifica se o usuário pode acessar uma feature específica"""
    return usuario_tem_feature(usuario_id, feature)


def quantidade_agentes_disponivel(usuario_id: int) -> int:
    """Retorna quantos agentes o usuário pode criar"""
    plano = get_plano_do_usuario(usuario_id)
    
    if not plano:
        return 0  # Básico não tem agentes
    
    if plano.max_agentes == 0:
        return float('inf')  # Ilimitado
    
    return plano.max_agentes