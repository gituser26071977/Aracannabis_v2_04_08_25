"""
Rotas para cadastro de profissionais

Suporta múltiplos conselhos de classe (feat/intelligent-import fase I2):
  CRM, CRP, COREN, CRN, CREFITO, NONE (staff sem conselho).
Detecção automática via `conselho_tipo` no payload; default 'CRM' para
compatibilidade com dados legados.
"""
from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
from models import db, Profissional, SolicitacoesCadastro
from services.conselho_validator import (
    validar_conselho,
    normalizar_tipo_conselho,
    CONSELHO_NONE,
    CONSELHO_LABELS,
)
from security_config import (
    limiter,
    SENSITIVE_ENDPOINTS_RATE_LIMIT,
    LOGIN_RATE_LIMIT,
)
import re
import secrets
import string
from datetime import datetime, timedelta
from services.email_service import EmailService
from services.subscription_expiration_service import SubscriptionExpirationService
from sqlalchemy.exc import IntegrityError
import psycopg2

email_service = EmailService()

cadastro_profissionais_bp = Blueprint('cadastro_profissionais', __name__)


def validar_email(email):
    """Validar formato do email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def _is_staff_request(tipo_norm: str) -> bool:
    """Staff (secretária/gestor) não exige conselho de classe."""
    return tipo_norm == CONSELHO_NONE

def gerar_senha_temporaria():
    """Gerar senha temporária segura"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(12))

@cadastro_profissionais_bp.route('/solicitar-cadastro', methods=['POST'])
@limiter.limit(SENSITIVE_ENDPOINTS_RATE_LIMIT)
def solicitar_cadastro():
    """Solicitar cadastro de novo profissional (ou staff, se conselho_tipo='NONE')."""
    try:
        data = request.get_json()
        nome = (data.get('nome') or '').strip()
        email = (data.get('email') or '').strip().lower()

        if not nome or not email:
            return jsonify({'success': False, 'error': 'Nome e email são obrigatórios.'}), 400
        if len(nome) < 2:
            return jsonify({'success': False, 'error': 'Nome deve ter pelo menos 2 caracteres'}), 400
        if not validar_email(email):
            return jsonify({'success': False, 'error': 'Email inválido'}), 400

        # Detecta tipo de conselho (CRM/CRP/COREN/CRN/CREFITO/NONE)
        tipo_bruto = data.get('conselho_tipo', 'CRM')
        tipo_norm = normalizar_tipo_conselho(tipo_bruto)
        crm = (data.get('crm') or '').strip()
        uf_crm = (data.get('uf_crm') or '').strip().upper()

        # Validação unificada via conselho_validator (regex por tipo + UF para COREN)
        resultado = validar_conselho(
            numero=crm,
            uf=uf_crm,
            tipo=tipo_bruto,
        )
        if not resultado['valido']:
            erros = '; '.join(resultado['erros'])
            return jsonify({
                'success': False,
                'error': f"{erros} (conselho: {tipo_norm})",
                'conselho_tipo': tipo_norm,
                'profissao': resultado.get('profissao'),
            }), 400

        if SolicitacoesCadastro.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email já cadastrado'}), 409

        # Staff (conselho_tipo='NONE') não tem CRM/UF — não checar duplicidade por registro
        is_staff = _is_staff_request(tipo_norm)
        if not is_staff and (crm or uf_crm):
            if (SolicitacoesCadastro.query.filter_by(crm=crm, uf_crm=uf_crm).first()
                    or Profissional.query.filter_by(crm=crm, uf_crm=uf_crm).first()):
                return jsonify({'success': False, 'error': 'Registro já cadastrado'}), 409

        nova_solicitacao = SolicitacoesCadastro(
            nome=nome, email=email,
            crm=crm or None,
            uf_crm=uf_crm or None,
            conselho_tipo=tipo_norm,
            telefone=(data.get('telefone') or '').strip(),
            especialidade=(data.get('especialidade') or '').strip(),
            instituicao=(data.get('instituicao') or '').strip(),
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
            from services.telegram_service import telegram_service

            verifier = RegistrationVerificationService()

            verification_result = verifier.verify_registration(nova_solicitacao.id)
            current_app.logger.info(f"Verificação automática: {verification_result['summary']}")

            # Notificar Admin (Dr. Anderson) via Telegram
            telegram_service.notify_admin_new_registration(
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

    except IntegrityError as e:
        db.session.rollback()
        # Diferenciar violação de constraint para mensagens úteis ao cliente
        # (rc.16: o catch genérico "Dados duplicados" mascarava erros de NOT NULL).
        cause = getattr(e, 'orig', None)
        pgcode = getattr(cause, 'pgcode', None) if cause is not None else None
        constraint = getattr(cause, 'constraint_name', None) or getattr(cause, 'diag', {}).get('constraint_name') if cause is not None else None
        if pgcode == '23502':  # not_null_violation
            field = getattr(cause, 'column_name', None) if cause is not None else None
            current_app.logger.error(f"NotNull violation em cadastro: field={field}")
            return jsonify({
                'success': False,
                'error': f"Campo obrigatório não preenchido: {field or 'desconhecido'}."
            }), 400
        if pgcode == '23505':  # unique_violation
            if constraint == 'solicitacoes_cadastro_email_key':
                return jsonify({'success': False, 'error': 'Email já cadastrado'}), 409
            if constraint in ('uq_solicitacao_crm_uf_partial', 'uq_solicitacao_crm_uf'):
                return jsonify({'success': False, 'error': 'Registro já cadastrado'}), 409
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
        from services.telegram_service import telegram_service

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
        # conselho_tipo determina role: NONE → staff, demais → profissional
        conselho_tipo = normalizar_tipo_conselho(
            getattr(solicitacao, 'conselho_tipo', None) or 'CRM'
        )
        role_inicial = (
            'secretary' if conselho_tipo == CONSELHO_NONE else 'profissional'
        )

        novo_profissional = Profissional(
            nome=solicitacao.nome,
            crm=solicitacao.crm,
            uf_crm=solicitacao.uf_crm,
            conselho_tipo=conselho_tipo,
            usuario=usuario,
            email=solicitacao.email,
            senha=generate_password_hash(senha_temporaria),
            role=role_inicial,
            data_expiracao=datetime.now() + timedelta(days=SubscriptionExpirationService.TRIAL_DAYS),
            status_cadastro='aprovado',
            aprovado_por='system',
            data_aprovacao=datetime.now(),
            onboarding_completed=True  # Usuário já passou pelo cadastro completo
        )
        db.session.add(novo_profissional)
        db.session.flush()

        # Workspace Linking logic
        # rc.16: usar instituicao (se preenchida) como nome da clinica
        # em vez do fallback fixo "Consultorio {nome}". Tambem gerar
        # CNPJ placeholder unico (AUTO-<id>-<ts>) em vez de reusar o CRM,
        # que violava Associacao.cnpj UNIQUE NOT NULL. Erros agora sao
        # logados estruturados (em vez de engolidos com `pass`) e usam
        # SAVEPOINT para nao desfazer o INSERT do profissional.
        try:
            sp = db.session.begin_nested()
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

                # rc.16: nome da clinica = instituicao quando preenchida;
                # senao fallback "Consultorio {nome}"
                instituicao = (getattr(solicitacao, 'instituicao', '') or '').strip()
                nome_assoc = instituicao if instituicao else f"Consultorio {solicitacao.nome}"
                # rc.16: CNPJ placeholder unico (AUTO-<prof_id>-<ts>) para
                # nao colidir com CRM de outros profissionais. Usuario
                # podera editar via /association para CNPJ real depois.
                import time as _time
                cnpj_placeholder = f"AUTO-{novo_profissional.id}-{int(_time.time())}"
                target_assoc = Associacao(
                    nome=nome_assoc, slug=slug, cnpj=cnpj_placeholder, ativo=True
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

            sp.commit()
        except IntegrityError as ie:
            sp.rollback()
            current_app.logger.warning(
                f"[cadastro_profissionais] workspace_link_integrity_error: "
                f"prof_id={novo_profissional.id} tipo_vinculo={tipo_vinculo} "
                f"error={getattr(ie, 'orig', ie)}"
            )
        except Exception as e:
            sp.rollback()
            current_app.logger.error(
                f"[cadastro_profissionais] workspace_link_error: "
                f"prof_id={novo_profissional.id} tipo_vinculo={tipo_vinculo} "
                f"error={type(e).__name__}: {e}"
            )

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
            telegram_service.notify_doctor_approval(solicitacao.telefone, solicitacao.nome)
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
@limiter.limit(SENSITIVE_ENDPOINTS_RATE_LIMIT)
def aprovar_solicitacao(solicitacao_id):
    result, status_code = processar_aprovacao(solicitacao_id)
    return jsonify(result), status_code

@cadastro_profissionais_bp.route('/rejeitar-solicitacao/<int:solicitacao_id>', methods=['POST'])
@limiter.limit(SENSITIVE_ENDPOINTS_RATE_LIMIT)
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
