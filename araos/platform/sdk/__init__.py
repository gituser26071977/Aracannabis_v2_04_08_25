"""
AraOS Platform — Unified SDK.

Único ponto de entrada para todos os consumidores da Platform Layer.
Nenhum módulo deve acessar implementações diretamente.

Uso:
    from araos.platform.sdk import (
        TenantContext,
        EventEnvelope,
        EventCatalog,
        AuditProvider,
        IdentityProvider,
        FeatureFlagService,
    )

Arquitetura:
    - SIAP (Flask) consome via este SDK
    - Voice (FastAPI) consome via este SDK
    - Smart Flow (FastAPI) consome via este SDK
    - Todos usam os MESMOS contratos e convenções
"""

# Contexto
from araos.platform.shared.context import TenantContext

# Tenant Layer
from araos.platform.tenant import (
    Organization,
    Clinic,
    Professional,
    User,
    ServiceAccount,
    FeatureFlag,
    TenantContextResolver,
    ResolverInput,
    FlaskTenantMiddleware,
    FastAPITenantMiddleware,
    require_tenant,
    require_feature_flag,
    require_roles,
    TenantService,
    PlatformTenantProvider,
    PlatformTenantSettingsProvider,
)

# Eventos
from araos.platform.events.schemas import EventEnvelope, EventPayload, EventMetadata
from araos.platform.events.catalog import EventCatalog, EventDefinition
from araos.platform.events.json_schemas import SchemaRegistry, get_schema_registry

# Contratos (ABC)
from araos.platform.contracts.tenant import TenantProvider, TenantSettingsProvider
from araos.platform.contracts.identity import IdentityProvider, TokenProvider
from araos.platform.contracts.event_bus import EventPublisher, EventConsumer, EventBus
from araos.platform.contracts.audit import AuditProvider

# Feature Flags
from araos.platform.feature_flags.service import FeatureFlagService, FeatureFlagContext

# Identity Platform
from araos.platform.identity.client import IdentityClient
from araos.platform.identity.permissions import Permission, RoleRegistry, PermissionRegistry
from araos.platform.identity.tokens import JWTTokenProvider, TokenClaims, PlatformTokenPair
from araos.platform.identity.context import IdentityContext, ActorType
from araos.platform.identity.service_accounts import ServiceAccountAuthenticator, APIKeyCredentials
from araos.platform.identity.delegated import DelegatedIdentity, DelegationContext, DelegationManager
from araos.platform.identity.service import IdentityService

# Event Bus (The Nervous System)
from araos.platform.event_bus.envelope import EventEnvelopeV2, EventPriority, EventCategory, ClinicalEvent
from araos.platform.event_bus.publisher import RedisEventPublisher
from araos.platform.event_bus.consumer import RedisEventConsumer
from araos.platform.event_bus.bus import AraOSEventBus
from araos.platform.event_bus.router import EventRouter
from araos.platform.event_bus.registry import HandlerRegistry
from araos.platform.event_bus.store import EventStore, EventRecord
from araos.platform.event_bus.dlq import DeadLetterQueue
from araos.platform.event_bus.correlation import CorrelationEngine
from araos.platform.event_bus.replay import EventReplay, ReplayResult
from araos.platform.event_bus.metrics import EventMetrics
from araos.platform.event_bus.pipeline import EventAuditPipeline

# Audit Ledger
from araos.platform.audit.ledger import AuditEntry, AuditLedger
from araos.platform.audit.service import AuditService

# Clinical Intelligence Foundation (Week 4)
from araos.clinical.entities.models import (
    ClinicalEntityBase,
    Diagnosis,
    Medication,
    Allergy,
    Procedure,
    RiskFactor,
)
from araos.clinical.profile.models import ClinicalProfile
from araos.clinical.timeline.models import ClinicalTimeline, TimelineEntry
from araos.clinical.graph.models import (
    ClinicalGraph,
    ClinicalNode,
    ClinicalRelationship,
    ClinicalGraphBuilder,
    NodeType,
    RelationshipType,
)
from araos.clinical.summary.engine import ClinicalSummaryEngine, SummaryResult
from araos.clinical.twin.models import PatientDigitalTwin, PatientDigitalTwinBuilder
from araos.clinical.projections.engine import ClinicalProjectionEngine
from araos.clinical.contracts.voice import VoiceClinicalAdapter, VoiceQuery, VoiceResponse
from araos.clinical.contracts.concierge import (
    ConciergeClinicalAdapter,
    ConciergeQuery,
    ConciergeResponse,
)
from araos.clinical.contracts.knowledge import (
    KnowledgeStore,
    VectorStore,
    GraphStore,
    ClinicalQuery,
    KnowledgeResult,
)

# Agent Runtime & Integration (Week 5)
from araos.agents.runtime.agent import BaseAgent, AgentCapability, AgentResult
from araos.agents.runtime.context import AgentContext, CorrelationContext
from araos.agents.runtime.memory import AgentMemory, MemoryStore, AgentMemoryRecord
from araos.agents.runtime.executor import AgentExecutor
from araos.agents.runtime.runtime import AgentRuntime
from araos.agents.registry.registry import AgentRegistry, AgentDefinition, AgentRegistration
from araos.agents.events.catalog import AgentEventCatalog
from araos.agents.workflows.engine import WorkflowEngine, WorkflowStep, WorkflowResult

from araos.integration.voice_adapter import VoiceAdapter, VoiceCommand, VoiceCommandResult
from araos.integration.concierge_adapter import ConciergeAdapter, ConciergeMessage, ConciergeResponse
from araos.integration.smart_flow_adapter import SmartFlowAdapter, FlowEvent, FlowAction
from araos.integration.core_adapter import CoreAdapter, CorePatientQuery, CoreConsultation

from araos.platform.api.agents import AgentAPI
from araos.platform.api.context import ContextAPI
from araos.platform.api.twin import TwinAPI
from araos.platform.api.events import EventAPI

from araos.intelligence.llm import LLMProvider, LLMMessage, LLMResponse, LLMRequest
from araos.intelligence.embeddings import EmbeddingProvider, EmbeddingResult
from araos.intelligence.vector import VectorStoreProvider, VectorSearchResult

# Trust Levels (Week 7B)
from araos.intelligence.trust.levels import SourceType, TrustLevel, TrustedResponse

# Knowledge Layer (Week 8)
from araos.knowledge.types import KnowledgeType, KnowledgeStatus, KnowledgeSourceType
from araos.knowledge.models import (
    KnowledgeDocument,
    KnowledgeChunk,
    KnowledgeCollection,
    KnowledgeSource,
    KnowledgeMetadata,
)
from araos.knowledge.repository import KnowledgeRepository, InMemoryKnowledgeRepository
from araos.knowledge.retrieval import KnowledgeRetrievalEngine, RetrievalResult
from araos.knowledge.adapter import LLMKnowledgeAdapter, KnowledgeContext
from araos.knowledge.observability import KnowledgeObservability, KnowledgeQueryMetric
from araos.knowledge.sources.organizational import OrganizationalMemory
from araos.knowledge.sources.professional import ProfessionalMemory
from araos.knowledge.sources.patient import PatientKnowledgeSource
# Specialty Framework (Week 10)
from araos.specialties.core.definitions import (
    SpecialtyDefinition, SpecialtyCategory, SpecialtyStatus, SpecialtyCapability,
)
from araos.specialties.core.profile import SpecialtyProfile, SpecialtyField, SpecialtyScore
from araos.specialties.core.timeline import SpecialtyTimeline, SpecialtyTimelineEvent
from araos.specialties.core.protocol import SpecialtyProtocol, ProtocolStep, ProtocolStepType, ProtocolTrigger
from araos.specialties.core.workflow import (
    SpecialtyWorkflow, WorkflowCheckpoint, WorkflowInstance, WorkflowStatus, WorkflowPhase,
)
from araos.specialties.core.dashboard import (
    SpecialtyDashboard, SpecialtyMetric, SpecialtyKPI, SpecialtyChart,
    SpecialtyMetricsCollector, MetricType, ChartType, KpiSeverity,
)
from araos.specialties.core.registry import SpecialtyRegistry
from araos.specialties.core.agent import SpecialtyAgent
from araos.specialties.core.knowledge import SpecialtyKnowledgeSource

# Follow-up Engine (Week 11A)
from araos.followup.core.models import (
    FollowupProgram, FollowupPhase, FollowupCheckpoint,
    FollowupQuestionnaire, FollowupQuestion, FollowupResponse,
    FollowupRule, FollowupAlert,
    FollowupStatus, AlertSeverity, AlertStatus, QuestionType,
)
from araos.followup.core.engine import AdaptiveFollowupEngine
from araos.followup.core.specialty_integration import SpecialtyFollowupProgram
from araos.followup.rules.engine import FollowupRuleEngine, RuleEvaluationContext
from araos.followup.observability.metrics import FollowupObservability, FollowupMetric

# Erros
from araos.platform.shared.errors import (
    AraOSPlatformError,
    EventValidationError,
    EventNotInCatalogError,
    TenantNotFoundError,
    AuthenticationError,
    AuthorizationError,
)

# Constantes
from araos.platform.shared.constants import PLATFORM_NAME, PLATFORM_VERSION

__all__ = [
    # Contexto
    "TenantContext",
    
    # Tenant Layer
    "Organization",
    "Clinic",
    "Professional",
    "User",
    "ServiceAccount",
    "FeatureFlag",
    "TenantContextResolver",
    "ResolverInput",
    "FlaskTenantMiddleware",
    "FastAPITenantMiddleware",
    "require_tenant",
    "require_feature_flag",
    "require_roles",
    "TenantService",
    "PlatformTenantProvider",
    "PlatformTenantSettingsProvider",
    
    # Eventos
    "EventEnvelope",
    "EventPayload",
    "EventMetadata",
    "EventCatalog",
    "EventDefinition",
    "SchemaRegistry",
    "get_schema_registry",
    
    # Contratos
    "TenantProvider",
    "TenantSettingsProvider",
    "IdentityProvider",
    "TokenProvider",
    "EventPublisher",
    "EventConsumer",
    "EventBus",
    "AuditProvider",
    
    # Serviços
    "FeatureFlagService",
    "FeatureFlagContext",
    "IdentityClient",
    "Permission",
    "RoleRegistry",
    "PermissionRegistry",
    "JWTTokenProvider",
    "TokenClaims",
    "PlatformTokenPair",
    "IdentityContext",
    "ActorType",
    "ServiceAccountAuthenticator",
    "APIKeyCredentials",
    "DelegatedIdentity",
    "DelegationContext",
    "DelegationManager",
    "IdentityService",
    
    # Event Bus (Nervous System)
    "EventEnvelopeV2",
    "EventPriority",
    "EventCategory",
    "ClinicalEvent",
    "RedisEventPublisher",
    "RedisEventConsumer",
    "AraOSEventBus",
    "EventRouter",
    "HandlerRegistry",
    "EventStore",
    "EventRecord",
    "DeadLetterQueue",
    "CorrelationEngine",
    "EventReplay",
    "ReplayResult",
    "EventMetrics",
    "EventAuditPipeline",
    
    # Audit Ledger
    "AuditEntry",
    "AuditLedger",
    "AuditService",
    
    # Clinical Intelligence Foundation (Week 4)
    "ClinicalEntityBase",
    "Diagnosis",
    "Medication",
    "Allergy",
    "Procedure",
    "RiskFactor",
    "ClinicalProfile",
    "ClinicalTimeline",
    "TimelineEntry",
    "ClinicalGraph",
    "ClinicalNode",
    "ClinicalRelationship",
    "ClinicalGraphBuilder",
    "NodeType",
    "RelationshipType",
    "ClinicalSummaryEngine",
    "SummaryResult",
    "PatientDigitalTwin",
    "PatientDigitalTwinBuilder",
    "ClinicalProjectionEngine",
    "VoiceClinicalAdapter",
    "VoiceQuery",
    "VoiceResponse",
    "ConciergeClinicalAdapter",
    "ConciergeQuery",
    "ConciergeResponse",
    "KnowledgeStore",
    "VectorStore",
    "GraphStore",
    "ClinicalQuery",
    "KnowledgeResult",
    
    # Agent Runtime & Integration (Week 5)
    "BaseAgent",
    "AgentCapability",
    "AgentResult",
    "AgentContext",
    "CorrelationContext",
    "AgentMemory",
    "MemoryStore",
    "AgentMemoryRecord",
    "AgentExecutor",
    "AgentRuntime",
    "AgentRegistry",
    "AgentDefinition",
    "AgentRegistration",
    "AgentEventCatalog",
    "WorkflowEngine",
    "WorkflowStep",
    "WorkflowResult",
    "VoiceAdapter",
    "VoiceCommand",
    "VoiceCommandResult",
    "ConciergeAdapter",
    "ConciergeMessage",
    "ConciergeResponse",
    "SmartFlowAdapter",
    "FlowEvent",
    "FlowAction",
    "CoreAdapter",
    "CorePatientQuery",
    "CoreConsultation",
    "AgentAPI",
    "ContextAPI",
    "TwinAPI",
    "EventAPI",
    "LLMProvider",
    "LLMMessage",
    "LLMResponse",
    "LLMRequest",
    "EmbeddingProvider",
    "EmbeddingResult",
    "VectorStoreProvider",
    "VectorSearchResult",
    
    # Trust Levels (Week 7B)
    "SourceType",
    "TrustLevel",
    "TrustedResponse",
    
    # Knowledge Layer (Week 8)
    "KnowledgeType",
    "KnowledgeStatus",
    "KnowledgeSourceType",
    "KnowledgeDocument",
    "KnowledgeChunk",
    "KnowledgeCollection",
    "KnowledgeSource",
    "KnowledgeMetadata",
    "KnowledgeRepository",
    "InMemoryKnowledgeRepository",
    "KnowledgeRetrievalEngine",
    "RetrievalResult",
    "LLMKnowledgeAdapter",
    "KnowledgeContext",
    "KnowledgeObservability",
    "KnowledgeQueryMetric",
    "OrganizationalMemory",
    "ProfessionalMemory",
    "PatientKnowledgeSource",
    # Specialty Framework (Week 10)
    "SpecialtyDefinition",
    "SpecialtyCategory",
    "SpecialtyStatus",
    "SpecialtyCapability",
    "SpecialtyProfile",
    "SpecialtyField",
    "SpecialtyScore",
    "SpecialtyTimeline",
    "SpecialtyTimelineEvent",
    "SpecialtyProtocol",
    "ProtocolStep",
    "ProtocolStepType",
    "ProtocolTrigger",
    "SpecialtyWorkflow",
    "WorkflowCheckpoint",
    "WorkflowInstance",
    "WorkflowStatus",
    "WorkflowPhase",
    "SpecialtyDashboard",
    "SpecialtyMetric",
    "SpecialtyKPI",
    "SpecialtyChart",
    "SpecialtyMetricsCollector",
    "MetricType",
    "ChartType",
    "KpiSeverity",
    "SpecialtyRegistry",
    "SpecialtyAgent",
    "SpecialtyKnowledgeSource",
    # Follow-up Engine (Week 11A)
    "FollowupProgram",
    "FollowupPhase",
    "FollowupCheckpoint",
    "FollowupQuestionnaire",
    "FollowupQuestion",
    "FollowupResponse",
    "FollowupRule",
    "FollowupAlert",
    "FollowupStatus",
    "AlertSeverity",
    "AlertStatus",
    "QuestionType",
    "AdaptiveFollowupEngine",
    "SpecialtyFollowupProgram",
    "FollowupRuleEngine",
    "RuleEvaluationContext",
    "FollowupObservability",
    "FollowupMetric",
    # Erros
    "AraOSPlatformError",
    "EventValidationError",
    "EventNotInCatalogError",
    "TenantNotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    
    # Constantes
    "PLATFORM_NAME",
    "PLATFORM_VERSION",
]
