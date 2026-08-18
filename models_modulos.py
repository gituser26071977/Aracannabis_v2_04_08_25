"""
Modelos de Módulos de Especialidade (Fase 4 pre-deploy).

Catálogo de módulos complementares que o profissional pode ativar (com trial 14 dias)
independentemente do seu plano principal:
  - `base` (sempre incluso, sem assinatura)
  - `cannabis-medicinal`
  - `nutrologia`
  - `psiquiatria`
  - `cardiologia`
  - `pesquisa-clinica`

Cada módulo tem uma assinatura por profissional com status
(trial/active/expired/cancelled) e termo de consentimento LGPD registrado.
"""
from datetime import datetime, timedelta
from models import db


# Duração padrão do trial gratuito
TRIAL_DAYS = 14


class Modulo(db.Model):
    """Catálogo de módulos de especialidade disponíveis."""

    __tablename__ = "modulos"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text)
    descricao_curta = db.Column(db.String(200))
    icone = db.Column(db.String(64), default="extension")  # nome do ícone MUI
    cor = db.Column(db.String(16), default="#0d7377")  # cor hex para UI
    preco_mensal = db.Column(db.Float, default=0.0)
    plano_minimo_slug = db.Column(db.String(64), default="basico")
    ordem = db.Column(db.Integer, default=100)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    requer_consentimento_lgpd = db.Column(db.Boolean, default=True, nullable=False)
    politica_versao = db.Column(db.String(16), default="v1")  # versão do termo

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "slug": self.slug,
            "nome": self.nome,
            "descricao": self.descricao,
            "descricao_curta": self.descricao_curta,
            "icone": self.icone,
            "cor": self.cor,
            "preco_mensal": self.preco_mensal,
            "plano_minimo_slug": self.plano_minimo_slug,
            "ordem": self.ordem,
            "ativo": self.ativo,
            "requer_consentimento_lgpd": self.requer_consentimento_lgpd,
            "politica_versao": self.politica_versao,
        }


class ModuloAssinatura(db.Model):
    """Vínculo entre profissional e módulo (com status + datas)."""

    __tablename__ = "modulos_assinaturas"

    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(
        db.Integer,
        db.ForeignKey("profissionais.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    modulo_id = db.Column(
        db.Integer,
        db.ForeignKey("modulos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # trial | active | expired | cancelled
    status = db.Column(db.String(16), nullable=False, default="trial")
    trial_iniciado_em = db.Column(db.DateTime)
    trial_expira_em = db.Column(db.DateTime)
    ativo_desde = db.Column(db.DateTime)
    expira_em = db.Column(db.DateTime)
    cancelado_em = db.Column(db.DateTime)
    # idempotência: chave única trial-1x por (profissional, modulo)
    __table_args__ = (
        db.UniqueConstraint(
            "profissional_id", "modulo_id", name="uq_modulo_assinatura_user_mod"
        ),
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # helpers REDACTED
    def is_acesso_ativo(self) -> bool:
        if self.status not in ("trial", "active"):
            return False
        if self.status == "trial" and self.trial_expira_em:
            return datetime.utcnow() < self.trial_expira_em
        if self.status == "active" and self.expira_em:
            return datetime.utcnow() < self.expira_em
        return False

    def dias_restantes(self) -> int:
        if self.status == "trial" and self.trial_expira_em:
            delta = self.trial_expira_em - datetime.utcnow()
            return max(0, delta.days)
        if self.status == "active" and self.expira_em:
            delta = self.expira_em - datetime.utcnow()
            return max(0, delta.days)
        return 0

    def to_dict(self, modulo: "Modulo" = None) -> dict:
        out = {
            "id": self.id,
            "profissional_id": self.profissional_id,
            "modulo_id": self.modulo_id,
            "status": self.status,
            "trial_iniciado_em": self.trial_iniciado_em.isoformat()
            if self.trial_iniciado_em
            else None,
            "trial_expira_em": self.trial_expira_em.isoformat()
            if self.trial_expira_em
            else None,
            "ativo_desde": self.ativo_desde.isoformat() if self.ativo_desde else None,
            "expira_em": self.expira_em.isoformat() if self.expira_em else None,
            "cancelado_em": self.cancelado_em.isoformat() if self.cancelado_em else None,
            "acesso_ativo": self.is_acesso_ativo(),
            "dias_restantes": self.dias_restantes(),
        }
        if modulo is not None:
            out["modulo"] = modulo.to_dict()
        return out


class ModuloConsentimento(db.Model):
    """Registro do consentimento LGPD do profissional para um módulo."""

    __tablename__ = "modulos_consentimentos"

    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(
        db.Integer,
        db.ForeignKey("profissionais.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    modulo_id = db.Column(
        db.Integer,
        db.ForeignKey("modulos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    aceito = db.Column(db.Boolean, nullable=False, default=False)
    politica_versao = db.Column(db.String(16), nullable=False)
    ip_origem = db.Column(db.String(64))
    user_agent = db.Column(db.String(256))
    aceito_em = db.Column(db.DateTime)
    revogado_em = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "profissional_id": self.profissional_id,
            "modulo_id": self.modulo_id,
            "aceito": self.aceito,
            "politica_versao": self.politica_versao,
            "ip_origem": self.ip_origem,
            "user_agent": self.user_agent,
            "aceito_em": self.aceito_em.isoformat() if self.aceito_em else None,
            "revogado_em": self.revogado_em.isoformat() if self.revogado_em else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


__all__ = [
    "Modulo",
    "ModuloAssinatura",
    "ModuloConsentimento",
    "TRIAL_DAYS",
    "MODULOS_CATALOGO",
    "seed_modulos_catalogo",
]


# ═══════════════════════════════════════════════════════════════════════
# Catálogo canônico de módulos (idempotente)
# ═══════════════════════════════════════════════════════════════════════
MODULOS_CATALOGO = [
    {
        "slug": "base",
        "nome": "Módulo Base (Clínica Médica)",
        "descricao": "Prontuário, agenda, receituário e fluxos clínicos essenciais.",
        "descricao_curta": "Fluxos essenciais do dia a dia",
        "preco_mensal": 0.0,
        "plano_minimo_slug": "basico",
        "ordem": 0,
    },
    {
        "slug": "cannabis-medicinal",
        "nome": "Cannabis Medicinal",
        "descricao": "Prescrição e rastreio de cannabis medicinal (dosagens, concentrações, acompanhamento).",
        "descricao_curta": "Prescrição e rastreio canábico",
        "preco_mensal": 99.0,
        "plano_minimo_slug": "premium",
        "ordem": 10,
    },
    {
        "slug": "nutrologia",
        "nome": "Nutrologia",
        "descricao": "Avaliação nutricional, planos alimentares e acompanhamento de metas.",
        "descricao_curta": "Avaliação e planos nutricionais",
        "preco_mensal": 89.0,
        "plano_minimo_slug": "basico",
        "ordem": 20,
    },
    {
        "slug": "psiquiatria",
        "nome": "Psiquiatria",
        "descricao": "Escalas psiquiátricas (PHQ-9, GAD-7, Beck), prescrição e acompanhamento.",
        "descricao_curta": "Escalas e acompanhamento psiquiátrico",
        "preco_mensal": 89.0,
        "plano_minimo_slug": "basico",
        "ordem": 30,
    },
    {
        "slug": "cardiologia",
        "nome": "Cardiologia",
        "descricao": "Avaliação cardiovascular, fatores de risco e acompanhamento.",
        "descricao_curta": "Avaliação e acompanhamento cardiovascular",
        "preco_mensal": 89.0,
        "plano_minimo_slug": "premium",
        "ordem": 40,
    },
    {
        "slug": "nefrologia",
        "nome": "Nefrologia",
        "descricao": "Avaliação renal, função glomerular, diálise e acompanhamento.",
        "descricao_curta": "Avaliação e acompanhamento renal",
        "preco_mensal": 89.0,
        "plano_minimo_slug": "premium",
        "ordem": 50,
    },
    {
        "slug": "oncologia",
        "nome": "Oncologia",
        "descricao": "Acompanhamento oncológico, esquemas de tratamento e toxicidade.",
        "descricao_curta": "Acompanhamento oncológico",
        "preco_mensal": 129.0,
        "plano_minimo_slug": "premium",
        "ordem": 60,
    },
    {
        "slug": "pediatria",
        "nome": "Pediatria",
        "descricao": "Puericultura, curvas de crescimento, imunização e acompanhamento pediátrico.",
        "descricao_curta": "Puericultura e acompanhamento pediátrico",
        "preco_mensal": 89.0,
        "plano_minimo_slug": "basico",
        "ordem": 70,
    },
    {
        "slug": "geriatria",
        "nome": "Geriatria",
        "descricao": "Avaliação geriátrica ampla, risco de queda, polifarmácia e acompanhamento.",
        "descricao_curta": "Avaliação geriátrica ampla",
        "preco_mensal": 89.0,
        "plano_minimo_slug": "basico",
        "ordem": 80,
    },
    {
        "slug": "pesquisa-clinica",
        "nome": "Pesquisa Clínica",
        "descricao": "Coortes, correlacões e relatórios de evidência para pesquisa.",
        "descricao_curta": "Coortes e evidência para pesquisa",
        "preco_mensal": 149.0,
        "plano_minimo_slug": "enterprise",
        "ordem": 90,
    },
]


def seed_modulos_catalogo() -> list[Modulo]:
    """Garante o catálogo canônico no banco (idempotente).

    Cria/atualiza os módulos por slug. Retorna a lista de módulos ativos.
    """
    criados: list[Modulo] = []
    for data in MODULOS_CATALOGO:
        m = Modulo.query.filter_by(slug=data["slug"]).first()
        if not m:
            m = Modulo(**data)
            db.session.add(m)
        else:
            for k, v in data.items():
                setattr(m, k, v)
        criados.append(m)
    db.session.commit()
    return criados