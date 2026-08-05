from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import text

db = SQLAlchemy()


class Profissional(db.Model):
    __tablename__ = "profissionais"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    # crm/uf_crm nullable para staff/secretária (conselho_tipo='NONE').
    # Unicidade (crm, uf_crm) garantida por partial unique index
    # `uq_crm_uf_partial` na migration rc.16 (apenas quando ambos NOT NULL).
    crm = db.Column(db.String, nullable=True)
    uf_crm = db.Column(db.String, nullable=True)
    conselho_tipo = db.Column(
        db.String(20), nullable=True, default="CRM"
    )  # 'CRM' | 'CRP' | 'COREN' | 'CRN' | 'CREFITO' | 'NONE' (staff sem conselho)
    usuario = db.Column(db.String, unique=True, nullable=False)
    senha = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True)
    role = db.Column(
        db.String, default="profissional", nullable=False
    )  # 'admin', 'profissional', 'auxiliar'
    perfil_acesso = db.Column(
        db.String(20), nullable=True
    )  # 'assistencial' | 'administrativo' | 'solo' (None = derivado por plano/role)
    data_expiracao = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Campos de validação automática
    status_cadastro = db.Column(
        db.String, default="aprovado", nullable=False
    )  # 'pendente', 'aprovado', 'rejeitado'
    motivo_rejeicao = db.Column(db.Text)  # Motivo da rejeição se status='rejeitado'
    data_aprovacao = db.Column(db.DateTime)  # Quando foi aprovado
    aprovado_por = db.Column(db.String)  # 'system' ou ID do admin que aprovou
    validation_data = db.Column(db.JSON)  # Dados da validação CRM (resposta API, etc)

    # Onboarding & Email Verification
    status_conta = db.Column(
        db.String, default="active", nullable=False
    )  # 'pending_email', 'active', 'suspended'
    email_verified = db.Column(db.Boolean, default=False)
    onboarding_completed = db.Column(db.Boolean, default=False)
    onboarding_step = db.Column(db.Integer, default=0)  # último passo completado no wizard

    evolucoes = db.relationship("Evolucao", backref="profissional", lazy=True)
    logs = db.relationship("LogAtividade", backref="profissional", lazy=True)
    consultas = db.relationship("Consulta", backref="profissional", lazy=True)
    exames = db.relationship("Exame", backref="profissional", lazy=True)

    # Partial unique index criado na migration rc.16 — mantém unicidade
    # para profissionais de saúde sem barrar múltiplos staffs (crm NULL).
    __table_args__ = (
        db.Index(
            "uq_crm_uf_partial",
            "crm", "uf_crm",
            unique=True,
            postgresql_where=text("crm IS NOT NULL AND uf_crm IS NOT NULL"),
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "crm": self.crm,
            "uf_crm": self.uf_crm,
            "conselho_tipo": self.conselho_tipo,
            "usuario": self.usuario,
            "email": self.email,
            "role": self.role,
            "perfil_acesso": self.perfil_acesso,
            "status_cadastro": self.status_cadastro,
            "data_aprovacao": self.data_aprovacao.isoformat()
            if self.data_aprovacao
            else None,
            "data_expiracao": self.data_expiracao.isoformat()
            if self.data_expiracao
            else None,
            "status_conta": self.status_conta,
            "email_verified": self.email_verified,
            "onboarding_completed": self.onboarding_completed,
            "onboarding_step": self.onboarding_step,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ConfiguracaoPrescricao(db.Model):
    __tablename__ = "configuracao_prescricao"

    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(
        db.Integer,
        db.ForeignKey("profissionais.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    logo_clinica = db.Column(db.String)
    logo_profissional = db.Column(db.String)
    usar_assinatura_digital = db.Column(db.Boolean, default=False)
    modo_consultor_ia = db.Column(db.Boolean, default=False)
    cabecalho_personalizado = db.Column(db.Text)
    rodape_personalizado = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    profissional = db.relationship(
        "Profissional", backref=db.backref("config_prescricao", uselist=False)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "profissional_id": self.profissional_id,
            "logo_clinica": self.logo_clinica,
            "logo_profissional": self.logo_profissional,
            "usar_assinatura_digital": self.usar_assinatura_digital,
            "modo_consultor_ia": self.modo_consultor_ia,
            "cabecalho_personalizado": self.cabecalho_personalizado,
            "rodape_personalizado": self.rodape_personalizado,
        }


class ConfiguracaoIA(db.Model):
    __tablename__ = "configuracao_ia"

    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(
        db.Integer,
        db.ForeignKey("profissionais.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    nome_assistente = db.Column(db.String, default="Assistente Virtual")
    tom_de_voz = db.Column(db.String, default="Empático e profissional")
    valor_consulta = db.Column(db.String)
    regras_adicionais = db.Column(db.Text)
    instance_name = db.Column(
        db.String, unique=True
    )  # Nome da instância na Evolution API
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    profissional = db.relationship(
        "Profissional", backref=db.backref("config_ia", uselist=False)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "profissional_id": self.profissional_id,
            "nome_assistente": self.nome_assistente,
            "tom_de_voz": self.tom_de_voz,
            "valor_consulta": self.valor_consulta,
            "regras_adicionais": self.regras_adicionais,
            "instance_name": self.instance_name,
            "ativo": self.ativo,
        }


class SenhaTemporaria(db.Model):
    __tablename__ = "senhas_temporarias"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("profissionais.id", ondelete="CASCADE"),
        nullable=False,
    )
    senha_hash = db.Column(db.String, nullable=False)
    data_expiracao = db.Column(db.DateTime, nullable=False)
    usado = db.Column(db.Boolean, default=False, nullable=False)

    profissional = db.relationship("Profissional", backref="senhas_temporarias")

    def to_dict(self):
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "data_expiracao": self.data_expiracao.isoformat()
            if self.data_expiracao
            else None,
            "usado": self.usado,
        }


class Paciente(db.Model):
    __tablename__ = "pacientes"

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer, db.ForeignKey("associacoes.id"), nullable=True
    )  # Nullable for migration
    profissional_responsavel_id = db.Column(
        db.Integer,
        db.ForeignKey("profissionais.id", ondelete="SET NULL"),
        nullable=True,  # autoregistro pelo intake pode não ter responsável ainda
    )
    nome = db.Column(db.String, nullable=False)
    data_nascimento = db.Column(db.Date, nullable=True)  # opcional (autoregistro pelo intake)
    cpf = db.Column(db.String)
    genero = db.Column(db.String)
    telefone = db.Column(db.String)
    email = db.Column(db.String)
    endereco = db.Column(db.String)
    diagnostico = db.Column(db.Text)
    condicao_medica = db.Column(
        db.String
    )  # alias mais amigável para diagnóstico/condição principal
    observacoes = db.Column(db.Text)
    em_tratamento = db.Column(db.Boolean, default=False, nullable=False)
    composicao = db.Column(db.String)
    dosagem = db.Column(db.String)
    horarios = db.Column(db.String)
    foto_nome = db.Column(db.String)  # Nome original do arquivo da foto
    foto_caminho = db.Column(db.String)  # Caminho do arquivo no servidor
    foto_tipo = db.Column(db.String)  # MIME type (image/jpeg, image/png, etc.)
    foto_tamanho = db.Column(db.Integer)  # Tamanho em bytes
    consentimento_lgpd = db.Column(db.Boolean, default=False)
    data_consentimento = db.Column(db.DateTime)
    # P0-05 (Fase 1): data em que o titular revogou consentimento
    # (separada de data_consentimento para fins de auditoria LGPD)
    data_revogacao = db.Column(db.DateTime)
    # Novo campo para TDAH
    tdah_positivo = db.Column(db.Boolean, default=False, nullable=True)
    # Novo campo para depressão
    depressao_positiva = db.Column(db.Boolean, default=False, nullable=True)

    # Campos de Autenticação
    senha_hash = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    last_login_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamentos
    profissional_responsavel = db.relationship(
        "Profissional",
        foreign_keys=[profissional_responsavel_id],
        backref="pacientes_responsavel",
    )
    sintomas = db.relationship(
        "Sintoma", backref="paciente", lazy=True, cascade="all, delete-orphan"
    )
    dosagens = db.relationship(
        "Dosagem", backref="paciente", lazy=True, cascade="all, delete-orphan"
    )
    evolucoes = db.relationship(
        "Evolucao", backref="paciente", lazy=True, cascade="all, delete-orphan"
    )
    consultas = db.relationship(
        "Consulta", backref="paciente", lazy=True, cascade="all, delete-orphan"
    )
    exames = db.relationship(
        "Exame", backref="paciente", lazy=True, cascade="all, delete-orphan"
    )
    # Relationships to exam images and lab results are handled through the Exame model
    # Removed direct relationships to ExameImagem and ExameLabResultado
    compartilhamentos = db.relationship(
        "CompartilhamentoPaciente",
        backref="paciente",
        lazy=True,
        cascade="all, delete-orphan",
    )
    associacao = db.relationship("Associacao", backref="pacientes", lazy=True)
    snap_iv_testes = db.relationship(
        "SnapIVTeste",
        back_populates="paciente",
        lazy=True,
        cascade="all, delete-orphan",
    )
    anamneses = db.relationship(
        "Anamnese", backref="paciente", lazy=True, cascade="all, delete-orphan", order_by="Anamnese.data_anamnese.desc()"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "associacao_id": self.associacao_id,
            "associacao": self.associacao.nome if self.associacao else None,
            "profissional_responsavel_id": self.profissional_responsavel_id,
            "nome": self.nome,
            "data_nascimento": self.data_nascimento.isoformat()
            if self.data_nascimento
            else None,
            "cpf": self.cpf,
            "genero": self.genero,
            "telefone": self.telefone,
            "email": self.email,
            "endereco": self.endereco,
            "diagnostico": self.diagnostico,
            "condicao_medica": self.condicao_medica,
            "em_tratamento": self.em_tratamento,
            "composicao": self.composicao,
            "dosagem": self.dosagem,
            "horarios": self.horarios,
            "foto_nome": self.foto_nome,
            "foto_caminho": self.foto_caminho,
            "tdah_positivo": self.tdah_positivo,
            "depressao_positiva": self.depressao_positiva,
            "consentimento_lgpd": self.consentimento_lgpd,
            "data_consentimento": self.data_consentimento.isoformat()
            if self.data_consentimento
            else None,
            # New auth fields
            "is_active": getattr(self, "is_active", False),
            "email_verified": getattr(self, "email_verified", False),
            "last_login_at": self.last_login_at.isoformat()
            if hasattr(self, "last_login_at") and self.last_login_at
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Anamnese(db.Model):
    __tablename__ = "anamneses"

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissionais.id", ondelete="SET NULL"), nullable=True
    )

    # Dados coletados pela LIA (ou manualmente)
    condicao_principal = db.Column(db.Text)
    sintomas_atuais = db.Column(db.Text)
    medicamentos_uso = db.Column(db.Text)
    historico_cannabis = db.Column(db.Text)
    tratamentos_previos = db.Column(db.Text)
    exames_recentes = db.Column(db.Text)
    alergias = db.Column(db.Text)
    peso = db.Column(db.Float)
    altura = db.Column(db.Float)

    # Metadados
    fonte = db.Column(db.String, default="lia")  # "lia", "manual", "import"
    data_anamnese = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    telefone_origem = db.Column(db.String)
    conversa_id = db.Column(db.String)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    profissional = db.relationship("Profissional", backref="anamneses")

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "profissional_id": self.profissional_id,
            "profissional_nome": self.profissional.nome if self.profissional else None,
            "condicao_principal": self.condicao_principal,
            "sintomas_atuais": self.sintomas_atuais,
            "medicamentos_uso": self.medicamentos_uso,
            "historico_cannabis": self.historico_cannabis,
            "tratamentos_previos": self.tratamentos_previos,
            "exames_recentes": self.exames_recentes,
            "alergias": self.alergias,
            "peso": self.peso,
            "altura": self.altura,
            "fonte": self.fonte,
            "data_anamnese": self.data_anamnese.isoformat() if self.data_anamnese else None,
            "telefone_origem": self.telefone_origem,
            "conversa_id": self.conversa_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Sintoma(db.Model):
    __tablename__ = "sintomas"

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer, db.ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=True
    )
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    data = db.Column(db.Date, nullable=False)
    sintoma = db.Column(db.String, nullable=False)
    intensidade = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "paciente_id", "data", "sintoma", name="uq_paciente_data_sintoma"
        ),
        db.CheckConstraint(
            "intensidade >= 0 AND intensidade <= 10", name="check_intensidade_range"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "data": self.data.isoformat() if self.data else None,
            "sintoma": self.sintoma,
            "intensidade": self.intensidade,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Dosagem(db.Model):
    __tablename__ = "dosagens"

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer, db.ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=True
    )
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    data = db.Column(db.Date, nullable=False)
    dosagem = db.Column(db.String, nullable=False)
    gotas = db.Column(db.Integer, default=0)
    frequencia_diaria = db.Column(db.Integer, default=1)  # 1, 2, 3 ou 4 vezes ao dia
    concentracao_cbd = db.Column(db.Float, default=0.0)  # em mg/ml
    concentracao_thc = db.Column(db.Float, default=0.0)  # em mg/ml
    concentracao_cbg = db.Column(db.Float, default=0.0)  # em mg/ml
    concentracao_cbn = db.Column(db.Float, default=0.0)  # em mg/ml
    gotas_por_ml = db.Column(db.Integer, default=30, nullable=False)
    tipo_dose = db.Column(
        db.String, default="fixa"
    )  # 'fixa' (qtd igual) ou 'variavel' (por horario)
    esquema_doses = db.Column(db.JSON)  # Ex: {'manha': 2, 'tarde': 0, 'noite': 5}
    instrucoes_uso = db.Column(
        db.Text
    )  # Instruções específicas para esta dosagem (ex: "tomar com gordura")
    via_administracao = db.Column(db.String(50))  # Se diferir do produto
    produto_id = db.Column(
        db.Integer, db.ForeignKey("produtos.id"), nullable=True
    )  # Link opcional direto ao produto
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Add relationship to access instructions easily
    produto = db.relationship("Produto", backref="dosagens")

    def calcular_dose_diaria(self):
        if not self.gotas_por_ml or self.gotas_por_ml == 0:
            ml_por_gota = 0.05
        else:
            ml_por_gota = 1 / self.gotas_por_ml

        total_gotas = 0
        if self.tipo_dose == "variavel" and self.esquema_doses:
            # Soma as gotas de todos os horários
            for key, val in self.esquema_doses.items():
                if isinstance(val, (int, float)):
                    total_gotas += val
        else:
            # Cálculo antigo
            total_gotas = (self.gotas or 0) * (self.frequencia_diaria or 1)

        ml_por_dia = total_gotas * ml_por_gota

        return {
            "ml_por_dia": round(ml_por_dia, 2),
            "cbd_mg": round(ml_por_dia * self.concentracao_cbd, 2),
            "thc_mg": round(ml_por_dia * self.concentracao_thc, 2),
            "cbg_mg": round(ml_por_dia * self.concentracao_cbg, 2),
            "cbn_mg": round(ml_por_dia * self.concentracao_cbn, 2),
            "canabinoides_totais": round(
                ml_por_dia
                * (
                    self.concentracao_cbd
                    + self.concentracao_thc
                    + self.concentracao_cbg
                    + self.concentracao_cbn
                ),
                2,
            ),
            "total_gotas_diarias": total_gotas,
        }

    def to_dict(self):
        dose_diaria = self.calcular_dose_diaria()
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "data": self.data.isoformat() if self.data else None,
            "dosagem": self.dosagem,
            "gotas": self.gotas,
            "frequencia_diaria": self.frequencia_diaria,
            "concentracao_cbd": self.concentracao_cbd,
            "concentracao_thc": self.concentracao_thc,
            "concentracao_cbg": self.concentracao_cbg,
            "concentracao_cbn": self.concentracao_cbn,
            "gotas_por_ml": self.gotas_por_ml,
            "tipo_dose": self.tipo_dose,  # Novo
            "esquema_doses": self.esquema_doses,  # Novo
            "produto_id": self.produto_id,
            "instrucoes_uso": self.instrucoes_uso,
            "via_administracao": self.via_administracao,
            "dose_diaria": dose_diaria,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Prescricao(db.Model):
    __tablename__ = "prescricoes"

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer, db.ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=True
    )
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissionais.id", ondelete="SET NULL")
    )
    data_emissao = db.Column(db.DateTime, default=datetime.utcnow)
    arquivo_path = db.Column(db.String)  # Caminho do PDF gerado
    conteudo_json = db.Column(db.JSON)  # Snapshot dos medicamentos na época
    observacoes = db.Column(db.Text)

    paciente = db.relationship("Paciente")
    profissional = db.relationship("Profissional")

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "paciente_nome": self.paciente.nome if self.paciente else None,
            "profissional_nome": self.profissional.nome if self.profissional else None,
            "data_emissao": self.data_emissao.isoformat(),
            "arquivo_path": self.arquivo_path,
            "observacoes": self.observacoes,
        }


class Evolucao(db.Model):
    __tablename__ = "evolucoes"

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer, db.ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=True
    )
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissionais.id", ondelete="SET NULL")
    )
    data_evolucao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    nota_evolucao = db.Column(db.Text, nullable=False)
    fonte_origem = db.Column(db.String(20), default="manual")  # "manual" ou "sdr"

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "profissional_id": self.profissional_id,
            "data_evolucao": self.data_evolucao.isoformat()
            if self.data_evolucao
            else None,
            "nota_evolucao": self.nota_evolucao,
            "profissional_nome": self.profissional.nome if self.profissional else None,
            "fonte_origem": self.fonte_origem,
        }


class Consulta(db.Model):
    __tablename__ = "consultas"

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer, db.ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=True
    )
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissionais.id", ondelete="SET NULL")
    )
    data_hora = db.Column(db.DateTime, nullable=False)
    duracao_minutos = db.Column(db.Integer, default=60, nullable=False)
    tipo_consulta = db.Column(
        db.String, default="presencial", nullable=False
    )  # presencial, telemedicina
    status = db.Column(
        db.String, default="agendada", nullable=False
    )  # agendada, confirmada, realizada, cancelada
    observacoes = db.Column(db.Text)
    google_event_id = db.Column(db.String)  # ID do evento no Google Calendar
    lembrete_email_enviado = db.Column(db.Boolean, default=False)
    lembrete_whatsapp_enviado = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        try:
            paciente_nome = self.paciente.nome if self.paciente else None
        except:
            paciente_nome = None

        try:
            profissional_nome = self.profissional.nome if self.profissional else None
        except:
            profissional_nome = None

        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "paciente_nome": paciente_nome,
            "profissional_id": self.profissional_id,
            "profissional_nome": profissional_nome,
            "data_hora": self.data_hora.isoformat() if self.data_hora else None,
            "duracao_minutos": self.duracao_minutos,
            "tipo_consulta": self.tipo_consulta,
            "status": self.status,
            "observacoes": self.observacoes,
            "google_event_id": self.google_event_id,
            "lembrete_email_enviado": self.lembrete_email_enviado,
            "lembrete_whatsapp_enviado": self.lembrete_whatsapp_enviado,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Exame(db.Model):
    __tablename__ = "exames"

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer, db.ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=True
    )
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissionais.id", ondelete="SET NULL")
    )
    data_exame = db.Column(db.Date, nullable=False)
    tipo_exame = db.Column(db.String, nullable=False)  # 'texto', 'arquivo', 'numerico'
    titulo = db.Column(db.String, nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    valor = db.Column(db.Float, nullable=True)
    unidade = db.Column(db.String, nullable=True)
    is_chartable = db.Column(
        db.Boolean, default=False, nullable=False
    )  # Flag para dados gráficos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    imagens = db.relationship(
        "ExameImagem", backref="exame", lazy=True, cascade="all, delete-orphan"
    )
    resultados_lab = db.relationship(
        "ExameLabResultado", backref="exame", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "profissional_id": self.profissional_id,
            "profissional_nome": self.profissional.nome if self.profissional else None,
            "data_exame": self.data_exame.isoformat() if self.data_exame else None,
            "tipo_exame": self.tipo_exame,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "valor": self.valor,
            "unidade": self.unidade,
            "is_chartable": self.is_chartable,  # Incluir flag de gráfico
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ExameImagem(db.Model):
    __tablename__ = "exame_imagens"

    id = db.Column(db.Integer, primary_key=True)
    exame_id = db.Column(
        db.Integer, db.ForeignKey("exames.id", ondelete="CASCADE"), nullable=False
    )
    arquivo_nome = db.Column(db.String, nullable=False)
    arquivo_caminho = db.Column(db.String, nullable=False)
    laudo = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "exame_id": self.exame_id,
            "arquivo_nome": self.arquivo_nome,
            "arquivo_caminho": self.arquivo_caminho,
            "laudo": self.laudo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ExameLabResultado(db.Model):
    __tablename__ = "exame_lab_resultados"

    id = db.Column(db.Integer, primary_key=True)
    exame_id = db.Column(
        db.Integer, db.ForeignKey("exames.id", ondelete="CASCADE"), nullable=False
    )
    teste_nome = db.Column(db.String, nullable=False)
    valor = db.Column(db.Numeric, nullable=False)
    unidade = db.Column(db.String, nullable=False)
    valor_referencia = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "exame_id": self.exame_id,
            "teste_nome": self.teste_nome,
            "valor": float(self.valor) if self.valor is not None else None,
            "unidade": self.unidade,
            "valor_referencia": self.valor_referencia,
        }


class SolicitacaoExame(db.Model):
    __tablename__ = "solicitacoes_exames"

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissionais.id", ondelete="SET NULL")
    )
    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow)
    exames_solicitados = db.Column(db.JSON)  # Array of exam names
    observacoes = db.Column(db.Text)
    arquivo_path = db.Column(db.String)  # PDF file path
    status = db.Column(
        db.String, default="pendente"
    )  # 'pendente', 'entregue', 'realizado'

    # Relationships
    paciente = db.relationship("Paciente")
    profissional = db.relationship("Profissional")

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "profissional_id": self.profissional_id,
            "profissional_nome": self.profissional.nome if self.profissional else None,
            "data_solicitacao": self.data_solicitacao.isoformat()
            if self.data_solicitacao
            else None,
            "exames_solicitados": self.exames_solicitados,
            "observacoes": self.observacoes,
            "arquivo_path": self.arquivo_path,
            "status": self.status,
        }


class LogAtividade(db.Model):
    __tablename__ = "logs_atividades"

    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissionais.id", ondelete="SET NULL")
    )
    associacao_id = db.Column(
        db.Integer, db.ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=True
    )
    acao = db.Column(db.String, nullable=False)
    detalhes = db.Column(db.Text)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    associacao = db.relationship("Associacao", foreign_keys=[associacao_id])

    def to_dict(self):
        return {
            "id": self.id,
            "profissional_id": self.profissional_id,
            "profissional_nome": self.profissional.nome if self.profissional else None,
            "acao": self.acao,
            "detalhes": self.detalhes,
            "data_hora": self.data_hora.isoformat() if self.data_hora else None,
        }


class CompartilhamentoPaciente(db.Model):
    __tablename__ = "compartilhamentos_pacientes"

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    profissional_id = db.Column(
        db.Integer,
        db.ForeignKey("profissionais.id", ondelete="CASCADE"),
        nullable=False,
    )
    nivel_acesso = db.Column(
        db.String, default="leitura", nullable=False
    )  # leitura, escrita, completo
    data_compartilhamento = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False
    )
    compartilhado_por = db.Column(
        db.Integer, db.ForeignKey("profissionais.id", ondelete="SET NULL")
    )
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    # Relacionamentos
    profissional = db.relationship(
        "Profissional",
        foreign_keys=[profissional_id],
        backref="compartilhamentos_recebidos",
    )
    compartilhador = db.relationship(
        "Profissional",
        foreign_keys=[compartilhado_por],
        backref="compartilhamentos_feitos",
    )

    # Constraint para evitar duplicatas
    __table_args__ = (
        db.UniqueConstraint(
            "paciente_id", "profissional_id", name="uq_paciente_profissional"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "profissional_id": self.profissional_id,
            "profissional_nome": self.profissional.nome if self.profissional else None,
            "nivel_acesso": self.nivel_acesso,
            "data_compartilhamento": self.data_compartilhamento.isoformat()
            if self.data_compartilhamento
            else None,
            "compartilhado_por": self.compartilhado_por,
            "compartilhador_nome": self.compartilhador.nome
            if self.compartilhador
            else None,
            "ativo": self.ativo,
        }


class Produto(db.Model):
    __tablename__ = "produtos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    tipo = db.Column(db.String, default="oleo")
    categoria = db.Column(db.String(100), nullable=True)
    unidade = db.Column(db.String(50), nullable=True)
    concentracao = db.Column(db.String(50), nullable=True)
    codigo_barras = db.Column(db.String(50), nullable=True)
    concentracao_cbd = db.Column(db.Float, default=0)
    concentracao_thc = db.Column(db.Float, default=0)
    concentracao_cbg = db.Column(db.Float, default=0)
    concentracao_cbn = db.Column(db.Float, default=0)
    gotas_por_ml = db.Column(db.Integer, default=30)
    volume_ml = db.Column(db.Float, default=30)
    fabricante = db.Column(db.String)
    descricao = db.Column(db.Text)
    instrucoes = db.Column(
        db.Text
    )  # Instruções padrão do produto (ex: ingerir com gordura)
    via_administracao = db.Column(
        db.String(50), default="Oral"
    )  # Oral, Sublingual, Tópico
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_registro = db.Column(
        db.Date, default=datetime.utcnow
    )  # Nova coluna: Data de registro manual ou automática
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "tipo": self.tipo,
            "categoria": self.categoria,
            "unidade": self.unidade,
            "concentracao": self.concentracao,
            "codigo_barras": self.codigo_barras,
            "concentracao_cbd": self.concentracao_cbd,
            "concentracao_thc": self.concentracao_thc,
            "concentracao_cbg": self.concentracao_cbg,
            "concentracao_cbn": self.concentracao_cbn,
            "gotas_por_ml": self.gotas_por_ml,
            "volume_ml": self.volume_ml,
            "fabricante": self.fabricante,
            "descricao": self.descricao,
            "instrucoes": self.instrucoes,
            "via_administracao": self.via_administracao,
            "ativo": self.ativo,
            "data_registro": self.data_registro.isoformat()
            if self.data_registro
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ReminderSettings(db.Model):
    __tablename__ = "reminder_settings"

    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(
        db.Integer,
        db.ForeignKey("profissionais.id", ondelete="CASCADE"),
        nullable=False,
    )
    lead_time_hours = db.Column(
        db.Integer, default=24, nullable=False
    )  # Horas antes da consulta
    email_template = db.Column(db.Text, default="Lembrete de consulta", nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    profissional = db.relationship("Profissional", backref="reminder_settings")

    def to_dict(self):
        return {
            "id": self.id,
            "profissional_id": self.profissional_id,
            "lead_time_hours": self.lead_time_hours,
            "email_template": self.email_template,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ========== BILLING / SAAS ==========


class Plano(db.Model):
    __tablename__ = "planos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    # Slug canônico para tier (basico | premium | enterprise).
    # Backfill na migration: sem_ia→basico, com_ia→premium.
    # Usado como fonte de verdade para gating de features.
    slug = db.Column(db.String(64), unique=True, nullable=True)
    descricao = db.Column(db.Text)
    preco_mensal = db.Column(db.Float, nullable=False, default=0)
    limite_pacientes = db.Column(db.Integer, default=50)
    limite_agentes_ia = db.Column(db.Integer, default=3)
    limite_armazenamento_mb = db.Column(db.Integer, default=1024)
    cor = db.Column(db.String, default="#1976d2")  # Cor Hex para UI
    is_popular = db.Column(db.Boolean, default=False)  # Destaque na UI
    # Feature flags por plano. Cada plano decide quais features libera.
    # Mantemos nomes booleanos para clareza; padrão = False (não libera).
    permite_gestao_clinica = db.Column(db.Boolean, default=False, nullable=False)
    permite_agentes_sdr = db.Column(db.Boolean, default=False, nullable=False)
    permite_chatbot_ia = db.Column(db.Boolean, default=False, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "slug": self.slug,
            "descricao": self.descricao,
            "preco_mensal": self.preco_mensal,
            "limite_pacientes": self.limite_pacientes,
            "limite_agentes_ia": self.limite_agentes_ia,
            "limite_armazenamento_mb": self.limite_armazenamento_mb,
            "cor": self.cor,
            "is_popular": self.is_popular,
            "permite_gestao_clinica": self.permite_gestao_clinica,
            "permite_agentes_sdr": self.permite_agentes_sdr,
            "permite_chatbot_ia": self.permite_chatbot_ia,
            "ativo": self.ativo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Assinatura(db.Model):
    __tablename__ = "assinaturas"

    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(
        db.Integer,
        db.ForeignKey("profissionais.id", ondelete="CASCADE"),
        nullable=False,
    )
    plano_id = db.Column(db.Integer, db.ForeignKey("planos.id"), nullable=False)
    status = db.Column(
        db.String, default="trial"
    )  # trial, ativa, cancelada, inadimplente, pending
    trial_ends_at = db.Column(db.DateTime)
    renovacao_em = db.Column(db.DateTime)
    # --- campos v2 billing ---
    provedor = db.Column(db.String(50))  # mercadopago, stripe, asaas
    provider_subscription_id = db.Column(db.String(255))
    periodicidade = db.Column(db.String(20), default="mensal")  # mensal, trimestral, semestral, anual
    # -------------------------
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    plano = db.relationship("Plano")
    profissional = db.relationship("Profissional")

    def to_dict(self):
        return {
            "id": self.id,
            "profissional_id": self.profissional_id,
            "plano_id": self.plano_id,
            "plano": self.plano.to_dict() if self.plano else None,
            "status": self.status,
            "trial_ends_at": self.trial_ends_at.isoformat()
            if self.trial_ends_at
            else None,
            "renovacao_em": self.renovacao_em.isoformat()
            if self.renovacao_em
            else None,
            "provedor": self.provedor,
            "provider_subscription_id": self.provider_subscription_id,
            "periodicidade": self.periodicidade,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Fatura(db.Model):
    __tablename__ = "faturas"

    id = db.Column(db.Integer, primary_key=True)
    assinatura_id = db.Column(
        db.Integer, db.ForeignKey("assinaturas.id"), nullable=False
    )
    valor = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, default="pendente")  # pendente, paga, cancelada
    vencimento = db.Column(db.DateTime)
    cobranca_id = db.Column(db.String)  # id de cobrança no PSP
    metodo = db.Column(db.String, default="pix")  # pix, boleto, card
    # --- campos v2 billing ---
    provedor = db.Column(db.String(50))
    provider_invoice_id = db.Column(db.String(255))
    # -------------------------
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    assinatura = db.relationship("Assinatura")

    def to_dict(self):
        return {
            "id": self.id,
            "assinatura_id": self.assinatura_id,
            "valor": self.valor,
            "status": self.status,
            "vencimento": self.vencimento.isoformat() if self.vencimento else None,
            "cobranca_id": self.cobranca_id,
            "metodo": self.metodo,
            "provedor": self.provedor,
            "provider_invoice_id": self.provider_invoice_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PagamentoRegistro(db.Model):
    __tablename__ = "pagamentos_registros"

    id = db.Column(db.Integer, primary_key=True)
    fatura_id = db.Column(db.Integer, db.ForeignKey("faturas.id"), nullable=False)
    status = db.Column(db.String, default="pending")  # pending, paid, failed, canceled
    metodo = db.Column(db.String, default="pix")
    valor = db.Column(db.Float, nullable=False)
    referencia_psp = db.Column(db.String)
    payload = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    fatura = db.relationship("Fatura")

    def to_dict(self):
        return {
            "id": self.id,
            "fatura_id": self.fatura_id,
            "status": self.status,
            "metodo": self.metodo,
            "valor": self.valor,
            "referencia_psp": self.referencia_psp,
            "payload": self.payload,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ========== FATURAMENTO CLÍNICO ==========
# Módulo de faturamento do atendimento (convênios, tabela de preços,
# percentual de repasse do profissional, contas a receber).
# Modalidade PARTICULAR = lançamento sem convenio_id (convenio_id NULL).
# Valor particular vem de `servicos.valor_particular`.

class Convenio(db.Model):
    """Convênio/plano de saúde que paga pelos atendimentos (valor fixo por serviço)."""

    __tablename__ = "convenios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), unique=True, nullable=False)
    registro_ans = db.Column(db.String(50), nullable=True)
    tipo = db.Column(db.String(20), default="operadora")  # operadora | consultorio | outro
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "registro_ans": self.registro_ans,
            "tipo": self.tipo,
            "ativo": self.ativo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Servico(db.Model):
    """Serviço/procedimento/consulta com valor particular (tabela base)."""

    __tablename__ = "servicos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), default="consulta")  # consulta | retorno | procedimento | outro
    codigo = db.Column(db.String(50), nullable=True)
    valor_particular = db.Column(db.Float, default=0.0, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "tipo": self.tipo,
            "codigo": self.codigo,
            "valor_particular": self.valor_particular,
            "ativo": self.ativo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TabelaPrecoConvenio(db.Model):
    """Valor fixo que um convênio paga por serviço (override sobre o particular)."""

    __tablename__ = "tabela_preco_convenios"

    id = db.Column(db.Integer, primary_key=True)
    convenio_id = db.Column(db.Integer, db.ForeignKey("convenios.id"), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id"), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("convenio_id", "servico_id", name="uq_tabela_convenio_servico"),
    )

    convenio = db.relationship("Convenio")
    servico = db.relationship("Servico")

    def to_dict(self):
        return {
            "id": self.id,
            "convenio_id": self.convenio_id,
            "convenio_nome": self.convenio.nome if self.convenio else None,
            "servico_id": self.servico_id,
            "servico_nome": self.servico.nome if self.servico else None,
            "valor": self.valor,
            "ativo": self.ativo,
        }


class PercentualRepasse(db.Model):
    """Percentual do valor que vai para o profissional, por serviço (ou global).

    `servico_id` NULL = percentual global do profissional (fallback).
    Resolução: linha por serviço → linha global → 100% (profissional fica com tudo).
    """

    __tablename__ = "percentuais_repasse"

    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissionais.id"), nullable=False
    )
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id"), nullable=True)
    percentual = db.Column(db.Float, nullable=False)  # 0-100
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "profissional_id", "servico_id", name="uq_repasse_profissional_servico"
        ),
    )

    profissional = db.relationship("Profissional")
    servico = db.relationship("Servico")

    def to_dict(self):
        return {
            "id": self.id,
            "profissional_id": self.profissional_id,
            "profissional_nome": self.profissional.nome if self.profissional else None,
            "servico_id": self.servico_id,
            "servico_nome": self.servico.nome if self.servico else None,
            "percentual": self.percentual,
            "ativo": self.ativo,
        }


class LancamentoFaturamento(db.Model):
    """Conta a receber de um atendimento (modalidade particular ou convênio)."""

    __tablename__ = "lancamentos_faturamento"

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer, db.ForeignKey("associacoes.id", ondelete="CASCADE"), nullable=True
    )
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="SET NULL"), nullable=True
    )
    atendimento_id = db.Column(
        db.Integer, db.ForeignKey("consultas.id", ondelete="SET NULL"), nullable=True
    )
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissionais.id"), nullable=False
    )
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id"), nullable=False)
    convenio_id = db.Column(
        db.Integer, db.ForeignKey("convenios.id"), nullable=True  # NULL = PARTICULAR
    )
    valor_total = db.Column(db.Float, nullable=False)
    desconto = db.Column(db.Float, default=0.0, nullable=False)
    valor_receber = db.Column(db.Float, nullable=False)  # valor_total - desconto
    percentual_repasse = db.Column(db.Float, nullable=False)  # 0-100
    valor_repasse = db.Column(db.Float, nullable=False)  # parte do profissional
    forma_pagamento = db.Column(db.String(30), default="dinheiro")
    status = db.Column(db.String(20), default="pendente")  # pendente | parcial | pago | cancelado
    data_lancamento = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_recebimento = db.Column(db.DateTime, nullable=True)
    observacao = db.Column(db.Text, nullable=True)
    criado_por = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    convenio = db.relationship("Convenio")
    servico = db.relationship("Servico")
    profissional = db.relationship("Profissional")
    paciente = db.relationship("Paciente")

    def to_dict(self, privileged: bool = True):
        recebido = sum(r.valor for r in self.recebimentos) if self.recebimentos else 0.0
        status_label = {
            "pendente": "EM ABERTO",
            "parcial": "EM ABERTO (PARCIAL)",
            "pago": "PAGO",
            "cancelado": "RESTITUÍDO",
        }.get(self.status, self.status.upper())
        dados = {
            "id": self.id,
            "associacao_id": self.associacao_id,
            "paciente_id": self.paciente_id,
            "paciente_nome": self.paciente.nome if self.paciente else None,
            "atendimento_id": self.atendimento_id,
            "profissional_id": self.profissional_id,
            "profissional_nome": self.profissional.nome if self.profissional else None,
            "servico_id": self.servico_id,
            "servico_nome": self.servico.nome if self.servico else None,
            "convenio_id": self.convenio_id,
            "convenio_nome": self.convenio.nome if self.convenio else None,
            "modalidade": "particular" if self.convenio_id is None else "convenio",
            "forma_pagamento": self.forma_pagamento,
            "status": self.status,
            "status_label": status_label,
            "data_lancamento": self.data_lancamento.isoformat() if self.data_lancamento else None,
            "data_recebimento": self.data_recebimento.isoformat() if self.data_recebimento else None,
            "observacao": self.observacao,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if privileged:
            dados.update({
                "valor_total": self.valor_total,
                "desconto": self.desconto,
                "valor_receber": self.valor_receber,
                "percentual_repasse": self.percentual_repasse,
                "valor_repasse": self.valor_repasse,
                "valor_recebido": round(recebido, 2),
            })
        return dados


class Recebimento(db.Model):
    """Pagamento (parcial/múltiplo) recebido de um lançamento."""

    __tablename__ = "recebimentos"

    id = db.Column(db.Integer, primary_key=True)
    lancamento_id = db.Column(
        db.Integer, db.ForeignKey("lancamentos_faturamento.id"), nullable=False
    )
    valor = db.Column(db.Float, nullable=False)
    forma_pagamento = db.Column(db.String(30), default="dinheiro")
    data = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    observacao = db.Column(db.Text, nullable=True)
    criado_por = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lancamento = db.relationship(
        "LancamentoFaturamento", backref=db.backref("recebimentos", lazy="select")
    )

    def to_dict(self):
        return {
            "id": self.id,
            "lancamento_id": self.lancamento_id,
            "valor": self.valor,
            "forma_pagamento": self.forma_pagamento,
            "data": self.data.isoformat() if self.data else None,
            "observacao": self.observacao,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PreConsulta(db.Model):
    """Pré-consulta coletada pelo Ara Intake e vinculada ao paciente (SIAP).

    Criada automaticamente quando a pré-consulta é concluída no intake
    (cadastro de paciente por autoregistro). Alimenta o Dashboard do médico
    (queixa do dia, status da pré-consulta).
    """

    __tablename__ = "pre_consultas"

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    queixa_principal = db.Column(db.Text, nullable=True)
    intensidade = db.Column(db.String(20), nullable=True)
    canal = db.Column(db.String(20), default="web", nullable=False)  # web | telegram
    status = db.Column(
        db.String(20), default="concluida", nullable=False
    )  # concluida | revisada
    intake_interview_id = db.Column(db.String(64), nullable=True, unique=True)
    araos_patient_id = db.Column(db.String(64), nullable=True, index=True)
    gene_expressions = db.Column(db.JSON, nullable=True)
    data_pre_consulta = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    paciente = db.relationship("Paciente")

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "queixa_principal": self.queixa_principal,
            "intensidade": self.intensidade,
            "canal": self.canal,
            "status": self.status,
            "intake_interview_id": self.intake_interview_id,
            "araos_patient_id": self.araos_patient_id,
            "data_pre_consulta": self.data_pre_consulta.isoformat()
            if self.data_pre_consulta
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OnboardingPaciente(db.Model):
    """Item de onboarding/pendência de paciente (padrão SGA).

    Criação: cadastro administrativo com dados incompletos ou duplicado de um
    paciente existente. O administrativo confirma (cria/usa existente) ou
    descarta na fila de pendências.
    """

    __tablename__ = "onboarding_pacientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=True)
    telefone = db.Column(db.String(32), nullable=True)
    cpf = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    queixa = db.Column(db.Text, nullable=True)
    origem = db.Column(db.String(20), default="admin", nullable=False)  # admin | manual | intake
    dados_sugeridos = db.Column(db.JSON, nullable=True)
    motivo = db.Column(db.String(30), default="dados_incompletos", nullable=False)
    # dados_incompletos | duplicado | revisar
    status = db.Column(db.String(20), default="pendente", nullable=False)  # pendente | aprovado | descartado
    duplicado_de = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="SET NULL"), nullable=True
    )
    criado_por = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    duplicado = db.relationship("Paciente")

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "telefone": self.telefone,
            "cpf": self.cpf,
            "email": self.email,
            "queixa": self.queixa,
            "origem": self.origem,
            "dados_sugeridos": self.dados_sugeridos,
            "motivo": self.motivo,
            "status": self.status,
            "duplicado_de": self.duplicado_de,
            "duplicado_nome": self.duplicado.nome if self.duplicado else None,
            "criado_por": self.criado_por,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SolicitacoesCadastro(db.Model):
    __tablename__ = "solicitacoes_cadastro"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    # crm/uf_crm nullable para staff/secretária (conselho_tipo='NONE').
    # Unicidade (crm, uf_crm) garantida por partial unique index
    # `uq_solicitacao_crm_uf_partial` na migration rc.16.
    crm = db.Column(db.String, nullable=True)
    uf_crm = db.Column(db.String, nullable=True)
    conselho_tipo = db.Column(
        db.String(20), nullable=True, default="CRM"
    )  # 'CRM' | 'CRP' | 'COREN' | 'CRN' | 'CREFITO' | 'NONE'
    telefone = db.Column(db.String)
    especialidade = db.Column(db.String)
    instituicao = db.Column(db.String)
    tipo_vinculo = db.Column(db.String, default="pessoal")  # 'pessoal', 'existente'
    associacao_id = db.Column(
        db.Integer, db.ForeignKey("associacoes.id"), nullable=True
    )  # ID da associacao se 'existente'
    status = db.Column(db.String, default="pendente", nullable=False)
    data_solicitacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_aprovacao = db.Column(db.DateTime)
    observacoes = db.Column(db.Text)
    aprovado_por = db.Column(
        db.Integer, db.ForeignKey("profissionais.id", ondelete="SET NULL")
    )
    verificacao_automatica = db.Column(db.JSON)  # Resultados da auditoria IA

    aprovador = db.relationship(
        "Profissional", backref="solicitacoes_aprovadas", foreign_keys=[aprovado_por]
    )

    __table_args__ = (
        # Partial unique index criado na migration rc.16 — mesma
        # motivação da constraint `uq_crm_uf_partial` em Profissional.
        db.Index(
            "uq_solicitacao_crm_uf_partial",
            "crm", "uf_crm",
            unique=True,
            postgresql_where=text("crm IS NOT NULL AND uf_crm IS NOT NULL"),
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "crm": self.crm,
            "uf_crm": self.uf_crm,
            "conselho_tipo": self.conselho_tipo,
            "telefone": self.telefone,
            "especialidade": self.especialidade,
            "instituicao": self.instituicao,
            "tipo_vinculo": self.tipo_vinculo,
            "associacao_id": self.associacao_id,
            "status": self.status,
            "data_solicitacao": self.data_solicitacao.isoformat(),
            "data_aprovacao": self.data_aprovacao.isoformat()
            if self.data_aprovacao
            else None,
            "observacoes": self.observacoes,
            "aprovado_por": self.aprovado_por,
            "aprovador_nome": self.aprovador.nome if self.aprovador else None,
            "verificacao_automatica": self.verificacao_automatica,
        }


class SintomaPersonalizado(db.Model):
    __tablename__ = "sintomas_personalizados"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, unique=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
        }


class OCRResultado(db.Model):
    __tablename__ = "ocr_resultados"

    id = db.Column(db.Integer, primary_key=True)
    exame_imagem_id = db.Column(
        db.Integer,
        db.ForeignKey("exame_imagens.id", ondelete="CASCADE"),
        nullable=False,
    )
    texto_extraido = db.Column(db.Text, nullable=False)
    dados_estruturados = db.Column(
        db.JSON, nullable=True
    )  # Dados extraídos em formato JSON para IA
    confianca = db.Column(db.Float, nullable=True)  # Confiança do OCR (0-100)
    status_processamento = db.Column(
        db.String, default="pendente", nullable=False
    )  # pendente, processando, concluido, erro
    erro_processamento = db.Column(db.Text, nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    processado_em = db.Column(db.DateTime, nullable=True)

    # Relacionamento
    exame_imagem = db.relationship("ExameImagem", backref="ocr_resultados")

    def to_dict(self):
        return {
            "id": self.id,
            "exame_imagem_id": self.exame_imagem_id,
            "texto_extraido": self.texto_extraido,
            "dados_estruturados": self.dados_estruturados,
            "confianca": self.confianca,
            "status_processamento": self.status_processamento,
            "erro_processamento": self.erro_processamento,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
            "processado_em": self.processado_em.isoformat()
            if self.processado_em
            else None,
        }


class SnapIVTeste(db.Model):
    __tablename__ = "snap_iv_testes"

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissionais.id", ondelete="SET NULL")
    )

    # Respostas das perguntas (0-3)
    # Desatenção (itens 1-9)
    desatencao_1 = db.Column(db.Integer, nullable=False)
    desatencao_2 = db.Column(db.Integer, nullable=False)
    desatencao_3 = db.Column(db.Integer, nullable=False)
    desatencao_4 = db.Column(db.Integer, nullable=False)
    desatencao_5 = db.Column(db.Integer, nullable=False)
    desatencao_6 = db.Column(db.Integer, nullable=False)
    desatencao_7 = db.Column(db.Integer, nullable=False)
    desatencao_8 = db.Column(db.Integer, nullable=False)
    desatencao_9 = db.Column(db.Integer, nullable=False)

    # Hiperatividade/Impulsividade (itens 10-18)
    hiperatividade_10 = db.Column(db.Integer, nullable=False)
    hiperatividade_11 = db.Column(db.Integer, nullable=False)
    hiperatividade_12 = db.Column(db.Integer, nullable=False)
    hiperatividade_13 = db.Column(db.Integer, nullable=False)
    hiperatividade_14 = db.Column(db.Integer, nullable=False)
    hiperatividade_15 = db.Column(db.Integer, nullable=False)
    hiperatividade_16 = db.Column(db.Integer, nullable=False)
    hiperatividade_17 = db.Column(db.Integer, nullable=False)
    hiperatividade_18 = db.Column(db.Integer, nullable=False)

    # Resultados da análise
    pontos_desatencao = db.Column(db.Integer, nullable=False)
    pontos_hiperatividade = db.Column(db.Integer, nullable=False)
    sugestivo_desatencao = db.Column(db.Boolean, nullable=False)
    sugestivo_hiperatividade = db.Column(db.Boolean, nullable=False)
    tdah_positivo = db.Column(db.Boolean, nullable=False)

    # Metadados
    data_realizacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    observacoes = db.Column(db.Text)

    # Relacionamentos
    paciente = db.relationship("Paciente", back_populates="snap_iv_testes")
    profissional = db.relationship("Profissional", backref="snap_iv_testes")

    def calcular_resultados(self):
        """Calcula os resultados baseado nas respostas"""
        # Contagem para Desatenção (itens 1-9)
        pontos_desatencao = 0
        for i in range(1, 10):
            resposta = getattr(self, f"desatencao_{i}")
            if resposta >= 2:  # 2 ou 3 = clinicamente significativo
                pontos_desatencao += 1

        # Contagem para Hiperatividade/Impulsividade (itens 10-18)
        pontos_hiperatividade = 0
        for i in range(10, 19):
            resposta = getattr(self, f"hiperatividade_{i}")
            if resposta >= 2:  # 2 ou 3 = clinicamente significativo
                pontos_hiperatividade += 1

        # Critérios de corte: 6 ou mais itens marcados como >= 2
        sugestivo_desatencao = pontos_desatencao >= 6
        sugestivo_hiperatividade = pontos_hiperatividade >= 6
        tdah_positivo = sugestivo_desatencao or sugestivo_hiperatividade

        return {
            "pontos_desatencao": pontos_desatencao,
            "pontos_hiperatividade": pontos_hiperatividade,
            "sugestivo_desatencao": sugestivo_desatencao,
            "sugestivo_hiperatividade": sugestivo_hiperatividade,
            "tdah_positivo": tdah_positivo,
        }

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "profissional_id": self.profissional_id,
            "profissional_nome": self.profissional.nome if self.profissional else None,
            "respostas": {
                "desatencao": {
                    f"item_{i}": getattr(self, f"desatencao_{i}") for i in range(1, 10)
                },
                "hiperatividade": {
                    f"item_{i}": getattr(self, f"hiperatividade_{i}")
                    for i in range(10, 19)
                },
            },
            "resultados": {
                "pontos_desatencao": self.pontos_desatencao,
                "pontos_hiperatividade": self.pontos_hiperatividade,
                "sugestivo_desatencao": self.sugestivo_desatencao,
                "sugestivo_hiperatividade": self.sugestivo_hiperatividade,
                "tdah_positivo": self.tdah_positivo,
            },
            "data_realizacao": self.data_realizacao.isoformat()
            if self.data_realizacao
            else None,
            "observacoes": self.observacoes,
        }


class BeckDepressionTeste(db.Model):
    __tablename__ = "beck_depression_testes"

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissionais.id", ondelete="SET NULL")
    )

    # Respostas das 21 perguntas do BDI-II (0-3)
    item_1 = db.Column(db.Integer, nullable=False)  # Tristeza
    item_2 = db.Column(db.Integer, nullable=False)  # Pessimismo
    item_3 = db.Column(db.Integer, nullable=False)  # Fracasso passado
    item_4 = db.Column(db.Integer, nullable=False)  # Perda de prazer
    item_5 = db.Column(db.Integer, nullable=False)  # Sentimentos de culpa
    item_6 = db.Column(db.Integer, nullable=False)  # Sentimentos de punição
    item_7 = db.Column(db.Integer, nullable=False)  # Autoaversão
    item_8 = db.Column(db.Integer, nullable=False)  # Autocrítica
    item_9 = db.Column(db.Integer, nullable=False)  # Pensamentos suicidas
    item_10 = db.Column(db.Integer, nullable=False)  # Choro
    item_11 = db.Column(db.Integer, nullable=False)  # Agitação
    item_12 = db.Column(db.Integer, nullable=False)  # Perda de interesse
    item_13 = db.Column(db.Integer, nullable=False)  # Indecisão
    item_14 = db.Column(db.Integer, nullable=False)  # Desvalia
    item_15 = db.Column(db.Integer, nullable=False)  # Perda de energia
    item_16 = db.Column(db.Integer, nullable=False)  # Mudanças no sono
    item_17 = db.Column(db.Integer, nullable=False)  # Irritabilidade
    item_18 = db.Column(db.Integer, nullable=False)  # Mudanças no apetite
    item_19 = db.Column(db.Integer, nullable=False)  # Dificuldade de concentração
    item_20 = db.Column(db.Integer, nullable=False)  # Cansaço/fadiga
    item_21 = db.Column(db.Integer, nullable=False)  # Perda de interesse sexual

    # Resultados da análise
    pontuacao_total = db.Column(db.Integer, nullable=False)
    nivel_depressao = db.Column(
        db.String, nullable=False
    )  # minima, leve, moderada, grave
    depressao_positiva = db.Column(
        db.Boolean, nullable=False
    )  # True se pontuação >= 14

    # Metadados
    data_realizacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    observacoes = db.Column(db.Text)

    # Relacionamentos
    paciente = db.relationship("Paciente", backref="beck_depression_testes")
    profissional = db.relationship("Profissional", backref="beck_depression_testes")

    def calcular_resultados(self):
        """Calcula os resultados baseado nas respostas"""
        # Soma de todos os itens
        pontuacao_total = sum(getattr(self, f"item_{i}") for i in range(1, 22))

        # Classificação baseada na pontuação total
        if pontuacao_total <= 13:
            nivel_depressao = "minima"
        elif pontuacao_total <= 19:
            nivel_depressao = "leve"
        elif pontuacao_total <= 28:
            nivel_depressao = "moderada"
        else:
            nivel_depressao = "grave"

        # Depressão positiva se pontuação >= 14 (critério clínico)
        depressao_positiva = pontuacao_total >= 14

        return {
            "pontuacao_total": pontuacao_total,
            "nivel_depressao": nivel_depressao,
            "depressao_positiva": depressao_positiva,
        }

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "profissional_id": self.profissional_id,
            "profissional_nome": self.profissional.nome if self.profissional else None,
            "respostas": {
                f"item_{i}": getattr(self, f"item_{i}") for i in range(1, 22)
            },
            "resultados": {
                "pontuacao_total": self.pontuacao_total,
                "nivel_depressao": self.nivel_depressao,
                "depressao_positiva": self.depressao_positiva,
            },
            "data_realizacao": self.data_realizacao.isoformat()
            if self.data_realizacao
            else None,
            "observacoes": self.observacoes,
        }


class PHQ9Teste(db.Model):
    __tablename__ = "phq9_testes"

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissionais.id", ondelete="SET NULL")
    )

    # Respostas das 9 perguntas do PHQ-9 (0-3)
    q1 = db.Column(
        db.Integer, nullable=False
    )  # Pouco interesse ou pouco prazer em fazer as coisas
    q2 = db.Column(
        db.Integer, nullable=False
    )  # Sentir-se para baixo, deprimido ou sem esperanças
    q3 = db.Column(
        db.Integer, nullable=False
    )  # Dificuldade para pegar no sono ou permanecer dormindo, ou dormir demais
    q4 = db.Column(db.Integer, nullable=False)  # Sentir-se cansado ou com pouca energia
    q5 = db.Column(db.Integer, nullable=False)  # Falta de apetite ou comer demais
    q6 = db.Column(db.Integer, nullable=False)  # Sentir-se mal consigo mesmo
    q7 = db.Column(
        db.Integer, nullable=False
    )  # Dificuldade de concentração nas atividades
    q8 = db.Column(db.Integer, nullable=False)  # Lentidão ou agitação excessiva
    q9 = db.Column(
        db.Integer, nullable=False
    )  # Pensamentos de que seria melhor estar morto ou de se ferir

    # Resultados da análise
    pontuacao_total = db.Column(db.Integer, nullable=False)
    nivel_depressao = db.Column(
        db.String, nullable=False
    )  # minima, leve, moderada, moderadamente_grave, grave
    depressao_positiva = db.Column(
        db.Boolean, nullable=False
    )  # True se pontuação >= 10
    risco_suicida = db.Column(db.Boolean, nullable=False)  # True se Q9 >= 1

    # Metadados
    data_realizacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    observacoes = db.Column(db.Text)

    # Relacionamentos
    paciente = db.relationship("Paciente", backref="phq9_testes")
    profissional = db.relationship("Profissional", backref="phq9_testes")

    def calcular_resultados(self):
        """Calcula os resultados baseado nas respostas do PHQ-9"""
        # Soma de todos os itens (0-27)
        pontuacao_total = sum(
            [
                self.q1,
                self.q2,
                self.q3,
                self.q4,
                self.q5,
                self.q6,
                self.q7,
                self.q8,
                self.q9,
            ]
        )

        # Classificação baseada na pontuação total
        if pontuacao_total <= 4:
            nivel_depressao = "minima"
        elif pontuacao_total <= 9:
            nivel_depressao = "leve"
        elif pontuacao_total <= 14:
            nivel_depressao = "moderada"
        elif pontuacao_total <= 19:
            nivel_depressao = "moderadamente_grave"
        else:
            nivel_depressao = "grave"

        # Depressão positiva se pontuação >= 10 (critério clínico)
        depressao_positiva = pontuacao_total >= 10

        # Risco suicida se Q9 >= 1
        risco_suicida = self.q9 >= 1

        return {
            "pontuacao_total": pontuacao_total,
            "nivel_depressao": nivel_depressao,
            "depressao_positiva": depressao_positiva,
            "risco_suicida": risco_suicida,
        }

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "profissional_id": self.profissional_id,
            "profissional_nome": self.profissional.nome if self.profissional else None,
            "respostas": {
                "q1": self.q1,
                "q2": self.q2,
                "q3": self.q3,
                "q4": self.q4,
                "q5": self.q5,
                "q6": self.q6,
                "q7": self.q7,
                "q8": self.q8,
                "q9": self.q9,
            },
            "resultados": {
                "pontuacao_total": self.pontuacao_total,
                "nivel_depressao": self.nivel_depressao,
                "depressao_positiva": self.depressao_positiva,
                "risco_suicida": self.risco_suicida,
            },
            "data_realizacao": self.data_realizacao.isoformat()
            if self.data_realizacao
            else None,
            "observacoes": self.observacoes,
        }


class GAD7Teste(db.Model):
    __tablename__ = "gad7_testes"

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(
        db.Integer, db.ForeignKey("pacientes.id", ondelete="CASCADE"), nullable=False
    )
    profissional_id = db.Column(
        db.Integer, db.ForeignKey("profissionais.id", ondelete="SET NULL")
    )

    # Respostas das 7 perguntas do GAD-7 (0-3)
    q1 = db.Column(
        db.Integer, nullable=False
    )  # Sentindo-se nervoso, ansioso ou muito tenso
    q2 = db.Column(
        db.Integer, nullable=False
    )  # Não sendo capaz de impedir ou de controlar as preocupações
    q3 = db.Column(
        db.Integer, nullable=False
    )  # Preocupando-se muito com diversas coisas
    q4 = db.Column(db.Integer, nullable=False)  # Tendo dificuldade para relaxar
    q5 = db.Column(
        db.Integer, nullable=False
    )  # Ficando tão agitado que se torna difícil permanecer sentado
    q6 = db.Column(
        db.Integer, nullable=False
    )  # Ficando facilmente aborrecido ou irritado
    q7 = db.Column(
        db.Integer, nullable=False
    )  # Sentindo medo como se algo horrível fosse acontecer

    # Resultados da análise
    pontuacao_total = db.Column(db.Integer, nullable=False)
    nivel_ansiedade = db.Column(
        db.String, nullable=False
    )  # minima, leve, moderada, grave
    ansiedade_positiva = db.Column(
        db.Boolean, nullable=False
    )  # True se pontuação >= 10

    # Metadados
    data_realizacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    observacoes = db.Column(db.Text)

    # Relacionamentos
    paciente = db.relationship("Paciente", backref="gad7_testes")
    profissional = db.relationship("Profissional", backref="gad7_testes")

    def calcular_resultados(self):
        """Calcula os resultados baseado nas respostas do GAD-7"""
        # Soma de todos os itens (0-21)
        pontuacao_total = sum(
            [self.q1, self.q2, self.q3, self.q4, self.q5, self.q6, self.q7]
        )

        # Classificação baseada na pontuação total
        if pontuacao_total <= 4:
            nivel_ansiedade = "minima"
        elif pontuacao_total <= 9:
            nivel_ansiedade = "leve"
        elif pontuacao_total <= 14:
            nivel_ansiedade = "moderada"
        else:
            nivel_ansiedade = "grave"

        # Ansiedade positiva se pontuação >= 10 (critério clínico comum)
        ansiedade_positiva = pontuacao_total >= 10

        return {
            "pontuacao_total": pontuacao_total,
            "nivel_ansiedade": nivel_ansiedade,
            "ansiedade_positiva": ansiedade_positiva,
        }

    def to_dict(self):
        return {
            "id": self.id,
            "paciente_id": self.paciente_id,
            "profissional_id": self.profissional_id,
            "profissional_nome": self.profissional.nome if self.profissional else None,
            "respostas": {
                "q1": self.q1,
                "q2": self.q2,
                "q3": self.q3,
                "q4": self.q4,
                "q5": self.q5,
                "q6": self.q6,
                "q7": self.q7,
            },
            "resultados": {
                "pontuacao_total": self.pontuacao_total,
                "nivel_ansiedade": self.nivel_ansiedade,
                "ansiedade_positiva": self.ansiedade_positiva,
            },
            "data_realizacao": self.data_realizacao.isoformat()
            if self.data_realizacao
            else None,
            "observacoes": self.observacoes,
        }


class UploadSession(db.Model):
    __tablename__ = "upload_sessions"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String, unique=True, nullable=False)
    status = db.Column(
        db.String, default="pending", nullable=False
    )  # pending, completed, failed
    context = db.Column(
        db.String(50), default="exam", nullable=False
    )  # 'exam' or 'product'
    file_path = db.Column(db.String, nullable=True)
    file_type = db.Column(db.String, nullable=True)  # image/jpeg, audio/webm, etc
    original_filename = db.Column(db.String, nullable=True)
    ai_result = db.Column(
        db.JSON, nullable=True
    )  # Store AI extraction result for products
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "token": self.token,
            "status": self.status,
            "context": self.context,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "original_filename": self.original_filename,
            "ai_result": self.ai_result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class Disponibilidade(db.Model):
    __tablename__ = "disponibilidades"

    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(
        db.Integer,
        db.ForeignKey("profissionais.id", ondelete="CASCADE"),
        nullable=False,
    )
    dia_semana = db.Column(
        db.Integer, nullable=False
    )  # 0=domingo, 1=segunda, ..., 6=sabado
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fim = db.Column(db.Time, nullable=False)
    duracao_consulta_minutos = db.Column(db.Integer, default=60)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    profissional = db.relationship(
        "Profissional", backref=db.backref("disponibilidades", lazy=True)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "profissional_id": self.profissional_id,
            "dia_semana": self.dia_semana,
            "hora_inicio": self.hora_inicio.strftime("%H:%M")
            if self.hora_inicio
            else None,
            "hora_fim": self.hora_fim.strftime("%H:%M") if self.hora_fim else None,
            "duracao_consulta_minutos": self.duracao_consulta_minutos,
            "ativo": self.ativo,
        }


class Consultorio(db.Model):
    """Consultório/sala de uma clínica (tenant-scoped via associacao_id).

    Parte da feature feat/intelligent-import: criado quando o gestor importa
    uma lista de consultórios via IntelligentImportService.
    """
    __tablename__ = "consultorios"

    id = db.Column(db.Integer, primary_key=True)
    associacao_id = db.Column(
        db.Integer,
        db.ForeignKey("associacoes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nome = db.Column(db.String(120), nullable=False)
    andar = db.Column(db.String(40))
    ala = db.Column(db.String(40))
    capacidade = db.Column(db.Integer, default=1)
    recursos = db.Column(db.Text)  # ex.: "macas=2,balança,computador"
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("associacao_id", "nome", name="uq_consultorio_assoc_nome"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "associacao_id": self.associacao_id,
            "nome": self.nome,
            "andar": self.andar,
            "ala": self.ala,
            "capacidade": self.capacidade,
            "recursos": self.recursos,
            "ativo": self.ativo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }