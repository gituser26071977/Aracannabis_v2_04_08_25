"""
Sistema de Feature Flags para SIAP
Permite ativar/desativar funcionalidades por ambiente, tenant ou percentual.
"""
import os
import json
from datetime import datetime
from models import db
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text


class FeatureFlag(db.Model):
    __tablename__ = 'feature_flags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    enabled = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)
    rollout_percentage = Column(Integer, default=100, nullable=False)  # 0-100
    allowed_tenants = Column(Text, nullable=True)  # JSON list de tenant_ids
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'enabled': self.enabled,
            'description': self.description,
            'rollout_percentage': self.rollout_percentage,
            'allowed_tenants': json.loads(self.allowed_tenants) if self.allowed_tenants else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class FeatureFlagService:
    """Serviço centralizado de feature flags."""
    
    # Features da Fase 1
    FEATURES = {
        'new_billing_v2': {
            'description': 'Novo sistema de billing com cobrança real',
            'default': False,
        },
        'recurring_payments': {
            'description': 'Cobrança recorrente automática',
            'default': False,
        },
        'subscription_block': {
            'description': 'Bloqueio de acesso por inadimplência',
            'default': False,
        },
        'plan_enforcement': {
            'description': 'Enforcement de limites do plano',
            'default': False,
        },
        'email_verification': {
            'description': 'Verificação obrigatória de email',
            'default': False,
        },
        'onboarding_wizard': {
            'description': 'Wizard de onboarding para novos usuários',
            'default': False,
        },
        'trial_banner': {
            'description': 'Banner de contagem regressiva do trial',
            'default': False,
        },
        'sga_catalog_extraction': {
            'description': 'Extração de catálogo por IA (SGA)',
            'default': False,
        },
        'multi_payment_provider': {
            'description': 'Suporte a múltiplos provedores de pagamento',
            'default': False,
        },
    }
    
    @classmethod
    def init_defaults(cls):
        """Cria feature flags padrão se não existirem."""
        for name, config in cls.FEATURES.items():
            existing = FeatureFlag.query.filter_by(name=name).first()
            if not existing:
                flag = FeatureFlag(
                    name=name,
                    enabled=config['default'],
                    description=config['description'],
                )
                db.session.add(flag)
        db.session.commit()
    
    @classmethod
    def is_enabled(cls, name, tenant_id=None, user_id=None):
        """
        Verifica se uma feature está habilitada.
        
        Args:
            name: nome da feature
            tenant_id: opcional, para verificar por tenant
            user_id: opcional, para rollout percentual
        
        Returns:
            bool
        """
        # Ambiente de desenvolvimento: todas ativas
        if os.getenv('FLASK_ENV') == 'development' and os.getenv('ENABLE_ALL_FEATURES') == 'true':
            return True
        
        flag = FeatureFlag.query.filter_by(name=name).first()
        if not flag:
            return False
        
        if not flag.enabled:
            return False
        
        # Verificar tenant específico
        if tenant_id and flag.allowed_tenants:
            allowed = json.loads(flag.allowed_tenants)
            if allowed and tenant_id not in allowed:
                return False
        
        # Verificar rollout percentual
        if flag.rollout_percentage < 100 and user_id:
            import hashlib
            hash_val = int(hashlib.md5(f"{name}:{user_id}".encode()).hexdigest(), 16)
            user_percentile = hash_val % 100
            if user_percentile >= flag.rollout_percentage:
                return False
        
        return True
    
    @classmethod
    def enable(cls, name):
        """Ativa uma feature."""
        flag = FeatureFlag.query.filter_by(name=name).first()
        if flag:
            flag.enabled = True
            db.session.commit()
            return True
        return False
    
    @classmethod
    def disable(cls, name):
        """Desativa uma feature."""
        flag = FeatureFlag.query.filter_by(name=name).first()
        if flag:
            flag.enabled = False
            db.session.commit()
            return True
        return False
    
    @classmethod
    def set_rollout(cls, name, percentage):
        """Define rollout percentual (0-100)."""
        flag = FeatureFlag.query.filter_by(name=name).first()
        if flag:
            flag.rollout_percentage = max(0, min(100, percentage))
            db.session.commit()
            return True
        return False
    
    @classmethod
    def list_all(cls):
        """Lista todas as features e seus status."""
        flags = FeatureFlag.query.all()
        return {f.name: f.to_dict() for f in flags}


def feature_required(name):
    """Decorator para rotas que exigem feature flag ativa."""
    from functools import wraps
    from flask import jsonify
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_jwt_extended import get_jwt_identity
            user_id = get_jwt_identity()
            tenant_id = getattr(g, 'current_tenant_id', None) if 'g' in globals() else None
            
            if not FeatureFlagService.is_enabled(name, tenant_id=tenant_id, user_id=user_id):
                return jsonify({
                    'error': 'Feature não disponível',
                    'feature': name,
                    'message': 'Esta funcionalidade está em desenvolvimento ou não está incluída no seu plano.'
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
