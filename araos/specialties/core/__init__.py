"""
AraOS Specialty Framework — Core.

Fundação comum para todas as especialidades.

Week 10 — Specialty Framework Foundation
"""

from .definitions import (
    SpecialtyDefinition,
    SpecialtyCategory,
    SpecialtyStatus,
    SpecialtyCapability,
)
from .profile import SpecialtyProfile, SpecialtyField, SpecialtyScore
from .timeline import SpecialtyTimeline, SpecialtyTimelineEvent
from .protocol import SpecialtyProtocol, ProtocolStep, ProtocolStepType, ProtocolTrigger
from .workflow import (
    SpecialtyWorkflow,
    WorkflowCheckpoint,
    WorkflowInstance,
    WorkflowStatus,
    WorkflowPhase,
)
from .dashboard import (
    SpecialtyDashboard,
    SpecialtyMetric,
    SpecialtyKPI,
    SpecialtyChart,
    SpecialtyMetricsCollector,
    MetricType,
    ChartType,
    KpiSeverity,
)
from .registry import SpecialtyRegistry
from .agent import SpecialtyAgent
from .knowledge import SpecialtyKnowledgeSource

__all__ = [
    # Definitions
    "SpecialtyDefinition",
    "SpecialtyCategory",
    "SpecialtyStatus",
    "SpecialtyCapability",
    # Profile
    "SpecialtyProfile",
    "SpecialtyField",
    "SpecialtyScore",
    # Timeline
    "SpecialtyTimeline",
    "SpecialtyTimelineEvent",
    # Protocol
    "SpecialtyProtocol",
    "ProtocolStep",
    "ProtocolStepType",
    "ProtocolTrigger",
    # Workflow
    "SpecialtyWorkflow",
    "WorkflowCheckpoint",
    "WorkflowInstance",
    "WorkflowStatus",
    "WorkflowPhase",
    # Dashboard
    "SpecialtyDashboard",
    "SpecialtyMetric",
    "SpecialtyKPI",
    "SpecialtyChart",
    "SpecialtyMetricsCollector",
    "MetricType",
    "ChartType",
    "KpiSeverity",
    # Registry
    "SpecialtyRegistry",
    # Agent
    "SpecialtyAgent",
    # Knowledge
    "SpecialtyKnowledgeSource",
]
