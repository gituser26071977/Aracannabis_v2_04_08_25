"""
Rotas para cadastro de profissionais
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
from models import db, Profissional, SolicitacoesCadastro
import re
import secrets
import string
from datetime import datetime, timedelta
from services.email_service import EmailService
from sqlalchemy.exc import IntegrityError

email_service = EmailService()

cadastro_profissionais_bp = Blueprint('cadastro_profissionais', __name__)

def validar_crm(crm, uf):
    """Validar formato do CRM"""
    return crm and uf and crm.isdigit() and 4 <= len(crm) <= 6 and len(uf) == 2

def validar_email(email):
    """Validar formato do email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def gerar_senha_temporaria():
    """Gerar senha temporária segura"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(12))

@cadastro_profissionais_bp.route('/solicitar-cadastro', methods=['POST'])
def solicitar_cadastro():
    """Solicitar cadastro de novo profissional"""
    try:
        data = request.get_json()
        required_fields = ['nome', 'email', 'crm', 'uf_crm']
        if not all(field in data and data[field] for field in required_fields):
            return jsonify({'success': False, 'error': 'Todos os campos obrigatórios devem ser preenchidos.'}), 400

        nome = data['nome'].strip()
        email = data['email'].strip().lower()
        crm = data['crm'].strip()
        uf_crm = data['uf_crm'].strip().upper()

        if len(nome) < 2:
            return jsonify({'success': False, 'error': 'Nome deve ter pelo menos 2 caracteres'}), 400
        if not validar_email(email):
            return jsonify({'success': False, 'error': 'Email inválido'}), 400
        if not validar_crm(crm, uf_crm):
            return jsonify({'success': False, 'error': 'CRM ou UF inválidos'}), 400

        if SolicitacoesCadastro.query.filter_by(email=email).first() or Profissional.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email já cadastrado'}), 409
        if SolicitacoesCadastro.query.filter_by(crm=crm, uf_crm=uf_crm).first() or Profissional.query.filter_by(crm=crm, uf_crm=uf_crm).first():
            return jsonify({'success': False, 'error': 'CRM já cadastrado'}), 409

        nova_solicitacao = SolicitacoesCadastro(
            nome=nome, email=email, crm=crm, uf_crm=uf_crm,
            telefone=data.get('telefone', '').strip(),
            especialidade=data.get('especialidade', '').strip(),
            instituicao=data.get('instituicao', '').strip()
        )
        db.session.add(nova_solicitacao)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Solicitação enviada.', 'id': nova_solicitacao.id}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Dados duplicados.'}), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro: {e}")
        return jsonify({'success': False, 'error': 'Erro interno.'}), 500

@cadastro_profissionais_bp.route('/listar-solicitacoes', methods=['GET'])
def listar_solicitacoes():
    try:
        solicitacoes = SolicitacoesCadastro.query.order_by(SolicitacoesCadastro.data_solicitacao.desc()).all()
        return jsonify({'success': True, 'solicitacoes': [s.to_dict() for s in solicitacoes]})
    except Exception as e:
        current_app.logger.error(f"Erro: {e}")
        return jsonify({'success': False, 'error': 'Erro interno.'}), 500

@cadastro_profissionais_bp.route('/aprovar-solicitacao/<int:solicitacao_id>', methods=['POST'])
def aprovar_solicitacao(solicitacao_id):
    try:
        solicitacao = SolicitacoesCadastro.query.get(solicitacao_id)
        if not solicitacao or solicitacao.status != 'pendente':
            return jsonify({'success': False, 'error': 'Solicitação inválida.'}), 404

        # Gerar credenciais
        senha_temporaria = gerar_senha_temporaria()
        usuario_base = solicitacao.email.split('@')[0]
        usuario = usuario_base
        contador = 1
        while Profissional.query.filter_by(usuario=usuario).first():
            usuario = f"{usuario_base}{contador}"
            contador += 1

        novo_profissional = Profissional(
            nome=solicitacao.nome, 
            crm=solicitacao.crm, 
            uf_crm=solicitacao.uf_crm,
            usuario=usuario, 
            senha=generate_password_hash(senha_temporaria), 
            email=solicitacao.email,
            telefone=solicitacao.telefone, 
            especialidade=solicitacao.especialidade, 
            instituicao=solicitacao.instituicao,
            ativo=True, 
            tipo_conta='temporaria', 
            data_expiracao=datetime.now() + timedelta(days=7)
        )
        db.session.add(novo_profissional)

        solicitacao.status = 'aprovada'
        solicitacao.data_aprovacao = datetime.now()
        # solicitacao.aprovado_por = admin_id # Implementar com autenticação de admin

        db.session.commit()

        email_service.send_approval_email(solicitacao.email, solicitacao.nome, usuario, senha_temporaria, novo_profissional.data_expiracao)

        return jsonify({'success': True, 'message': 'Solicitação aprovada.'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro: {e}")
        return jsonify({'success': False, 'error': 'Erro interno.'}), 500

@cadastro_profissionais_bp.route('/rejeitar-solicitacao/<int:solicitacao_id>', methods=['POST'])
def rejeitar_solicitacao(solicitacao_id):
    try:
        solicitacao = SolicitacoesCadastro.query.get(solicitacao_id)
        if not solicitacao or solicitacao.status != 'pendente':
            return jsonify({'success': False, 'error': 'Solicitação inválida.'}), 404

        data = request.get_json()
        observacoes = data.get('observacoes', '')

        solicitacao.status = 'rejeitada'
        solicitacao.observacoes = observacoes
        # solicitacao.aprovado_por = admin_id # Implementar com autenticação de admin

        db.session.commit()

        email_service.send_rejection_email(solicitacao.email, solicitacao.nome, observacoes)

        return jsonify({'success': True, 'message': 'Solicitação rejeitada.'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro: {e}")
        return jsonify({'success': False, 'error': 'Erro interno.'}), 500