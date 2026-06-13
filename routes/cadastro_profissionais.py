"""
Rotas para cadastro de profissionais
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
from models import db, Profissional, SolicitacoesCadastro, ProfissionalRole
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

        tipo_vinculo = data.get('tipo_vinculo', 'pessoal')
        associacao_id = data.get('associacao_id') if data.get('associacao_id') != '' else None
        convite_token = (data.get('convite_token') or '').strip() or None
        instituicao = data.get('instituicao', '').strip()

        if convite_token:
            from association.models import ConviteProfissionalInstituicao

            convite = ConviteProfissionalInstituicao.query.filter_by(token=convite_token).first()
            if not convite or not convite.is_valid():
                return jsonify({'success': False, 'error': 'Convite inválido, expirado ou já utilizado.'}), 400
            if convite.email and convite.email.lower() != email:
                return jsonify({'success': False, 'error': 'Este convite foi emitido para outro email.'}), 400

            tipo_vinculo = 'convite'
            associacao_id = convite.associacao_id
            instituicao = convite.associacao.nome if convite.associacao else instituicao

        nova_solicitacao = SolicitacoesCadastro(
            nome=nome, email=email, crm=crm, uf_crm=uf_crm,
            telefone=data.get('telefone', '').strip(),
            especialidade=data.get('especialidade', '').strip(),
            instituicao=instituicao,
            # Novos campos para escolha de vínculo
            tipo_vinculo=tipo_vinculo,
            associacao_id=associacao_id,
            convite_token=convite_token
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
            aprovado_por=None,
            data_aprovacao=datetime.now(),
            onboarding_completed=True  # Usuário já passou pelo cadastro completo
        )
        db.session.add(novo_profissional)
        db.session.flush()

        # Workspace Linking logic
        try:
            from association.models import Associacao
            from models_extra import UsuarioAssociacao
            
            tipo_vinculo = getattr(solicitacao, 'tipo_vinculo', 'pessoal')
            target_assoc = None
            convite = None

            if tipo_vinculo == 'convite' and solicitacao.convite_token:
                from association.models import ConviteProfissionalInstituicao

                convite = ConviteProfissionalInstituicao.query.filter_by(token=solicitacao.convite_token).first()
                if not convite or not convite.is_valid():
                    raise ValueError('Convite institucional inválido, expirado ou já utilizado.')
                target_assoc = convite.associacao
                target_assoc_role = convite.role or 'member'

            elif tipo_vinculo == 'existente' and solicitacao.associacao_id:
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
                link = UsuarioAssociacao.query.filter_by(
                    profissional_id=novo_profissional.id,
                    associacao_id=target_assoc.id
                ).first()
                if not link:
                    link = UsuarioAssociacao(
                        profissional_id=novo_profissional.id,
                        associacao_id=target_assoc.id,
                        role=target_assoc_role,
                        status='active'
                    )
                    db.session.add(link)
                if convite:
                    convite.status = 'accepted'
                    convite.accepted_at = datetime.utcnow()

        except Exception:
            raise

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


# ═══════════════════════════════════════════════════════════════════════
# FASE 2 — Cadastro de STAFF via Convite (Secretária / Gestor)
# ═══════════════════════════════════════════════════════════════════════

def processar_aceitacao_staff(convite_token, nome, email, telefone, senha=None):
    """
    Processa a aceitação de um convite de STAFF.

    Fluxo:
      1. Valida convite (pendente, não expirado, não revogado, invite_type='staff')
      2. Cria Profissional com role='secretary' (ou role do convite) — SEM CRM/UF
      3. Cria UsuarioAssociacao vinculando à instituição do convite
      4. Marca convite como 'accepted'
      5. Gera senha temporária se não fornecida
      6. Envia email com credenciais
      7. Registra AuditLog

    Returns:
        (dict_response, status_code)
    """
    from association.models import ConviteProfissionalInstituicao
    from models_extra import UsuarioAssociacao, create_audit_entry

    convite = ConviteProfissionalInstituicao.query.filter_by(token=convite_token).first()
    if not convite:
        return {'success': False, 'error': 'Convite não encontrado.'}, 404
    if not convite.is_valid():
        return {'success': False, 'error': 'Convite expirado, já utilizado ou revogado.'}, 410
    if convite.invite_type != ConviteProfissionalInstituicao.INVITE_TYPE_STAFF:
        return {'success': False, 'error': 'Este convite não é para staff. Use o cadastro de profissional.'}, 400

    # Email deve bater com o convite (se convite especificou email)
    if convite.email and convite.email.lower() != email.lower():
        return {'success': False, 'error': 'Este convite foi emitido para outro email.'}, 403

    # Verificar se já existe Profissional com este email
    existing = Profissional.query.filter_by(email=email.lower()).first()
    if existing:
        return {'success': False, 'error': 'Já existe um usuário cadastrado com este email. Faça login ou use outro email.'}, 409

    # Determinar role
    target_role = convite.role if convite.role in ProfissionalRole.STAFF_ROLES or convite.role == 'admin' else ProfissionalRole.SECRETARY
    target_role = ProfissionalRole.normalize(target_role)

    # Gerar senha
    senha_final = senha if senha else gerar_senha_temporaria()
    if not senha or len(senha) < 8:
        # Política mínima: 8 caracteres; gera temp
        senha_final = gerar_senha_temporaria()

    # Gerar usuário único
    usuario_base = email.split('@')[0]
    usuario = usuario_base
    contador = 1
    while Profissional.query.filter_by(usuario=usuario).first():
        usuario = f"{usuario_base}{contador}"
        contador += 1

    # Criar Profissional
    novo_profissional = Profissional(
        nome=nome.strip(),
        crm=None,        # Staff não tem CRM
        uf_crm=None,     # Staff não tem UF
        usuario=usuario,
        email=email.lower().strip(),
        senha=generate_password_hash(senha_final),
        role=target_role,
        data_expiracao=datetime.now() + timedelta(days=7),
        status_cadastro='aprovado',   # Convite já é aprovação do gestor
        data_aprovacao=datetime.now(),
        email_verified=True,          # Email foi validado pelo convite
        onboarding_completed=True,    # Onboarding via fluxo simplificado
    )
    db.session.add(novo_profissional)
    db.session.flush()

    # Criar vínculo com a instituição
    link = UsuarioAssociacao(
        profissional_id=novo_profissional.id,
        associacao_id=convite.associacao_id,
        role=convite.role,  # mesmo role do convite (secretary/manager/admin/member)
        status='active',
    )
    db.session.add(link)

    # Marcar convite como aceito
    convite.status = 'accepted'
    convite.accepted_at = datetime.utcnow()
    convite.accepted_by_user_id = novo_profissional.id

    db.session.commit()

    # Audit log
    try:
        create_audit_entry(
            tenant_id=convite.associacao_id,
            user_id=novo_profissional.id,
            action='invite.accept',
            resource_type='convite',
            resource_id=str(convite.id),
            details={
                'invite_type': 'staff',
                'role': target_role,
                'profissional_id': novo_profissional.id,
                'association_id': convite.associacao_id,
            },
        )
    except Exception as exc:
        current_app.logger.warning("Falha ao criar audit entry (invite.accept): %s", exc)

    # Email de boas-vindas com credenciais
    try:
        email_service.send_staff_welcome_email(
            email=novo_profissional.email,
            nome=novo_profissional.nome,
            usuario=novo_profissional.usuario,
            senha_temporaria=senha_final,
            instituicao_nome=convite.associacao.nome if convite.associacao else '',
            data_expiracao=novo_profissional.data_expiracao,
        )
    except Exception as exc:
        current_app.logger.warning("Falha ao enviar email de boas-vindas staff: %s", exc)

    return {
        'success': True,
        'message': 'Conta de staff criada com sucesso!',
        'usuario': usuario,
        'profissional_id': novo_profissional.id,
        'role': target_role,
        'associacao_id': convite.associacao_id,
        'associacao_nome': convite.associacao.nome if convite.associacao else None,
        'data_expiracao': novo_profissional.data_expiracao.isoformat() if novo_profissional.data_expiracao else None,
    }, 201


@cadastro_profissionais_bp.route('/solicitar-cadastro-staff', methods=['POST'])
def solicitar_cadastro_staff():
    """
    Aceita um convite de STAFF e cria a conta.

    Body (JSON):
      {
        "convite_token": "...",
        "nome": "Maria Secretária",
        "email": "maria@clinica.com",
        "telefone": "(11) 99999-9999",   # opcional
        "senha": "minhaSenha123"          # opcional; se não fornecida, sistema gera
      }

    Não exige CRM/UF (sem conselho de classe para staff).
    Endpoint PÚBLICO (não exige @jwt_required) — proteção vem do token do convite.
    """
    try:
        data = request.get_json() or {}
        required = ['convite_token', 'nome', 'email']
        missing = [f for f in required if not (data.get(f) or '').strip()]
        if missing:
            return jsonify({
                'success': False,
                'error': f'Campos obrigatórios: {", ".join(missing)}',
            }), 400

        convite_token = (data.get('convite_token') or '').strip()
        nome = (data.get('nome') or '').strip()
        email = (data.get('email') or '').strip().lower()
        telefone = (data.get('telefone') or '').strip() or None
        senha = data.get('senha')  # opcional

        if len(nome) < 2:
            return jsonify({'success': False, 'error': 'Nome deve ter pelo menos 2 caracteres'}), 400

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'success': False, 'error': 'Email inválido'}), 400

        # Se o usuário forneceu senha, validar política mínima
        if senha and len(senha) < 8:
            return jsonify({
                'success': False,
                'error': 'Senha deve ter no mínimo 8 caracteres. Deixe vazio para gerar uma temporária.',
            }), 400

        result, status_code = processar_aceitacao_staff(
            convite_token=convite_token,
            nome=nome,
            email=email,
            telefone=telefone,
            senha=senha,
        )
        return jsonify(result), status_code

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Dados duplicados. Este email ou usuário já está em uso.',
        }), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro em solicitar_cadastro_staff: {e}")
        return jsonify({'success': False, 'error': 'Erro interno.'}), 500


# ═══════════════════════════════════════════════════════════════════════
# FASE 2 — Adaptar processar_aprovacao para suportar STAFF
# ═══════════════════════════════════════════════════════════════════════

def processar_aprovacao(solicitacao_id):
    """
    Lógica centralizada de aprovação para uso na rota e na auto-aprovação.
    Inclui suporte a STAFF (Fase 2): quando o convite é do tipo 'staff',
    cria Profissional com role='secretary' e pula ConfiguracaoPrescricao.
    """
    try:
        from services.whatsapp_service import WhatsAppService
        from models_extra import UsuarioAssociacao
        from association.models import Associacao, ConviteProfissionalInstituicao
        whatsapp_service = WhatsAppService()

        # Re-query para garantir sessão
        solicitacao = SolicitacoesCadastro.query.get(solicitacao_id)
        if not solicitacao or solicitacao.status != 'pendente':
            return {'success': False, 'error': 'Solicitação inválida'}, 404

        # Detectar tipo via convite
        convite = None
        if getattr(solicitacao, 'convite_token', None):
            convite = ConviteProfissionalInstituicao.query.filter_by(token=solicitacao.convite_token).first()

        is_staff = (
            convite is not None
            and convite.invite_type == ConviteProfissionalInstituicao.INVITE_TYPE_STAFF
        )

        # Gerar credenciais
        senha_temporaria = gerar_senha_temporaria()
        usuario_base = solicitacao.email.split('@')[0]
        usuario = usuario_base
        contador = 1
        while Profissional.query.filter_by(usuario=usuario).first():
            usuario = f"{usuario_base}{contador}"
            contador += 1

        # Criar profissional
        if is_staff:
            # Staff: SEM CRM/UF, role=convite.role
            target_role = convite.role if convite.role in (ProfissionalRole.SECRETARY, ProfissionalRole.MANAGER, 'admin') else ProfissionalRole.SECRETARY
            novo_profissional = Profissional(
                nome=solicitacao.nome,
                crm=None,
                uf_crm=None,
                usuario=usuario,
                email=solicitacao.email,
                senha=generate_password_hash(senha_temporaria),
                role=ProfissionalRole.normalize(target_role),
                data_expiracao=datetime.now() + timedelta(days=7),
                status_cadastro='aprovado',
                data_aprovacao=datetime.now(),
                onboarding_completed=True,
                email_verified=True,
            )
        else:
            # Profissional: com CRM/UF, role='profissional'
            novo_profissional = Profissional(
                nome=solicitacao.nome,
                crm=solicitacao.crm,
                uf_crm=solicitacao.uf_crm,
                usuario=usuario,
                email=solicitacao.email,
                senha=generate_password_hash(senha_temporaria),
                role=ProfissionalRole.PROFISSIONAL,
                data_expiracao=datetime.now() + timedelta(days=7),
                status_cadastro='aprovado',
                aprovado_por=None,
                data_aprovacao=datetime.now(),
                onboarding_completed=True,
            )
        db.session.add(novo_profissional)
        db.session.flush()

        # Workspace Linking logic
        try:
            tipo_vinculo = getattr(solicitacao, 'tipo_vinculo', 'pessoal')
            target_assoc = None
            target_assoc_role = None

            if tipo_vinculo == 'convite' and solicitacao.convite_token:
                if not convite or not convite.is_valid():
                    raise ValueError('Convite institucional inválido, expirado ou já utilizado.')
                target_assoc = convite.associacao
                target_assoc_role = convite.role or 'member'

            elif tipo_vinculo == 'existente' and solicitacao.associacao_id:
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
                    nome=nome_assoc, slug=slug, cnpj=solicitacao.crm or solicitacao.cpf or f"WS-{novo_profissional.id}", ativo=True
                )
                db.session.add(target_assoc)
                db.session.flush()
                target_assoc_role = 'admin'

            if target_assoc:
                link = UsuarioAssociacao.query.filter_by(
                    profissional_id=novo_profissional.id,
                    associacao_id=target_assoc.id
                ).first()
                if not link:
                    link = UsuarioAssociacao(
                        profissional_id=novo_profissional.id,
                        associacao_id=target_assoc.id,
                        role=target_assoc_role or 'member',
                        status='active'
                    )
                    db.session.add(link)
                if convite:
                    convite.status = 'accepted'
                    convite.accepted_at = datetime.utcnow()
                    convite.accepted_by_user_id = novo_profissional.id

        except Exception:
            raise

        # Criar configuração de prescrição padrão — APENAS para profissionais clínicos
        if not is_staff:
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
            if is_staff:
                # Email específico de staff
                email_service.send_staff_welcome_email(
                    email=solicitacao.email,
                    nome=solicitacao.nome,
                    usuario=usuario,
                    senha_temporaria=senha_temporaria,
                    instituicao_nome=convite.associacao.nome if convite and convite.associacao else '',
                    data_expiracao=novo_profissional.data_expiracao,
                )
            else:
                email_service.send_approval_email(
                    solicitacao.email, solicitacao.nome, usuario, senha_temporaria, novo_profissional.data_expiracao
                )
            whatsapp_service.notify_doctor_approval(solicitacao.telefone, solicitacao.nome)
        except Exception:
            pass

        return {'success': True, 'message': 'Aprovado', 'role': novo_profissional.role}, 200

    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}, 500
