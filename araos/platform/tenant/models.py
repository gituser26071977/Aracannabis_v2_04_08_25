"""
AraOS Platform — Tenant Layer Models.

Modelos canônicos de tenancy. TODAS as entidades da plataforma
referenciam esses modelos.

Compatibilidade:
    - SQLAlchemy 2.0+ (declarative, Mapped, mapped_column)
    - Funciona com Flask (SIAP) e FastAPI (Voice, Smart Flow)
    - Não depende de Flask-SQLAlchemy

Regra de ouro:
    Toda entidade de domínio tem tenant_id obrigatório.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    String, Text, Boolean, DateTime, ForeignKey, JSON, Index, UniqueConstraint, Integer
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarativa da Platform Layer."""
    pass


def generate_uuid() -> str:
    """Gera UUID4 como string."""
    return str(uuid.uuid4())


def now_utc() -> datetime:
    """Retorna datetime UTC atual."""
    return datetime.now(timezone.utc)


class AuditFieldsMixin:
    """
    Mixin com campos de auditoria completos (LGPD/SOC2 friendly).

    Adiciona created_by / updated_by / deleted_by aos modelos que
    precisam de rastreabilidade humana (não apenas timestamps automáticos).

    Aplicado em módulos greenfield — módulos legados (ex.: cannabis db_models)
    continuam sem o mixin até migração específica.

    Uso:
        class NeuroPatientProfile(AuditFieldsMixin, Base):
            __tablename__ = "neuro_patient_profiles"
            ...
    """

    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    deleted_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    # created_at / updated_at / deleted_at continuam na própria entidade
    # (declarados em cada model para manter clareza do schema)


# ═══════════════════════════════════════════════════════════════════════
# ENTIDADE 1: ORGANIZATION
# ═══════════════════════════════════════════════════════════════════════

class Organization(Base):
    """
    Quem contrata e paga pela plataforma.
    
    Exemplos: Clínica ABC, Hospital XYZ, Rede Saúde+
    """
    __tablename__ = "araos_organizations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # CNPJ/CPF
    
    # Plano e status
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    # active, suspended, cancelled, trial, pending_payment
    
    # Branding
    primary_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Configurações JSON
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    clinics: Mapped[List["Clinic"]] = relationship(
        "Clinic", back_populates="organization", lazy="selectin"
    )
    professionals: Mapped[List["Professional"]] = relationship(
        "Professional", back_populates="organization", lazy="selectin"
    )
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="organization", lazy="selectin"
    )
    service_accounts: Mapped[List["ServiceAccount"]] = relationship(
        "ServiceAccount", back_populates="organization", lazy="selectin"
    )
    feature_flags: Mapped[List["FeatureFlag"]] = relationship(
        "FeatureFlag", back_populates="organization", lazy="selectin"
    )
    
    __table_args__ = (
        Index("ix_org_status_plan", "status", "plan"),
        Index("ix_org_document", "document"),
    )
    
    def is_active(self) -> bool:
        return self.status == "active" and self.deleted_at is None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "plan": self.plan,
            "status": self.status,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ═══════════════════════════════════════════════════════════════════════
# ENTIDADE 2: CLINIC
# ═══════════════════════════════════════════════════════════════════════

class Clinic(Base):
    """
    Unidade operacional.
    
    Uma organização pode ter várias clínicas.
    Exemplo: Hospital XYZ → Unidade Centro, Unidade Sul, Unidade Norte
    """
    __tablename__ = "araos_clinics"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("araos_organizations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Endereço
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Operação
    timezone: Mapped[str] = mapped_column(String(50), default="America/Sao_Paulo")
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Configurações
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    organization: Mapped["Organization"] = relationship("Organization", back_populates="clinics")
    
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_clinic_org_slug"),
        UniqueConstraint("organization_id", "code", name="uq_clinic_org_code"),
        Index("ix_clinic_org_active", "organization_id", "active"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
            "timezone": self.timezone,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ═══════════════════════════════════════════════════════════════════════
# ENTIDADE 3: PROFESSIONAL
# ═══════════════════════════════════════════════════════════════════════

class Professional(Base):
    """
    Prestador de serviço.
    
    Pode atuar em múltiplas clínicas.
    NÃO é conta de acesso — é a identidade profissional.
    """
    __tablename__ = "araos_professionals"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("araos_organizations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    
    # Dados pessoais
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Especialidade e registro
    specialty: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    professional_registry: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # CRM/CRP/etc
    registry_state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    # active, inactive, suspended, pending_validation
    
    # Clínicas onde atua (muitos-para-muitos via JSON por simplicidade inicial)
    # Futuro: tabela de junção araos_professional_clinics
    clinic_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Configurações
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    organization: Mapped["Organization"] = relationship("Organization", back_populates="professionals")
    
    __table_args__ = (
        Index("ix_professional_org_status", "organization_id", "status"),
        Index("ix_professional_registry", "professional_registry"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "full_name": self.full_name,
            "specialty": self.specialty,
            "status": self.status,
            "clinic_ids": self.clinic_ids,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ═══════════════════════════════════════════════════════════════════════
# ENTIDADE 4: USER
# ═══════════════════════════════════════════════════════════════════════

class User(Base):
    """
    Conta de acesso.
    
    Representa quem pode fazer login.
    Pode acessar múltiplas clínicas.
    """
    __tablename__ = "araos_users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("araos_organizations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    
    # Credenciais
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Perfil
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Papéis (RBAC)
    roles: Mapped[List[str]] = mapped_column(JSON, default=list)
    # admin, doctor, nurse, receptionist, manager, viewer
    
    # Permissões explícitas (sobrescrevem roles)
    permissions: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Clínicas acessíveis (null = todas da organização)
    clinic_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Login
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    login_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")
    
    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_user_org_email"),
        Index("ix_user_org_active", "organization_id", "active"),
    )
    
    def has_role(self, role: str) -> bool:
        return role in (self.roles or [])
    
    def has_permission(self, permission: str) -> bool:
        return permission in (self.permissions or [])
    
    def is_locked(self) -> bool:
        if self.locked_until and self.locked_until > now_utc():
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "email": self.email,
            "full_name": self.full_name,
            "roles": self.roles,
            "active": self.active,
            "email_verified": self.email_verified,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ═══════════════════════════════════════════════════════════════════════
# ENTIDADE 5: SERVICE ACCOUNT
# ═══════════════════════════════════════════════════════════════════════

class ServiceAccount(Base):
    """
    Ator não-humano.
    
    Representa agentes, integrações, webhooks, APIs externas.
    Cada service account tem sua própria API key.
    """
    __tablename__ = "araos_service_accounts"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("araos_organizations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tipo de serviço
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # concierge, voice, smart_flow, sdr, webhook, integration, api
    
    # API Key (hash, nunca plaintext)
    api_key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)
    
    # Permissões
    permissions: Mapped[List[str]] = mapped_column(JSON, default=list)
    
    # Rate limiting
    rate_limit_per_minute: Mapped[int] = mapped_column(Integer, default=60)
    
    # Escopo de clínicas (null = todas)
    clinic_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    
    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Último uso
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relacionamentos
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="service_accounts"
    )
    
    __table_args__ = (
        Index("ix_svc_acc_org_type", "organization_id", "service_type"),
        Index("ix_svc_acc_active", "organization_id", "active"),
    )
    
    def has_permission(self, permission: str) -> bool:
        return permission in (self.permissions or [])
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
            "service_type": self.service_type,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ═══════════════════════════════════════════════════════════════════════
# ENTIDADE 6: FEATURE FLAG
# ═══════════════════════════════════════════════════════════════════════

class FeatureFlag(Base):
    """
    Feature flag persistida.
    
    Controle granular de funcionalidades sem necessidade de deploy.
    """
    __tablename__ = "araos_feature_flags"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    organization_id: Mapped[str] = mapped_column(
        ForeignKey("araos_organizations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Estado
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Escopo: global | tenant | user | plan | environment | clinic
    scope: Mapped[str] = mapped_column(String(20), default="global", nullable=False)
    
    # Alvo do escopo (ex: user_id, plan_name, clinic_id)
    target: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Metadados adicionais
    flag_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, default=dict)
    
    # Controle de rollout (percentual 0-100)
    rollout_percentage: Mapped[int] = mapped_column(Integer, default=100)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )
    
    # Relacionamentos
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="feature_flags"
    )
    
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "key", "scope", "target",
            name="REDACTED"
        ),
        Index("ix_feature_flag_org_key", "organization_id", "key"),
        Index("ix_feature_flag_enabled", "organization_id", "enabled"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "key": self.key,
            "enabled": self.enabled,
            "scope": self.scope,
            "target": self.target,
            "rollout_percentage": self.rollout_percentage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
