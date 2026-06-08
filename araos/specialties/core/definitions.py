"""
AraOS Specialty Framework — Core Definitions.

Definições fundamentais para o sistema de especialidades.

Week 10 — Specialty Framework Foundation
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field


class SpecialtyCategory(str, Enum):
    """Categoria da especialidade médica/multiprofissional."""
    MEDICAL = "medical"           # Especialidade médica
    MULTIPROFESSIONAL = "multiprofessional"  # Psicologia, nutrição, etc.
    PARAMEDICAL = "paramedical"   # Fisioterapia, fonoaudiologia
    DIAGNOSTIC = "diagnostic"     # Radiologia, patologia
    SURGICAL = "surgical"         # Cirurgia geral, ortopedia
    INTEGRATIVE = "integrative"   # Cannabis, medicina integrativa


class SpecialtyStatus(str, Enum):
    """Status de uma especialidade na plataforma."""
    ACTIVE = "active"
    BETA = "beta"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"
    PLANNED = "planned"


class SpecialtyCapability(str, Enum):
    """Capacidades que uma especialidade pode declarar."""
    CLINICAL_PROFILE = "clinical_profile"
    SPECIALTY_TIMELINE = "specialty_timeline"
    PROTOCOLS = "protocols"
    SCALES = "scales"
    QUESTIONNAIRES = "questionnaires"
    WORKFLOWS = "workflows"
    DASHBOARD = "dashboard"
    KNOWLEDGE_BASE = "knowledge_base"
    AGENT_SUPPORT = "agent_support"
    DRUG_INTERACTIONS = "drug_interactions"
    DOSE_TRACKING = "dose_tracking"
    EVOLUTION_TRACKING = "evolution_tracking"


@dataclass
class SpecialtyDefinition:
    """
    Definição de uma especialidade na plataforma AraOS.

    Cada especialidade (Cannabis, Nutrologia, Psiquiatria, etc.)
    deve registrar uma SpecialtyDefinition no SpecialtyRegistry.

    Attributes:
        code: Código único da especialidade (ex: "cannabis", "cardiology")
        name: Nome legível (ex: "Cannabis Medicinal")
        description: Descrição da especialidade
        category: Categoria médica/multiprofissional
        status: Status na plataforma
        version: Versão do módulo
        capabilities: Capacidades declaradas
        required_permissions: Permissões necessárias para uso
        supported_entities: Entidades clínicas suportadas
        dependencies: Outras especialidades necessárias
        metadata: Metadados adicionais
    """
    code: str
    name: str
    description: str = ""
    category: SpecialtyCategory = SpecialtyCategory.MEDICAL
    status: SpecialtyStatus = SpecialtyStatus.ACTIVE
    version: str = "1.0.0"
    capabilities: Set[SpecialtyCapability] = field(default_factory=set)
    required_permissions: List[str] = field(default_factory=list)
    supported_entities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "status": self.status.value,
            "version": self.version,
            "capabilities": [c.value for c in self.capabilities],
            "required_permissions": self.required_permissions,
            "supported_entities": self.supported_entities,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
        }

    def has_capability(self, capability: SpecialtyCapability) -> bool:
        """Verifica se a especialidade possui uma capacidade."""
        return capability in self.capabilities

    def add_capability(self, capability: SpecialtyCapability) -> None:
        """Adiciona uma capacidade à especialidade."""
        self.capabilities.add(capability)
