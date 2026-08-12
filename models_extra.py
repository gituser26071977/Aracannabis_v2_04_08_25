from datetime import datetime
from models import db

# Novas models para suportar inventory, pharmacy dispenses e audit

class UsuarioAssociacao(db.Model):
    __tablename__ = 'usuarios_associacoes'

    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='CASCADE'), nullable=False)
    associacao_id = db.Column(db.Integer, db.ForeignKey('associacoes.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String, default='member') # 'admin', 'member', 'viewer'
    status = db.Column(db.String, default='active') # 'active', 'suspended', 'pending'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profissional = db.relationship('Profissional', backref='associacoes_vinculadas')
    associacao = db.relationship('Associacao', back_populates='usuarios_vinculados') # Backref in Associacao needs update or use back_populates if defined there, or just simple backref here.
    # Associacao model already has 'membros' and 'estoque', let's stick to simple relationship here or modify Associacao.
    # Associacao definition: `membros = db.relationship('Membro', backref='associacao', lazy=True)`
    # I will rely on this relationship here to access Assoc from UserAssoc.
    
    __table_args__ = (
        db.UniqueConstraint('profissional_id', 'associacao_id', name='uq_profissional_associacao'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'profissional_id': self.profissional_id,
            'associacao_id': self.associacao_id,
            'associacao_nome': self.associacao.nome if self.associacao else None,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id', ondelete='CASCADE'))
    lote = db.Column(db.String(100))
    quantidade = db.Column(db.Integer, default=0, nullable=False)
    localizacao = db.Column(db.String(255))
    validade = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    produto = db.relationship('Produto', backref='inventory_items')

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'produto_id': self.produto_id,
            'produto_nome': self.produto.nome if self.produto else None,
            'lote': self.lote,
            'quantidade': self.quantidade,
            'localizacao': self.localizacao,
            'validade': self.validade.isoformat() if self.validade else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PharmacyDispense(db.Model):
    __tablename__ = 'pharmacy_dispenses'

    id = db.Column(db.Integer, primary_key=True)
    prescricao_id = db.Column(db.Integer, db.ForeignKey('prescricoes.id', ondelete='SET NULL'))
    tenant_id = db.Column(db.Integer, nullable=False)
    dispensado_por = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='SET NULL'))
    itens = db.Column(db.JSON, nullable=False)  # lista de {produto_id, quantidade, lote}
    observacoes = db.Column(db.Text)
    data_dispensacao = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prescricao = db.relationship('Prescricao', foreign_keys=[prescricao_id], backref='dispensas')
    profissional = db.relationship('Profissional', foreign_keys=[dispensado_por])

    def to_dict(self):
        return {
            'id': self.id,
            'prescricao_id': self.prescricao_id,
            'tenant_id': self.tenant_id,
            'dispensado_por': self.dispensado_por,
            'dispensador_nome': self.profissional.nome if self.profissional else None,
            'itens': self.itens,
            'observacoes': self.observacoes,
            'data_dispensacao': self.data_dispensacao.isoformat() if self.data_dispensacao else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='SET NULL'))
    action = db.Column(db.String(150), nullable=False)
    resource_type = db.Column(db.String(100))
    resource_id = db.Column(db.String(100))
    details = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('Profissional', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'user_nome': self.user.nome if self.user else None,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# --- WebhookLog para idempotência e audit ---
class WebhookLog(db.Model):
    __tablename__ = 'webhook_logs'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)  # mercadopago, stripe, asaas
    event_type = db.Column(db.String(100), nullable=False)
    provider_event_id = db.Column(db.String(255), nullable=False, index=True)  # idempotência
    payload = db.Column(db.JSON)
    processed = db.Column(db.Boolean, default=False)
    fatura_id = db.Column(db.Integer, db.ForeignKey('faturas.id'), nullable=True)
    assinatura_id = db.Column(db.Integer, db.ForeignKey('assinaturas.id'), nullable=True)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('provider', 'provider_event_id', name='uq_webhook_provider_event'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'provider': self.provider,
            'event_type': self.event_type,
            'provider_event_id': self.provider_event_id,
            'processed': self.processed,
            'fatura_id': self.fatura_id,
            'assinatura_id': self.assinatura_id,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CatalogoImportLog(db.Model):
    __tablename__ = 'catalogo_import_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='SET NULL'), nullable=True)
    filename = db.Column(db.String(255), nullable=True)
    detected_count = db.Column(db.Integer, default=0)
    imported_count = db.Column(db.Integer, default=0)
    errors = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('Profissional', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_nome': self.user.nome if self.user else None,
            'filename': self.filename,
            'detected_count': self.detected_count,
            'imported_count': self.imported_count,
            'errors': self.errors,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class EmailVerification(db.Model):
    __tablename__ = 'email_verifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(128), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used': self.used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class OnboardingProgress(db.Model):
    __tablename__ = 'onboarding_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('profissionais.id', ondelete='CASCADE'), nullable=False, unique=True)
    current_step = db.Column(db.Integer, default=1, nullable=False)
    steps_data = db.Column(db.JSON, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'current_step': self.current_step,
            'steps_data': self.steps_data,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# Helper para criar entrada de audit log em rotas
def create_audit_entry(tenant_id, user_id, action, resource_type=None, resource_id=None, details=None, ip=None):
    try:
        entry = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=details,
            ip_address=ip
        )
        db.session.add(entry)
        db.session.commit()
        return entry
    except Exception:
        db.session.rollback()
        raise


class ConviteAssociacao(db.Model):
    """Convite para médico ingressar numa clínica/associação (tenant).

    Fluxo: o admin da associação gera um convite (email e/ou código).
    O médico convidado aceita (via link ou código) e vira membro da
    associação (UsuarioAssociacao). Suporta convidar médicos que ainda
    não têm conta (criam uma) ou que já têm (ingressam na clínica).
    """

    __tablename__ = 'convites_associacoes'

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer, db.ForeignKey('associacoes.id', ondelete='CASCADE'), nullable=False
    )
    email = db.Column(db.String, nullable=False)
    # token único para aceite via link; codigo curto para aceite manual
    token = db.Column(db.String(64), unique=True, nullable=False)
    codigo = db.Column(db.String(12), unique=True, nullable=False)
    role_convidado = db.Column(db.String, default='member')  # 'member', 'viewer'
    status = db.Column(db.String, default='pendente')  # pendente, aceito, revogado, expirado
    criado_por = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    expira_em = db.Column(db.DateTime, nullable=True)
    aceito_em = db.Column(db.DateTime, nullable=True)
    aceito_por = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=True)

    associacao = db.relationship('Associacao', backref='convites')

    def to_dict(self):
        return {
            'id': self.id,
            'associacao_id': self.associacao_id,
            'email': self.email,
            'token': self.token,
            'codigo': self.codigo,
            'role_convidado': self.role_convidado,
            'status': self.status,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'expira_em': self.expira_em.isoformat() if self.expira_em else None,
            'aceito_em': self.aceito_em.isoformat() if self.aceito_em else None,
        }


class SalaAmbiente(db.Model):
    """Espaço físico de uma clínica/associação (tenant).

    Consultórios, salas de espera, ambientes de infusão, salas de
    procedimento/exames, banheiros, terapia, pré-atendimentos. Alimenta
    o agente de IA de gestão de pessoas/espaços/insumos (conecta com o
    VSF de visão computacional e o MESH de ocupação).

    Tipos (canônicos): consultorio, sala_espera, infusao, procedimento,
    banheiro, terapia, pre_atendimento, recepcao, triagem, outro.

    `capacidade` = lugares/poltronas do espaço (ex.: infusao com 2
    poltronas → capacidade=2). `vsf_room_key` = identificador usado pelo
    VSF nos eventos ROOM_ENTERED/ROOM_EXITED (RoomRef.room_id).
    """

    __tablename__ = 'salas_ambientes'

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer, db.ForeignKey('associacoes.id', ondelete='CASCADE'), nullable=False, index=True
    )
    nome = db.Column(db.String, nullable=False)
    tipo = db.Column(db.String, default='consultorio', nullable=False)
    capacidade = db.Column(db.Integer, default=1)
    andar = db.Column(db.String(40))
    ala = db.Column(db.String(40))
    recursos = db.Column(db.Text)  # ex.: "macas=2,balanca,computador"
    ativo = db.Column(db.Boolean, default=True)
    # Hierarquia física (Facility → Sector → Bed): referência ao andar/setor
    unidade_id = db.Column(
        db.Integer, db.ForeignKey('unidades_fisicas.id', ondelete='SET NULL'), nullable=True, index=True
    )
    andar_setor_id = db.Column(
        db.Integer, db.ForeignKey('andares_setores.id', ondelete='SET NULL'), nullable=True, index=True
    )
    # Integração VSF: identificador da sala no fluxo de visão computacional
    vsf_room_key = db.Column(db.String, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    associacao = db.relationship('Associacao', backref='salas_ambientes')
    andar_setor = db.relationship('AndarSetor', back_populates='espacos')

    def to_dict(self):
        return {
            'id': self.id,
            'associacao_id': self.associacao_id,
            'nome': self.nome,
            'tipo': self.tipo,
            'capacidade': self.capacidade,
            'andar': self.andar,
            'ala': self.ala,
            'recursos': self.recursos,
            'ativo': self.ativo,
            'unidade_id': self.unidade_id,
            'andar_setor_id': self.andar_setor_id,
            'vsf_room_key': self.vsf_room_key,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
        }


class UnidadeFisica(db.Model):
    """Instalação física (clínica, consultório, hospital, home care).

    Nível raiz da hierarquia canônica (espelha o Facility do CareOS):
        UnidadeFisica → AndarSetor (andares, alas, UTIs) → SalaAmbiente (espaços/leitos)

    `tipo`: clinica | consultorio | hospital | home_care
    `possui_uti` / `possui_centro_cirurgico`: flags para o agente IA e VSF.
    Compatível com o VSF via `vsf_facility_key` (Location.facility_id).
    """

    __tablename__ = 'unidades_fisicas'

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer, db.ForeignKey('associacoes.id', ondelete='CASCADE'), nullable=False, index=True
    )
    nome = db.Column(db.String, nullable=False)
    tipo = db.Column(db.String, default='clinica', nullable=False)  # clinica|consultorio|hospital|home_care
    endereco = db.Column(db.String)
    cidade = db.Column(db.String)
    uf = db.Column(db.String(2))
    possui_uti = db.Column(db.Boolean, default=False)
    possui_centro_cirurgico = db.Column(db.Boolean, default=False)
    ativo = db.Column(db.Boolean, default=True)
    # Integração VSF: identificador da instalação no fluxo de visão computacional
    vsf_facility_key = db.Column(db.String, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    associacao = db.relationship('Associacao', backref='unidades_fisicas')
    andares = db.relationship(
        'AndarSetor', back_populates='unidade', lazy=True, cascade='all, delete-orphan'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'associacao_id': self.associacao_id,
            'nome': self.nome,
            'tipo': self.tipo,
            'endereco': self.endereco,
            'cidade': self.cidade,
            'uf': self.uf,
            'possui_uti': self.possui_uti,
            'possui_centro_cirurgico': self.possui_centro_cirurgico,
            'ativo': self.ativo,
            'vsf_facility_key': self.vsf_facility_key,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
        }


class AndarSetor(db.Model):
    """Andar/ala/setor dentro de uma instalação (espelha o Sector do CareOS).

    Suporta sub-setores via `parent_id` (ex.: Andar 2 → Ala Norte → UTI 1).
    `tipo`: andar | ala | setor | uti | centro_cirurgico | recepcao | outro
    Compatível com o VSF via `unit`/`floor` (Location).
    """

    __tablename__ = 'andares_setores'

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer, db.ForeignKey('associacoes.id', ondelete='CASCADE'), nullable=False, index=True
    )
    unidade_id = db.Column(
        db.Integer, db.ForeignKey('unidades_fisicas.id', ondelete='CASCADE'), nullable=False, index=True
    )
    nome = db.Column(db.String, nullable=False)
    tipo = db.Column(db.String, default='andar', nullable=False)  # andar|ala|setor|uti|centro_cirurgico|recepcao|outro
    parent_id = db.Column(db.Integer, db.ForeignKey('andares_setores.id'), nullable=True)
    ordem = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    unidade = db.relationship('UnidadeFisica', back_populates='andares')
    parent = db.relationship('AndarSetor', remote_side=[id], backref='sub_setores')
    espacos = db.relationship('SalaAmbiente', back_populates='andar_setor', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'associacao_id': self.associacao_id,
            'unidade_id': self.unidade_id,
            'nome': self.nome,
            'tipo': self.tipo,
            'parent_id': self.parent_id,
            'ordem': self.ordem,
            'ativo': self.ativo,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
        }


class ICatalogProcess(db.Model):
    """Fila de processamento inteligente de catálogo/estoque (cadastro inteligente).

    Espelha o pipeline do SGAC (intelligent_onboarding) aplicado a
    PRODUTOS e ESTOQUE: upload de documento (bula/nota/planilha) →
    extração LLM → sugestão de cadastro → revisão humana → aplicar.

    Status: processado | pendente_revisao | aplicado | duplicado | erro
    """

    __tablename__ = 'icatalog_processes'

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer, db.ForeignKey('associacoes.id', ondelete='CASCADE'), nullable=False, index=True
    )
    original_filename = db.Column(db.String)
    document_type = db.Column(db.String, default='produto')
    status = db.Column(db.String, default='processado', nullable=False)
    # Dados extraídos pelo LLM (produto + estoque)
    extracted_data = db.Column(db.JSON)
    confidence = db.Column(db.Integer, default=0)
    # Resultado do match/duplicidade
    match_result = db.Column(db.JSON)  # {produto_id, motivo, acao_sugerida}
    missing_fields = db.Column(db.JSON)
    completeness_score = db.Column(db.Integer, default=0)
    action_taken = db.Column(db.String)  # created | merged | skipped | pending
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id', ondelete='SET NULL'), nullable=True)
    error_message = db.Column(db.Text)
    criado_por = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    revisado_em = db.Column(db.DateTime, nullable=True)
    revisado_por = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'associacao_id': self.associacao_id,
            'original_filename': self.original_filename,
            'document_type': self.document_type,
            'status': self.status,
            'extracted_data': self.extracted_data,
            'confidence': self.confidence,
            'match_result': self.match_result,
            'missing_fields': self.missing_fields,
            'completeness_score': self.completeness_score,
            'action_taken': self.action_taken,
            'produto_id': self.produto_id,
            'error_message': self.error_message,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'revisado_em': self.revisado_em.isoformat() if self.revisado_em else None,
        }
