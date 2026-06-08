"""
AraOS Specialty Framework — Specialty Registry.

Registro dinâmico de especialidades.

Week 10 — Specialty Framework Foundation
"""

from typing import Dict, Any, List, Optional, Type

from .definitions import SpecialtyDefinition, SpecialtyCapability, SpecialtyCategory, SpecialtyStatus
from .profile import SpecialtyProfile
from .protocol import SpecialtyProtocol
from .workflow import SpecialtyWorkflow


class SpecialtyRegistry:
    """
    Registro de especialidades da plataforma AraOS.

    Responsabilidades:
        1. Registrar especialidades dinamicamente
        2. Resolver especialidade por código
        3. Listar especialidades por categoria/capacidade
        4. Gerenciar dependências entre especialidades

    Uso:
        registry = SpecialtyRegistry()

        # Registrar especialidade
        registry.register(SpecialtyDefinition(
            code="cannabis",
            name="Cannabis Medicinal",
            category=SpecialtyCategory.INTEGRATIVE,
            capabilities={SpecialtyCapability.PROTOCOLS, ...},
        ))

        # Resolver
        definition = registry.get("cannabis")

        # Listar
        medical = registry.list_by_category(SpecialtyCategory.MEDICAL)
        with_protocols = registry.list_by_capability(SpecialtyCapability.PROTOCOLS)
    """

    def __init__(self):
        self._definitions: Dict[str, SpecialtyDefinition] = {}
        self._profiles: Dict[str, Type[SpecialtyProfile]] = {}
        self._protocols: Dict[str, List[SpecialtyProtocol]] = {}
        self._workflows: Dict[str, List[SpecialtyWorkflow]] = {}
        self._metadata: Dict[str, Any] = {}

    # ── Registro ──

    def register(self, definition: SpecialtyDefinition) -> None:
        """Registra uma especialidade."""
        self._definitions[definition.code] = definition
        self._protocols.setdefault(definition.code, [])
        self._workflows.setdefault(definition.code, [])

    def unregister(self, code: str) -> bool:
        """Remove uma especialidade do registro."""
        if code in self._definitions:
            del self._definitions[code]
            self._profiles.pop(code, None)
            self._protocols.pop(code, None)
            self._workflows.pop(code, None)
            return True
        return False

    def register_profile_class(self, code: str, profile_class: Type[SpecialtyProfile]) -> None:
        """Registra a classe de profile de uma especialidade."""
        self._profiles[code] = profile_class

    def register_protocol(self, protocol: SpecialtyProtocol) -> None:
        """Registra um protocolo para uma especialidade."""
        code = protocol.specialty_code
        self._protocols.setdefault(code, [])
        self._protocols[code].append(protocol)

    def register_workflow(self, workflow: SpecialtyWorkflow) -> None:
        """Registra um workflow para uma especialidade."""
        code = workflow.specialty_code
        self._workflows.setdefault(code, [])
        self._workflows[code].append(workflow)

    # ── Resolução ──

    def get(self, code: str) -> Optional[SpecialtyDefinition]:
        """Recupera definição por código."""
        return self._definitions.get(code)

    def get_profile_class(self, code: str) -> Optional[Type[SpecialtyProfile]]:
        """Recupera classe de profile por código."""
        return self._profiles.get(code)

    def get_protocols(self, code: str) -> List[SpecialtyProtocol]:
        """Recupera protocolos de uma especialidade."""
        return self._protocols.get(code, [])

    def get_workflows(self, code: str) -> List[SpecialtyWorkflow]:
        """Recupera workflows de uma especialidade."""
        return self._workflows.get(code, [])

    # ── Listagem ──

    def list_all(self) -> List[SpecialtyDefinition]:
        """Lista todas as especialidades registradas."""
        return list(self._definitions.values())

    def list_by_category(self, category: SpecialtyCategory) -> List[SpecialtyDefinition]:
        """Lista especialidades por categoria."""
        return [d for d in self._definitions.values() if d.category == category]

    def list_by_status(self, status: SpecialtyStatus) -> List[SpecialtyDefinition]:
        """Lista especialidades por status."""
        return [d for d in self._definitions.values() if d.status == status]

    def list_by_capability(self, capability: SpecialtyCapability) -> List[SpecialtyDefinition]:
        """Lista especialidades que possuem uma capacidade."""
        return [d for d in self._definitions.values() if d.has_capability(capability)]

    def list_active(self) -> List[SpecialtyDefinition]:
        """Lista especialidades ativas."""
        return self.list_by_status(SpecialtyStatus.ACTIVE)

    def list_codes(self) -> List[str]:
        """Lista códigos de todas as especialidades."""
        return list(self._definitions.keys())

    # ── Validação ──

    def is_registered(self, code: str) -> bool:
        """Verifica se uma especialidade está registrada."""
        return code in self._definitions

    def check_dependencies(self, code: str) -> List[str]:
        """Verifica se as dependências de uma especialidade estão satisfeitas."""
        definition = self._definitions.get(code)
        if not definition:
            return [f"Specialty '{code}' not registered"]

        missing = []
        for dep in definition.dependencies:
            if dep not in self._definitions:
                missing.append(f"Dependency '{dep}' not registered")

        return missing

    def resolve_dependency_order(self) -> List[str]:
        """
        Resolve ordem de carregamento baseada em dependências.

        Uses topological sort (Kahn's algorithm).
        """
        in_degree: Dict[str, int] = {code: 0 for code in self._definitions}
        dependents: Dict[str, List[str]] = {code: [] for code in self._definitions}

        for code, definition in self._definitions.items():
            for dep in definition.dependencies:
                if dep in self._definitions:
                    in_degree[code] += 1
                    dependents.setdefault(dep, []).append(code)

        # Start with nodes with no dependencies
        queue = [code for code, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            code = queue.pop(0)
            result.append(code)
            for dependent in dependents.get(code, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # If not all nodes processed, there's a cycle
        if len(result) != len(self._definitions):
            # Fallback: return in arbitrary order
            return list(self._definitions.keys())

        return result

    # ── Resumo ──

    def summary(self) -> Dict[str, Any]:
        """Retorna resumo do registro."""
        categories: Dict[str, int] = {}
        for d in self._definitions.values():
            cat = d.category.value
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_specialties": len(self._definitions),
            "total_protocols": sum(len(p) for p in self._protocols.values()),
            "total_workflows": sum(len(w) for w in self._workflows.values()),
            "by_category": categories,
            "codes": self.list_codes(),
        }
