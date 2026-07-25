"""
AraOS Platform — Permission Engine & Role Mapping.

Permissões explícitas, não apenas roles.
Roles são agrupamentos de permissões.

Suporta:
    - Resource-based permissions (patient.read, consultation.write)
    - Action-based permissions (voice.use, billing.manage)
    - Wildcard permissions (patient.* para leitura+escrita)
    - Hierarchical permissions (platform.admin herda tudo)
"""

from typing import Dict, List, Set, Optional, FrozenSet
from dataclasses import dataclass, field
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════
# PERMISSIONS
# ═══════════════════════════════════════════════════════════════════════

class Permission:
    """
    Permissão explicita da plataforma.
    
    Formato: {resource}.{action}
    Exemplos: patient.read, consultation.write, voice.use
    """
    
    # ─── Patient ─────────────────────────────────────────────────────
    PATIENT_READ = "patient.read"
    PATIENT_WRITE = "patient.write"
    PATIENT_DELETE = "patient.delete"
    PATIENT_EXPORT = "patient.export"
    PATIENT_MERGE = "patient.merge"
    
    # ─── Consultation ────────────────────────────────────────────────
    CONSULTATION_READ = "consultation.read"
    CONSULTATION_WRITE = "consultation.write"
    CONSULTATION_DELETE = "consultation.delete"
    CONSULTATION_SCHEDULE = "consultation.schedule"
    CONSULTATION_START = "consultation.start"
    CONSULTATION_FINISH = "consultation.finish"
    
    # ─── Clinical Record ─────────────────────────────────────────────
    EVOLUTION_READ = "evolution.read"
    EVOLUTION_WRITE = "evolution.write"
    PRESCRIPTION_WRITE = "prescription.write"
    PRESCRIPTION_READ = "prescription.read"
    EXAM_REQUEST = "exam.request"
    EXAM_READ = "exam.read"
    DIAGNOSIS_WRITE = "diagnosis.write"
    DIAGNOSIS_READ = "diagnosis.read"
    ALLERGY_WRITE = "allergy.write"
    MEDICATION_PRESCRIBE = "medication.prescribe"
    
    # ─── Document ────────────────────────────────────────────────────
    DOCUMENT_UPLOAD = "document.upload"
    DOCUMENT_READ = "document.read"
    DOCUMENT_DELETE = "document.delete"
    DOCUMENT_PROCESS = "document.process"
    
    # ─── Voice ───────────────────────────────────────────────────────
    VOICE_USE = "voice.use"
    VOICE_COMMAND_EXECUTE = "voice.command.execute"
    VOICE_SESSION_MANAGE = "voice.session.manage"
    
    # ─── Smart Flow ──────────────────────────────────────────────────
    SMART_FLOW_CHECKIN = "smart_flow.checkin"
    SMART_FLOW_MONITOR = "smart_flow.monitor"
    SMART_FLOW_CONFIGURE = "smart_flow.configure"
    
    # ─── Communication ───────────────────────────────────────────────
    COMMUNICATION_SEND = "communication.send"
    COMMUNICATION_READ = "communication.read"
    COMMUNICATION_TEMPLATE_MANAGE = "communication.template.manage"
    
    # ─── Billing ─────────────────────────────────────────────────────
    BILLING_READ = "billing.read"
    BILLING_MANAGE = "billing.manage"
    BILLING_INVOICE_CREATE = "billing.invoice.create"
    BILLING_PAYMENT_RECEIVE = "billing.payment.receive"
    SUBSCRIPTION_MANAGE = "subscription.manage"
    
    # ─── Platform ────────────────────────────────────────────────────
    PLATFORM_ADMIN = "platform.admin"
    PLATFORM_READ = "platform.read"
    PLATFORM_CONFIGURE = "platform.configure"
    PLATFORM_AUDIT_READ = "platform.audit.read"
    PLATFORM_AUDIT_EXPORT = "platform.audit.export"
    
    # ─── User Management ─────────────────────────────────────────────
    USER_READ = "user.read"
    USER_WRITE = "user.write"
    USER_DELETE = "user.delete"
    USER_IMPERSONATE = "user.impersonate"
    
    # ─── Professional Management ─────────────────────────────────────
    PROFESSIONAL_READ = "professional.read"
    PROFESSIONAL_WRITE = "professional.write"
    PROFESSIONAL_VALIDATE = "professional.validate"
    
    # ─── Clinic Management ───────────────────────────────────────────
    CLINIC_READ = "clinic.read"
    CLINIC_WRITE = "clinic.write"
    CLINIC_CONFIGURE = "clinic.configure"
    
    # ─── Feature Flags ───────────────────────────────────────────────
    FEATURE_FLAG_READ = "feature_flag.read"
    FEATURE_FLAG_WRITE = "feature_flag.write"
    
    # ─── AI / Agents ─────────────────────────────────────────────────
    AI_USE = "ai.use"
    AI_CONFIGURE = "ai.configure"
    AI_AGENT_DEPLOY = "ai.agent.deploy"
    
    # ─── LGPD / Compliance ───────────────────────────────────────────
    LGPD_EXPORT = "lgpd.export"
    LGPD_PURGE = "lgpd.purge"
    LGPD_AUDIT = "lgpd.audit"

    # ─── Neurodevelopmental Module ───────────────────────────────────
    # Plataforma de assistência, pesquisa, gestão e ensino em
    # neurodesenvolvimento (TEA, TDAH, AH/SD, Dupla Excepcionalidade, TOD,
    # Transtornos de Linguagem, Deficiência Intelectual, Transtornos de
    # Aprendizagem, Outras). Substitui e amplia o antigo "módulo TEA".
    NEURODEVELOPMENTAL_PROFILE_READ = "neurodevelopmental.profile.read"
    NEURODEVELOPMENTAL_PROFILE_WRITE = "neurodevelopmental.profile.write"
    NEURODEVELOPMENTAL_SCALE_APPLY = "neurodevelopmental.scale.apply"
    NEURODEVELOPMENTAL_SCALE_INTERPRET = "neurodevelopmental.scale.interpret"
    REDACTED = "neurodevelopmental.medication.prescribe"
    REDACTED = "neurodevelopmental.cannabis.prescribe"
    NEURODEVELOPMENTAL_GRAPH_VIEW = "neurodevelopmental.graph.view"
    NEURODEVELOPMENTAL_GRAPH_CREATE = "neurodevelopmental.graph.create"
    NEURODEVELOPMENTAL_REPORT_GENERATE = "neurodevelopmental.report.generate"
    NEURODEVELOPMENTAL_REPORT_EXPORT = "neurodevelopmental.report.export"
    NEURODEVELOPMENTAL_AI_USE = "neurodevelopmental.ai.use"
    NEURODEVELOPMENTAL_RESEARCH_EXPORT = "neurodevelopmental.research.export"
    REDACTED = "neurodevelopmental.observatory.view"
    REDACTED = "neurodevelopmental.dashboard.medical"
    REDACTED = "neurodevelopmental.dashboard.coordinator"
    REDACTED = "neurodevelopmental.dashboard.researcher"
    REDACTED = "neurodevelopmental.dashboard.manager"
    REDACTED = "neurodevelopmental.dashboard.health_secretary"
    REDACTED = "neurodevelopmental.dashboard.financial"
    REDACTED = "neurodevelopmental.dashboard.scientific"

    # ─── Sprint 4 — Clinical Intelligence Platform ────────────────────
    # Explainability + Timeline + Analytics + Correlation + Cohort +
    # Research + Dashboard + ML Preparation (Sprint 4.1–4.5)
    INTELLIGENCE_TIMELINE_READ = "intelligence.timeline.read"
    INTELLIGENCE_EPISODE_READ = "intelligence.episode.read"
    INTELLIGENCE_EPISODE_WRITE = "intelligence.episode.write"
    INTELLIGENCE_EPISODE_CONFIRM = "intelligence.episode.confirm"
    INTELLIGENCE_ANALYTICS_READ = "intelligence.analytics.read"
    INTELLIGENCE_CORRELATION_READ = "intelligence.correlation.read"
    INTELLIGENCE_CORRELATION_COMPUTE = "intelligence.correlation.compute"
    INTELLIGENCE_COHORT_READ = "intelligence.cohort.read"
    INTELLIGENCE_COHORT_DEFINE = "intelligence.cohort.define"
    RESEARCH_EXPORT = "research.export"
    RESEARCH_OMOP_ACCESS = "research.omop.access"
    EXPLAINABILITY_READ = "explainability.read"
    EXPLAINABILITY_AUDIT = "explainability.audit"
    DASHBOARD_PATIENT_VIEW = "dashboard.patient.view"
    DASHBOARD_COHORT_VIEW = "dashboard.cohort.view"
    DASHBOARD_MANAGERIAL = "dashboard.managerial"
    ML_FEATURE_READ = "ml.feature.read"
    ML_DATASET_BUILD = "ml.dataset.build"
    ML_PREDICT_USE = "ml.predict.use"

    # ─── Sprint 4.2 — Clinical Context Engine (ADR-0003) ─────────────
    INTELLIGENCE_CONTEXT_READ = "intelligence.context.read"
    INTELLIGENCE_CONTEXT_WRITE = "intelligence.context.write"
    INTELLIGENCE_CONTEXT_CONFIRM = "intelligence.context.confirm"
    INTELLIGENCE_CONTEXT_RULE_RUN = "intelligence.context.rule.run"
    INTELLIGENCE_CONTEXT_QUERY = "intelligence.context.query"

    # ─── Sprint 4.5 — Knowledge REST API (RC1 Gate 2) ────────────────
    # ADDITIVE ONLY. These constants extend the registry; existing
    # roles default to ADMIN bypass via routes/auth_decorators.py.
    INTELLIGENCE_RESEARCH_READ = "intelligence.research.read"
    INTELLIGENCE_REPLAY_EXECUTE = "intelligence.replay.execute"

    @classmethod
    def all(cls) -> List[str]:
        """Retorna todas as permissões definidas."""
        return [
            v for k, v in cls.__dict__.items()
            if not k.startswith("_") and isinstance(v, str)
        ]
    
    @classmethod
    def wildcard_expand(cls, permission: str) -> Set[str]:
        """
        Expande wildcard em permissões concretas.
        
        Exemplo: patient.* → {patient.read, patient.write, patient.delete, ...}
        """
        if not permission.endswith(".*"):
            return {permission}
        
        prefix = permission[:-2]  # Remove .* 
        return {
            p for p in cls.all()
            if p.startswith(f"{prefix}.") and p != permission
        }


# ═══════════════════════════════════════════════════════════════════════
# ROLES
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Role:
    """
    Role = agrupamento de permissões.
    
    Não é autoridade por si só. É apenas um pacote de permissões
    que pode ser atribuído a um ator.
    """
    name: str
    permissions: FrozenSet[str]
    description: str = ""
    is_system: bool = True  # Roles do sistema não podem ser modificadas
    
    def has_permission(self, permission: str) -> bool:
        """Verifica se role possui permissão (incluindo wildcards)."""
        if permission in self.permissions:
            return True
        
        # Verifica wildcards
        for perm in self.permissions:
            if perm.endswith(".*"):
                prefix = perm[:-2]
                if permission.startswith(f"{prefix}."):
                    return True
        
        return False
    
    def has_any_permission(self, permissions: List[str]) -> bool:
        """Verifica se role tem pelo menos uma das permissões."""
        return any(self.has_permission(p) for p in permissions)
    
    def has_all_permissions(self, permissions: List[str]) -> bool:
        """Verifica se role tem todas as permissões."""
        return all(self.has_permission(p) for p in permissions)


class RoleRegistry:
    """
    Registro canônico de roles da plataforma.
    
    Cada role é um conjunto de permissões.
    Roles podem ser estendidas por tenant (custom roles).
    """
    
    # ─── ROLE_ADMIN ──────────────────────────────────────────────────
    # Acesso total à plataforma
    ROLE_ADMIN = Role(
        name="admin",
        permissions=frozenset(Permission.all()),
        description="Acesso total à plataforma",
    )
    
    # ─── ROLE_PHYSICIAN ──────────────────────────────────────────────
    # Médico / Prestador de serviço
    ROLE_PHYSICIAN = Role(
        name="physician",
        permissions=frozenset({
            Permission.PATIENT_READ,
            Permission.PATIENT_WRITE,
            Permission.PATIENT_EXPORT,
            Permission.CONSULTATION_READ,
            Permission.CONSULTATION_WRITE,
            Permission.CONSULTATION_START,
            Permission.CONSULTATION_FINISH,
            Permission.CONSULTATION_SCHEDULE,
            Permission.EVOLUTION_READ,
            Permission.EVOLUTION_WRITE,
            Permission.PRESCRIPTION_WRITE,
            Permission.PRESCRIPTION_READ,
            Permission.EXAM_REQUEST,
            Permission.EXAM_READ,
            Permission.DIAGNOSIS_WRITE,
            Permission.DIAGNOSIS_READ,
            Permission.ALLERGY_WRITE,
            Permission.MEDICATION_PRESCRIBE,
            Permission.DOCUMENT_UPLOAD,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_PROCESS,
            Permission.VOICE_USE,
            Permission.VOICE_COMMAND_EXECUTE,
            Permission.SMART_FLOW_CHECKIN,
            Permission.SMART_FLOW_MONITOR,
            Permission.COMMUNICATION_SEND,
            Permission.COMMUNICATION_READ,
            Permission.BILLING_READ,
            Permission.BILLING_INVOICE_CREATE,
            Permission.LGPD_EXPORT,
            Permission.AI_USE,
            Permission.CLINIC_READ,
            Permission.PROFESSIONAL_READ,
            Permission.USER_READ,
            Permission.FEATURE_FLAG_READ,
        }),
        description="Médico / Prestador de serviço",
    )
    
    # ─── ROLE_SECRETARY ──────────────────────────────────────────────
    # Recepcionista / Secretária
    ROLE_SECRETARY = Role(
        name="secretary",
        permissions=frozenset({
            Permission.PATIENT_READ,
            Permission.PATIENT_WRITE,
            Permission.PATIENT_EXPORT,
            Permission.CONSULTATION_READ,
            Permission.CONSULTATION_WRITE,
            Permission.CONSULTATION_SCHEDULE,
            Permission.DOCUMENT_UPLOAD,
            Permission.DOCUMENT_READ,
            Permission.SMART_FLOW_CHECKIN,
            Permission.SMART_FLOW_MONITOR,
            Permission.COMMUNICATION_SEND,
            Permission.COMMUNICATION_READ,
            Permission.COMMUNICATION_TEMPLATE_MANAGE,
            Permission.BILLING_READ,
            Permission.BILLING_INVOICE_CREATE,
            Permission.BILLING_PAYMENT_RECEIVE,
            Permission.CLINIC_READ,
            Permission.USER_READ,
            Permission.PROFESSIONAL_READ,
        }),
        description="Recepcionista / Secretária",
    )
    
    # ─── ROLE_MANAGER ────────────────────────────────────────────────
    # Gestor da clínica
    ROLE_MANAGER = Role(
        name="manager",
        permissions=frozenset({
            Permission.PATIENT_READ,
            Permission.PATIENT_WRITE,
            Permission.PATIENT_EXPORT,
            Permission.PATIENT_MERGE,
            Permission.CONSULTATION_READ,
            Permission.CONSULTATION_WRITE,
            Permission.CONSULTATION_DELETE,
            Permission.CONSULTATION_SCHEDULE,
            Permission.EVOLUTION_READ,
            Permission.PRESCRIPTION_READ,
            Permission.EXAM_READ,
            Permission.DIAGNOSIS_READ,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_DELETE,
            Permission.DOCUMENT_PROCESS,
            Permission.VOICE_USE,
            Permission.SMART_FLOW_CHECKIN,
            Permission.SMART_FLOW_MONITOR,
            Permission.SMART_FLOW_CONFIGURE,
            Permission.COMMUNICATION_SEND,
            Permission.COMMUNICATION_READ,
            Permission.COMMUNICATION_TEMPLATE_MANAGE,
            Permission.BILLING_READ,
            Permission.BILLING_MANAGE,
            Permission.BILLING_INVOICE_CREATE,
            Permission.BILLING_PAYMENT_RECEIVE,
            Permission.SUBSCRIPTION_MANAGE,
            Permission.PLATFORM_READ,
            Permission.PLATFORM_CONFIGURE,
            Permission.PLATFORM_AUDIT_READ,
            Permission.PLATFORM_AUDIT_EXPORT,
            Permission.USER_READ,
            Permission.USER_WRITE,
            Permission.USER_IMPERSONATE,
            Permission.PROFESSIONAL_READ,
            Permission.PROFESSIONAL_WRITE,
            Permission.PROFESSIONAL_VALIDATE,
            Permission.CLINIC_READ,
            Permission.CLINIC_WRITE,
            Permission.CLINIC_CONFIGURE,
            Permission.FEATURE_FLAG_READ,
            Permission.FEATURE_FLAG_WRITE,
            Permission.AI_USE,
            Permission.AI_CONFIGURE,
            Permission.LGPD_EXPORT,
            Permission.LGPD_AUDIT,
        }),
        description="Gestor da clínica",
    )
    
    # ─── ROLE_PATIENT ────────────────────────────────────────────────
    # Paciente (portal do paciente)
    ROLE_PATIENT = Role(
        name="patient",
        permissions=frozenset({
            Permission.PATIENT_READ,  # Próprio prontuário
            Permission.CONSULTATION_READ,  # Próprias consultas
            Permission.PRESCRIPTION_READ,
            Permission.EXAM_READ,
            Permission.DIAGNOSIS_READ,
            Permission.DOCUMENT_READ,
            Permission.COMMUNICATION_SEND,
            Permission.COMMUNICATION_READ,
            Permission.LGPD_EXPORT,
        }),
        description="Paciente (portal)",
    )
    
    # ─── ROLE_AGENT ──────────────────────────────────────────────────
    # Agente de IA (Concierge, Voice, etc)
    ROLE_AGENT = Role(
        name="agent",
        permissions=frozenset({
            Permission.PATIENT_READ,
            Permission.PATIENT_WRITE,
            Permission.CONSULTATION_READ,
            Permission.CONSULTATION_WRITE,
            Permission.CONSULTATION_SCHEDULE,
            Permission.CONSULTATION_START,
            Permission.CONSULTATION_FINISH,
            Permission.EVOLUTION_READ,
            Permission.EVOLUTION_WRITE,
            Permission.PRESCRIPTION_READ,
            Permission.EXAM_READ,
            Permission.DIAGNOSIS_READ,
            Permission.ALLERGY_WRITE,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_UPLOAD,
            Permission.DOCUMENT_PROCESS,
            Permission.VOICE_USE,
            Permission.VOICE_COMMAND_EXECUTE,
            Permission.SMART_FLOW_CHECKIN,
            Permission.SMART_FLOW_MONITOR,
            Permission.COMMUNICATION_SEND,
            Permission.COMMUNICATION_READ,
            Permission.AI_USE,
            Permission.AI_CONFIGURE,
            Permission.AI_AGENT_DEPLOY,
        }),
        description="Agente de IA",
    )
    
    # ─── ROLE_SERVICE_ACCOUNT ────────────────────────────────────────
    # Conta de serviço / Integração
    ROLE_SERVICE_ACCOUNT = Role(
        name="service_account",
        permissions=frozenset({
            Permission.PATIENT_READ,
            Permission.PATIENT_WRITE,
            Permission.CONSULTATION_READ,
            Permission.CONSULTATION_WRITE,
            Permission.EVOLUTION_READ,
            Permission.PRESCRIPTION_READ,
            Permission.EXAM_READ,
            Permission.DOCUMENT_READ,
            Permission.DOCUMENT_UPLOAD,
            Permission.VOICE_USE,
            Permission.COMMUNICATION_SEND,
            Permission.COMMUNICATION_READ,
            Permission.BILLING_READ,
            Permission.PLATFORM_READ,
            Permission.AI_USE,
            Permission.LGPD_EXPORT,
        }),
        description="Conta de serviço / Integração",
    )
    
    # ─── ROLE_VIEWER ─────────────────────────────────────────────────
    # Apenas visualização
    ROLE_VIEWER = Role(
        name="viewer",
        permissions=frozenset({
            Permission.PATIENT_READ,
            Permission.CONSULTATION_READ,
            Permission.EVOLUTION_READ,
            Permission.PRESCRIPTION_READ,
            Permission.EXAM_READ,
            Permission.DIAGNOSIS_READ,
            Permission.DOCUMENT_READ,
            Permission.CLINIC_READ,
            Permission.PROFESSIONAL_READ,
            Permission.USER_READ,
        }),
        description="Apenas visualização",
    )

    # ─── ROLE_NEURODEVELOPMENTAL_PHYSICIAN ──────────────────────────
    # Médico especialista em neurodesenvolvimento.
    # Herda permissões clínicas gerais + bundle específico do módulo.
    ROLE_NEURODEVELOPMENTAL_PHYSICIAN = Role(
        name="neuro_physician",
        permissions=frozenset({
            # Bundle clínico padrão (subset de physician)
            Permission.PATIENT_READ,
            Permission.PATIENT_WRITE,
            Permission.PATIENT_EXPORT,
            Permission.CONSULTATION_READ,
            Permission.CONSULTATION_WRITE,
            Permission.CONSULTATION_SCHEDULE,
            Permission.CONSULTATION_START,
            Permission.CONSULTATION_FINISH,
            Permission.EVOLUTION_READ,
            Permission.EVOLUTION_WRITE,
            Permission.PRESCRIPTION_READ,
            Permission.PRESCRIPTION_WRITE,
            Permission.EXAM_REQUEST,
            Permission.EXAM_READ,
            Permission.DIAGNOSIS_READ,
            Permission.DIAGNOSIS_WRITE,
            Permission.ALLERGY_WRITE,
            Permission.MEDICATION_PRESCRIBE,
            Permission.DOCUMENT_UPLOAD,
            Permission.DOCUMENT_READ,
            Permission.VOICE_USE,
            Permission.COMMUNICATION_SEND,
            Permission.COMMUNICATION_READ,
            Permission.BILLING_READ,
            Permission.AI_USE,
            Permission.LGPD_EXPORT,
            Permission.CLINIC_READ,
            # Bundle neurodesenvolvimento
            Permission.NEURODEVELOPMENTAL_PROFILE_READ,
            Permission.NEURODEVELOPMENTAL_PROFILE_WRITE,
            Permission.NEURODEVELOPMENTAL_SCALE_APPLY,
            Permission.NEURODEVELOPMENTAL_SCALE_INTERPRET,
            Permission.REDACTED,
            Permission.REDACTED,
            Permission.NEURODEVELOPMENTAL_GRAPH_VIEW,
            Permission.NEURODEVELOPMENTAL_GRAPH_CREATE,
            Permission.NEURODEVELOPMENTAL_REPORT_GENERATE,
            Permission.NEURODEVELOPMENTAL_REPORT_EXPORT,
            Permission.NEURODEVELOPMENTAL_AI_USE,
            Permission.REDACTED,
            Permission.REDACTED,
            # Sprint 4 — Clinical Intelligence Platform
            Permission.INTELLIGENCE_TIMELINE_READ,
            Permission.INTELLIGENCE_CONTEXT_READ,
            Permission.INTELLIGENCE_CONTEXT_WRITE,
            Permission.INTELLIGENCE_CONTEXT_CONFIRM,
            Permission.INTELLIGENCE_CONTEXT_QUERY,
            Permission.EXPLAINABILITY_READ,
            Permission.DASHBOARD_PATIENT_VIEW,
        }),
        description="Médico especialista em neurodesenvolvimento",
    )

    # ─── ROLE_INTELLIGENCE_CURATOR ────────────────────────────────────
    # Curador de Inteligência Clínica — responsável por revisar sugestões
    # de ClinicalContext, validar explicações, manter grafo de relacionamentos.
    # Read-only em módulos de inteligência clínica (timeline, analytics, correlation).
    ROLE_INTELLIGENCE_CURATOR = Role(
        name="intelligence_curator",
        permissions=frozenset({
            Permission.INTELLIGENCE_CONTEXT_READ,
            Permission.INTELLIGENCE_CONTEXT_WRITE,
            Permission.INTELLIGENCE_CONTEXT_CONFIRM,
            Permission.INTELLIGENCE_CONTEXT_RULE_RUN,
            Permission.INTELLIGENCE_CONTEXT_QUERY,
            Permission.INTELLIGENCE_TIMELINE_READ,
            Permission.INTELLIGENCE_EPISODE_READ,
            Permission.INTELLIGENCE_EPISODE_CONFIRM,
            Permission.INTELLIGENCE_ANALYTICS_READ,
            Permission.INTELLIGENCE_CORRELATION_READ,
            Permission.INTELLIGENCE_COHORT_READ,
            Permission.EXPLAINABILITY_READ,
            Permission.EXPLAINABILITY_AUDIT,
            Permission.DASHBOARD_PATIENT_VIEW,
            Permission.DASHBOARD_COHORT_VIEW,
        }),
        description="Curador de Inteligência Clínica — revisão de contextos e explicações",
    )

    # ─── ROLE_HEALTH_SECRETARY ──────────────────────────────────────
    # Secretaria Estadual/Municipal de Saúde — acesso somente leitura ao
    # Observatório Sergipano de Neurodesenvolvimento.
    ROLE_HEALTH_SECRETARY = Role(
        name="health_secretary",
        permissions=frozenset({
            Permission.REDACTED,
            Permission.REDACTED,
        }),
        description="Secretaria de Saúde (acesso somente leitura ao Observatório)",
    )

    # ─── ROLE_SCIENTIFIC_PRODUCER ───────────────────────────────────
    # Pesquisador / Produtor Científico — exportação de dados e
    # dashboards de pesquisa + produção científica.
    ROLE_SCIENTIFIC_PRODUCER = Role(
        name="scientific_producer",
        permissions=frozenset({
            Permission.PATIENT_READ,
            Permission.NEURODEVELOPMENTAL_PROFILE_READ,
            Permission.NEURODEVELOPMENTAL_RESEARCH_EXPORT,
            Permission.REDACTED,
            Permission.REDACTED,
        }),
        description="Pesquisador / Produtor Científico",
    )

    _ROLES: Dict[str, Role] = {
        ROLE_ADMIN.name: ROLE_ADMIN,
        ROLE_PHYSICIAN.name: ROLE_PHYSICIAN,
        ROLE_SECRETARY.name: ROLE_SECRETARY,
        ROLE_MANAGER.name: ROLE_MANAGER,
        ROLE_PATIENT.name: ROLE_PATIENT,
        ROLE_AGENT.name: ROLE_AGENT,
        ROLE_SERVICE_ACCOUNT.name: ROLE_SERVICE_ACCOUNT,
        ROLE_VIEWER.name: ROLE_VIEWER,
        ROLE_NEURODEVELOPMENTAL_PHYSICIAN.name: ROLE_NEURODEVELOPMENTAL_PHYSICIAN,
        ROLE_HEALTH_SECRETARY.name: ROLE_HEALTH_SECRETARY,
        ROLE_SCIENTIFIC_PRODUCER.name: ROLE_SCIENTIFIC_PRODUCER,
        ROLE_INTELLIGENCE_CURATOR.name: ROLE_INTELLIGENCE_CURATOR,
    }
    
    @classmethod
    def get(cls, role_name: str) -> Optional[Role]:
        """Retorna role pelo nome."""
        return cls._ROLES.get(role_name)
    
    @classmethod
    def all_roles(cls) -> List[Role]:
        """Retorna todas as roles."""
        return list(cls._ROLES.values())
    
    @classmethod
    def all_names(cls) -> List[str]:
        """Retorna nomes de todas as roles."""
        return list(cls._ROLES.keys())
    
    @classmethod
    def resolve_permissions(cls, roles: List[str]) -> Set[str]:
        """
        Resolve lista de roles em conjunto de permissões.
        
        Args:
            roles: Lista de nomes de roles
        
        Returns:
            Conjunto de todas as permissões concedidas
        """
        permissions: Set[str] = set()
        for role_name in roles:
            role = cls.get(role_name)
            if role:
                permissions.update(role.permissions)
        return permissions
    
    @classmethod
    def check_permission(cls, roles: List[str], permission: str) -> bool:
        """
        Verifica se alguma das roles possui a permissão.
        
        Args:
            roles: Lista de nomes de roles
            permission: Permissão a verificar
        
        Returns:
            True se alguma role concede a permissão
        """
        for role_name in roles:
            role = cls.get(role_name)
            if role and role.has_permission(permission):
                return True
        return False
    
    @classmethod
    def check_any_permission(cls, roles: List[str], permissions: List[str]) -> bool:
        """Verifica se tem pelo menos uma das permissões."""
        return any(cls.check_permission(roles, p) for p in permissions)
    
    @classmethod
    def check_all_permissions(cls, roles: List[str], permissions: List[str]) -> bool:
        """Verifica se tem todas as permissões."""
        return all(cls.check_permission(roles, p) for p in permissions)
    
    @classmethod
    def register_custom_role(cls, role: Role) -> None:
        """
        Registra role customizada (por tenant).
        
        Custom roles não são system roles.
        """
        cls._ROLES[role.name] = role


# ═══════════════════════════════════════════════════════════════════════
# PERMISSION REGISTRY
# ═══════════════════════════════════════════════════════════════════════

class PermissionRegistry:
    """
    Registro de permissões para validação runtime.
    
    Garante que apenas permissões conhecidas sejam usadas.
    """
    
    _VALID_PERMISSIONS: Set[str] = set(Permission.all())
    
    @classmethod
    def is_valid(cls, permission: str) -> bool:
        """Verifica se permissão existe no registro."""
        if permission in cls._VALID_PERMISSIONS:
            return True
        # Aceita wildcards
        if permission.endswith(".*"):
            prefix = permission[:-2]
            return any(p.startswith(f"{prefix}.") for p in cls._VALID_PERMISSIONS)
        return False
    
    @classmethod
    def validate(cls, permission: str) -> None:
        """Valida permissão, levanta erro se inválida."""
        from araos.platform.shared.errors import ValidationError
        if not cls.is_valid(permission):
            raise ValidationError(
                f"Invalid permission: {permission}",
                field="permission"
            )
    
    @classmethod
    def list_by_resource(cls, resource: str) -> List[str]:
        """Lista permissões de um recurso."""
        return [p for p in cls._VALID_PERMISSIONS if p.startswith(f"{resource}.")]
    
    @classmethod
    def resources(cls) -> Set[str]:
        """Retorna todos os recursos conhecidos."""
        return {p.split(".")[0] for p in cls._VALID_PERMISSIONS}
