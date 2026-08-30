"""Middleware de tenant: associa cada profissional ao seu próprio consultório.

Cada profissional tem UM consultório (Associacao) criado automaticamente
no cadastro. O tenant é resolvido de forma transparente — o usuário
nunca interage com o conceito de "associação".
"""

from flask import request, g
from models_extra import UsuarioAssociacao
from models import Profissional, Associacao, db
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
import logging

logger = logging.getLogger(__name__)


def _garantir_associacao(profissional_id: int) -> Associacao | None:
    """Garante que o profissional tenha um associacao/consultorio.
    
    Se não tiver, cria uma automaticamente com base no nome do profissional.
    Retorna o Associacao ou None se o profissional não for encontrado.
    """
    profissional = Profissional.query.get(profissional_id)
    if not profissional:
        return None

    link = UsuarioAssociacao.query.filter_by(
        profissional_id=profissional_id, status='active'
    ).first()
    if link and link.associacao:
        return link.associacao

    nome = profissional.nome or profissional.usuario or f"Profissional {profissional_id}"
    slug = "".join(c for c in nome.lower() if c.isalnum() or c == ' ').replace(' ', '-')[:50]
    
    import time
    cnpj_placeholder = f"AUTO-{profissional_id}-{int(time.time())}"
    
    assoc = Associacao(nome=nome, slug=slug, cnpj=cnpj_placeholder, ativo=True)
    db.session.add(assoc)
    db.session.flush()

    vinculo = UsuarioAssociacao(
        profissional_id=profissional_id,
        associacao_id=assoc.id,
        role='admin',
        status='active',
    )
    db.session.add(vinculo)
    db.session.commit()
    
    logger.info(f"Associacao auto-criada ID={assoc.id} para profissional {profissional_id}")
    return assoc


def register_tenant_middleware(app):
    @app.before_request
    def check_tenant():
        g.is_superadmin = False
        g.current_association = None
        g.user_role = None
        
        if request.method == 'OPTIONS':
            return
            
        if request.path.startswith('/api/auth') or \
           request.path.startswith('/api/status') or \
           request.path.startswith('/api/public') or \
           request.path.startswith('/agendar'):
            return

        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
            
            if not identity:
                return

            user_id = int(identity)
            profissional = Profissional.query.get(user_id)
            
            if profissional:
                g.user_role = profissional.role
                if profissional.role == 'superadmin':
                    g.is_superadmin = True
                    g.current_association = None
                    return

            assoc = _garantir_associacao(user_id)
            if assoc:
                g.current_association = assoc

        except Exception as e:
            logger.error(f"Tenant middleware error: {e}")
