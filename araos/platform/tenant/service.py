"""
AraOS Platform — Tenant Service.

Serviço de domínio para operações de tenant.
Não é CRUD — é orquestração de plataforma.
"""

from typing import Optional, List, Dict, Any

from araos.platform.shared.context import TenantContext
from araos.platform.shared.errors import (
    TenantNotFoundError,
    ValidationError,
    TenantFeatureNotEnabledError,
)
from .models import (
    Organization,
    Clinic,
    Professional,
    User,
    ServiceAccount,
    FeatureFlag,
)


class TenantService:
    """
    Serviço de tenant para operações de plataforma.
    
    Responsabilidades:
        - Criar/gerenciar organizações
        - Gerenciar clínicas
        - Gerenciar profissionais e usuários
        - Gerenciar service accounts
        - Resolver feature flags por contexto
    """
    
    def __init__(self, db_session):
        self.db = db_session
    
    # ─── Organization ────────────────────────────────────────────────
    
    def create_organization(
        self,
        name: str,
        slug: str,
        plan: str = "free",
        document: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Organization:
        """Cria nova organização."""
        org = Organization(
            name=name,
            slug=slug,
            document=document,
            plan=plan,
            settings=settings or {},
        )
        self.db.add(org)
        self.db.commit()
        self.db.refresh(org)
        return org
    
    def get_organization(self, org_id: str) -> Optional[Organization]:
        """Busca organização por ID."""
        return self.db.query(Organization).filter(
            Organization.id == org_id,
            Organization.deleted_at.is_(None),
        ).first()
    
    def get_organization_by_slug(self, slug: str) -> Optional[Organization]:
        """Busca organização por slug."""
        return self.db.query(Organization).filter(
            Organization.slug == slug,
            Organization.deleted_at.is_(None),
        ).first()
    
    def list_organizations(
        self,
        status: Optional[str] = None,
        plan: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Organization]:
        """Lista organizações com filtros."""
        query = self.db.query(Organization).filter(Organization.deleted_at.is_(None))
        
        if status:
            query = query.filter(Organization.status == status)
        if plan:
            query = query.filter(Organization.plan == plan)
        
        return query.order_by(Organization.created_at.desc()).offset(offset).limit(limit).all()
    
    def update_organization(
        self,
        org_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Organization]:
        """Atualiza organização."""
        org = self.get_organization(org_id)
        if not org:
            return None
        
        allowed = {"name", "slug", "plan", "status", "settings", "primary_color", "logo_url"}
        for key, value in updates.items():
            if key in allowed:
                setattr(org, key, value)
        
        self.db.commit()
        self.db.refresh(org)
        return org
    
    # ─── Clinic ──────────────────────────────────────────────────────
    
    def create_clinic(
        self,
        organization_id: str,
        name: str,
        timezone: str = "America/Sao_Paulo",
        settings: Optional[Dict[str, Any]] = None,
    ) -> Clinic:
        """Cria clínica dentro de organização."""
        clinic = Clinic(
            organization_id=organization_id,
            name=name,
            timezone=timezone,
            settings=settings or {},
        )
        self.db.add(clinic)
        self.db.commit()
        self.db.refresh(clinic)
        return clinic
    
    def get_clinic(self, clinic_id: str) -> Optional[Clinic]:
        """Busca clínica por ID."""
        return self.db.query(Clinic).filter(
            Clinic.id == clinic_id,
            Clinic.deleted_at.is_(None),
        ).first()
    
    def list_clinics_by_organization(
        self, org_id: str, active_only: bool = True
    ) -> List[Clinic]:
        """Lista clínicas de uma organização."""
        query = self.db.query(Clinic).filter(
            Clinic.organization_id == org_id,
            Clinic.deleted_at.is_(None),
        )
        if active_only:
            query = query.filter(Clinic.active == True)
        return query.all()
    
    # ─── Professional ────────────────────────────────────────────────
    
    def create_professional(
        self,
        organization_id: str,
        full_name: str,
        specialty: Optional[str] = None,
        professional_registry: Optional[str] = None,
        clinic_ids: Optional[List[str]] = None,
    ) -> Professional:
        """Cria profissional."""
        prof = Professional(
            organization_id=organization_id,
            full_name=full_name,
            specialty=specialty,
            professional_registry=professional_registry,
            clinic_ids=clinic_ids or [],
        )
        self.db.add(prof)
        self.db.commit()
        self.db.refresh(prof)
        return prof
    
    def get_professional(self, prof_id: str) -> Optional[Professional]:
        """Busca profissional por ID."""
        return self.db.query(Professional).filter(
            Professional.id == prof_id,
            Professional.deleted_at.is_(None),
        ).first()
    
    def list_professionals_by_organization(
        self, org_id: str
    ) -> List[Professional]:
        """Lista profissionais de organização."""
        return self.db.query(Professional).filter(
            Professional.organization_id == org_id,
            Professional.deleted_at.is_(None),
        ).all()
    
    # ─── User ────────────────────────────────────────────────────────
    
    def create_user(
        self,
        organization_id: str,
        email: str,
        password_hash: str,
        full_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        clinic_ids: Optional[List[str]] = None,
    ) -> User:
        """Cria usuário."""
        user = User(
            organization_id=organization_id,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            roles=roles or ["viewer"],
            clinic_ids=clinic_ids or [],
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Busca usuário por ID."""
        return self.db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None),
        ).first()
    
    def get_user_by_email(
        self, organization_id: str, email: str
    ) -> Optional[User]:
        """Busca usuário por email dentro de organização."""
        return self.db.query(User).filter(
            User.organization_id == organization_id,
            User.email == email,
            User.deleted_at.is_(None),
        ).first()
    
    # ─── Service Account ─────────────────────────────────────────────
    
    def create_service_account(
        self,
        organization_id: str,
        name: str,
        service_type: str,
        api_key_hash: str,
        api_key_prefix: str,
        permissions: Optional[List[str]] = None,
    ) -> ServiceAccount:
        """Cria service account."""
        svc = ServiceAccount(
            organization_id=organization_id,
            name=name,
            service_type=service_type,
            api_key_hash=api_key_hash,
            api_key_prefix=api_key_prefix,
            permissions=permissions or [],
        )
        self.db.add(svc)
        self.db.commit()
        self.db.refresh(svc)
        return svc
    
    def get_service_account(self, svc_id: str) -> Optional[ServiceAccount]:
        """Busca service account por ID."""
        return self.db.query(ServiceAccount).filter(
            ServiceAccount.id == svc_id,
            ServiceAccount.deleted_at.is_(None),
        ).first()
    
    # ─── Feature Flags ───────────────────────────────────────────────
    
    def get_feature_flags(
        self, organization_id: str
    ) -> List[FeatureFlag]:
        """Lista feature flags de organização."""
        return self.db.query(FeatureFlag).filter(
            FeatureFlag.organization_id == organization_id,
        ).all()
    
    def is_feature_enabled(
        self,
        organization_id: str,
        flag_key: str,
        user_id: Optional[str] = None,
        plan: Optional[str] = None,
    ) -> bool:
        """
        Verifica se feature está habilitada.
        
        Resolução por precedência:
            1. Override por usuário
            2. Override por tenant
            3. Por plano
            4. Global (default)
        """
        flags = self.db.query(FeatureFlag).filter(
            FeatureFlag.organization_id == organization_id,
            FeatureFlag.key == flag_key,
            FeatureFlag.enabled == True,
        ).all()
        
        if not flags:
            return False
        
        # Precedência: user > tenant > plan > global
        for flag in flags:
            if flag.scope == "user" and flag.target == user_id:
                return True
            if flag.scope == "tenant" and flag.target == organization_id:
                return True
            if flag.scope == "plan" and flag.target == plan:
                return True
            if flag.scope == "global":
                return True
        
        return False
    
    def set_feature_flag(
        self,
        organization_id: str,
        flag_key: str,
        enabled: bool,
        scope: str = "global",
        target: Optional[str] = None,
    ) -> FeatureFlag:
        """Define feature flag."""
        flag = self.db.query(FeatureFlag).filter(
            FeatureFlag.organization_id == organization_id,
            FeatureFlag.key == flag_key,
            FeatureFlag.scope == scope,
            FeatureFlag.target == target,
        ).first()
        
        if flag:
            flag.enabled = enabled
        else:
            flag = FeatureFlag(
                organization_id=organization_id,
                key=flag_key,
                enabled=enabled,
                scope=scope,
                target=target,
            )
            self.db.add(flag)
        
        self.db.commit()
        self.db.refresh(flag)
        return flag
    
    # ─── TenantContext Builder ───────────────────────────────────────
    
    def build_tenant_context(
        self,
        organization_id: str,
        user_id: Optional[str] = None,
        clinic_id: Optional[str] = None,
    ) -> TenantContext:
        """
        Constrói TenantContext completo a partir de IDs.
        
        Usado pelo resolver após autenticação.
        """
        org = self.get_organization(organization_id)
        if not org:
            raise TenantNotFoundError(organization_id)
        
        # Buscar usuário para roles
        roles = []
        if user_id and not user_id.startswith("svc:"):
            user = self.get_user(user_id)
            if user:
                roles = user.roles or []
        elif user_id and user_id.startswith("svc:"):
            roles = ["service_account"]
        
        # Feature flags ativas
        features = self._get_active_features(organization_id, user_id, org.plan)
        
        return TenantContext(
            tenant_id=org.id,
            organization_id=org.id,
            clinic_id=clinic_id,
            user_id=user_id,
            roles=roles,
            features=features,
            plan=org.plan,
            authenticated=user_id is not None,
        )
    
    def _get_active_features(
        self,
        organization_id: str,
        user_id: Optional[str] = None,
        plan: Optional[str] = None,
    ) -> List[str]:
        """Retorna lista de features ativas para o contexto."""
        flags = self.db.query(FeatureFlag).filter(
            FeatureFlag.organization_id == organization_id,
            FeatureFlag.enabled == True,
        ).all()
        
        active = []
        for flag in flags:
            if flag.scope == "global":
                active.append(flag.key)
            elif flag.scope == "tenant" and flag.target == organization_id:
                active.append(flag.key)
            elif flag.scope == "user" and flag.target == user_id:
                active.append(flag.key)
            elif flag.scope == "plan" and flag.target == plan:
                active.append(flag.key)
        
        return list(set(active))  # Remove duplicatas
