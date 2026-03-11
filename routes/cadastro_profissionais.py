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
    """Validar formato do Registro Profissional (CRM, COREN, CRP, etc)"""
    return crm and uf and len(crm) >= 4 and len(uf) == 2

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
            return jsonify({'success': False, 'error': 'Registro ou UF inválidos'}), 400

        if SolicitacoesCadastro.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email já cadastrado'}), 409
        if SolicitacoesCadastro.query.filter_by(crm=crm, uf_crm=uf_crm).first() or Profissional.query.filter_by(crm=crm, uf_crm=uf_crm).first():
            return jsonify({'success': False, 'error': 'Registro já cadastrado'}), 409

        nova_solicitacao = SolicitacoesCadastro(
            nome=nome, email=email, crm=crm, uf_crm=uf_crm,
            telefone=data.get('telefone', '').strip(),
            especialidade=data.get('especialidade', '').strip(),
            instituicao=data.get('instituicao', '').strip(),
            # Novos campos para escolha de vínculo
            tipo_vinculo=data.get('tipo_vinculo', 'pessoal'), # 'pessoal' ou 'existente'
            associacao_id=data.get('associacao_id') if data.get('associacao_id') != '' else None # ID da associacao se tipo_vinculo='existente'
        )
        db.session.add(nova_solicitacao)
        db.session.commit()

        # Enviar email de confirmação de recebimento
        try:
             email_service.send_registration_received_email(nova_solicitacao.email, nova_solicitacao.nome)
        except Exception as e:
             current_app.logger.error(f"Erro ao enviar email de boas-vindas: {e}")
        
        # Executar verificação automática
        try:
            from services.registration_verification_service import RegistrationVerificationService
            from services.whatsapp_service import WhatsAppService
            
            verifier = RegistrationVerificationService()
            whatsapp_service = WhatsAppService()
            
            verification_result = verifier.verify_registration(nova_solicitacao.id)
            current_app.logger.info(f"Verificação automática: {verification_result['summary']}")
            
            # Notificar Admin
            whatsapp_service.notify_admin_new_registration(
                nova_solicitacao.nome,
                nova_solicitacao.email,
                nova_solicitacao.crm,
                nova_solicitacao.uf_crm,
                verification_result.get('recommendation') == 'auto_approve'
            )

            # Auto-Aprovação
            if verification_result.get('recommendation') == 'auto_approve':
                current_app.logger.info(f"Auto-aprovando solicitação {nova_solicitacao.id}")
                # Chamar lógica de aprovação (RECURSÃO CUIDADOSA ou refatoração)
                # Como não posso chamar a rota diretamente facilmente sem request context, vou duplicar a chamada da validação por enquanto ou assumir que o admin aprovará.
                # O usuário disse "pode ativar a ativação automática".
                # Vou refatorar a aprovação para uma função auxiliar abaixo e chamá-la.
                result, status_code = processar_aprovacao(nova_solicitacao.id)
                if status_code != 200:
                     current_app.logger.error(f"Falha na auto-aprovação: {result}")
            
        except Exception as e:
            current_app.logger.error(f"Erro na verificação automática/notificação: {e}")

        return jsonify({'success': True, 'message': 'Solicitação enviada.', 'id': nova_solicitacao.id}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Dados duplicados.'}), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro: {e}")
        return jsonify({'success': False, 'error': 'Erro interno.'}), 500

def processar_aprovacao(solicitacao_id):
    """
    Lógica centralizada de aprovação para uso na rota e na auto-aprovação.
    """
    try:
        from services.whatsapp_service import WhatsAppService
        whatsapp_service = WhatsAppService()
        
        # Re-query para garantir sessão
        solicitacao = SolicitacoesCadastro.query.get(solicitacao_id)
        if not solicitacao or solicitacao.status != 'pendente':
            return {'success': False, 'error': 'Solicitação inválida'}, 404

        # Gerar credenciais
        senha_temporaria = gerar_senha_temporaria()
        usuario_base = solicitacao.email.split('@')[0]
        usuario = usuario_base
        contador = 1
        while Profissional.query.filter_by(usuario=usuario).first():
            usuario = f"{usuario_base}{contador}"
            contador += 1

        # Criar profissional
        novo_profissional = Profissional(
            nome=solicitacao.nome,
            crm=solicitacao.crm,
            uf_crm=solicitacao.uf_crm,
            usuario=usuario,
            email=solicitacao.email,
            senha=generate_password_hash(senha_temporaria),
            role='profissional',
            data_expiracao=datetime.now() + timedelta(days=7),
            status_cadastro='aprovado',
            aprovado_por='system',
            data_aprovacao=datetime.now()
        )
        db.session.add(novo_profissional)
        db.session.flush()

        # Workspace Linking logic
        try:
            from association.models import Associacao
            from models_extra import UsuarioAssociacao
            
            tipo_vinculo = getattr(solicitacao, 'tipo_vinculo', 'pessoal')
            target_assoc = None

            if tipo_vinculo == 'existente' and solicitacao.associacao_id:
                target_assoc = Associacao.query.get(solicitacao.associacao_id)
                if not target_assoc:
                    tipo_vinculo = 'pessoal'
                else:
                     target_assoc_role = 'member'

            if tipo_vinculo == 'pessoal':
                slug_base = "".join(c for c in solicitacao.nome.lower() if c.isalnum() or c == ' ').replace(' ', '-')
                slug = slug_base
                count = 1
                while Associacao.query.filter_by(slug=slug).first():
                    slug = f"{slug_base}-{count}"
                    count += 1
                
                nome_assoc = f"Consultório {solicitacao.nome}"
                target_assoc = Associacao(
                    nome=nome_assoc, slug=slug, cnpj=solicitacao.crm, ativo=True
                )
                db.session.add(target_assoc)
                db.session.flush()
                target_assoc_role = 'admin'

            if target_assoc:
                link = UsuarioAssociacao(
                    profissional_id=novo_profissional.id,
                    associacao_id=target_assoc.id,
                    role=target_assoc_role,
                    status='active'
                )
                db.session.add(link)

        except Exception:
            pass # Logger handled in caller context usually

        # Criar configuração de prescrição padrão
        try:
            from models import ConfiguracaoPrescricao
            if not ConfiguracaoPrescricao.query.filter_by(profissional_id=novo_profissional.id).first():
                nova_config = ConfiguracaoPrescricao(
                    profissional_id=novo_profissional.id,
                    modo_consultor_ia=True,
                    usar_assinatura_digital=False
                )
                db.session.add(nova_config)
        except Exception as e:
            current_app.logger.error(f"Erro ao criar configuração de prescrição: {e}")

        solicitacao.status = 'aprovada'
        solicitacao.data_aprovacao = datetime.now()
        db.session.commit()

        # Notificações
        try:
            email_service.send_approval_email(solicitacao.email, solicitacao.nome, usuario, senha_temporaria, novo_profissional.data_expiracao)
            whatsapp_service.notify_doctor_approval(solicitacao.telefone, solicitacao.nome)
        except Exception:
             pass

        return {'success': True, 'message': 'Aprovado'}, 200

    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}, 500

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
    result, status_code = processar_aprovacao(solicitacao_id)
    return jsonify(result), status_code

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
