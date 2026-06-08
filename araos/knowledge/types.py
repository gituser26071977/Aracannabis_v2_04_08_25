"""
AraOS Knowledge — Knowledge Types.

Domínios de conhecimento suportados pela Knowledge Layer.

Week 8 — Knowledge Layer v1
"""

from enum import Enum


class KnowledgeType(str, Enum):
    """
    Tipo de conhecimento armazenado.
    
    Values:
        CLINICAL        → Conhecimento clínico (protocolos, guidelines)
        PROFESSIONAL    → Conhecimento do profissional (templates, preferências)
        ORGANIZATIONAL  → Conhecimento institucional (fluxos, políticas, FAQ)
        PATIENT         → Conhecimento do paciente (Digital Twin, histórico)
        SYSTEM          → Conhecimento do sistema (logs, configurações)
    """
    CLINICAL = "clinical"
    PROFESSIONAL = "professional"
    ORGANIZATIONAL = "organizational"
    PATIENT = "patient"
    SYSTEM = "system"


class KnowledgeStatus(str, Enum):
    """Status de um objeto de conhecimento."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    DEPRECATED = "deprecated"


class KnowledgeSourceType(str, Enum):
    """Tipo de fonte do conhecimento."""
    DOCUMENT = "document"
    TEMPLATE = "template"
    PROTOCOL = "protocol"
    FAQ = "faq"
    POLICY = "policy"
    DIGITAL_TWIN = "digital_twin"
    TIMELINE = "timeline"
    SUMMARY = "summary"
    CHECKLIST = "checklist"
    WORKFLOW = "workflow"
