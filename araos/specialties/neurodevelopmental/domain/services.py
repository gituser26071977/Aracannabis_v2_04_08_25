"""
AraOS Neurodevelopmental — Domain Services.

Serviços sem estado que orquestram lógica de domínio que NÃO pertence
a uma entidade específica. Aqui vive a matriz de transições do Diagnosis
(encapsulada fora da entidade para reuso e testabilidade).

ADR-0002 §2.2.2: 'Diagnosis = ciclo de vida com 6 estados...
Cada mudança gera Clinical Event. Nunca atualizar silenciosamente.'

DiagnósticoTransitionService:
    - Valida transições válidas.
    - Fornece queries sobre o ciclo de vida (terminal states, allowed_from, etc).
"""

from __future__ import annotations

from enum import Enum
from typing import FrozenSet

from .diagnosis import DiagnosisState, InvalidDiagnosisTransitionError


# Matriz re-exportada para reuso externo (testes, application services).
# Mantida sincronizada com `_VALID_TRANSITIONS` em `diagnosis.py`.
VALID_TRANSITIONS: dict[DiagnosisState, frozenset[DiagnosisState]] = {
    DiagnosisState.HYPOTHESIS: frozenset(
        {
            DiagnosisState.INVESTIGATING,
            DiagnosisState.CONFIRMED,
            DiagnosisState.DISCARDED,
        }
    ),
    DiagnosisState.INVESTIGATING: frozenset(
        {
            DiagnosisState.CONFIRMED,
            DiagnosisState.DISCARDED,
            DiagnosisState.HYPOTHESIS,
        }
    ),
    DiagnosisState.CONFIRMED: frozenset(
        {
            DiagnosisState.REVISED,
            DiagnosisState.IN_REMISSION,
            DiagnosisState.DISCARDED,
        }
    ),
    DiagnosisState.REVISED: frozenset(
        {
            DiagnosisState.IN_REMISSION,
            DiagnosisState.DISCARDED,
        }
    ),
    DiagnosisState.IN_REMISSION: frozenset(
        {
            DiagnosisState.CONFIRMED,
            DiagnosisState.REVISED,
            DiagnosisState.DISCARDED,
        }
    ),
    DiagnosisState.DISCARDED: frozenset(),
}

TERMINAL_STATES: frozenset[DiagnosisState] = frozenset(
    {DiagnosisState.DISCARDED}
)
"""Estados terminais — nenhuma transição sai deles."""

ACTIVE_STATES: frozenset[DiagnosisState] = frozenset(
    {
        DiagnosisState.HYPOTHESIS,
        DiagnosisState.INVESTIGATING,
        DiagnosisState.CONFIRMED,
        DiagnosisState.REVISED,
        DiagnosisState.IN_REMISSION,
    }
)
"""Estados ativos — diagnóstico presente no quadro clínico atual."""


class DiagnosisTransitionService:
    """
    Domain Service — valida transições de estado do Diagnosis.

    Stateless. Toda lógica de transição fica aqui (não na entidade),
    facilitando testes unitários e evitando acoplamento.
    """

    @staticmethod
    def validate(current: DiagnosisState, target: DiagnosisState) -> None:
        """
        Levanta InvalidDiagnosisTransitionError se a transição não é válida.

        Caso contrário, retorna silenciosamente.
        """
        if current == target:
            # Self-loop não é permitido (mas não levantamos — é no-op lógico).
            # Application services devem prevenir isso antes de chamar.
            return
        allowed = VALID_TRANSITIONS.get(current, frozenset())
        if target not in allowed:
            raise InvalidDiagnosisTransitionError(
                from_state=current.value, to_state=target.value
            )

    @staticmethod
    def can_transition(current: DiagnosisState, target: DiagnosisState) -> bool:
        """Versão não-exception da validação."""
        if current == target:
            return True
        return target in VALID_TRANSITIONS.get(current, frozenset())

    @staticmethod
    def allowed_targets(current: DiagnosisState) -> FrozenSet[DiagnosisState]:
        """Conjunto imutável de estados-alvo válidos a partir de `current`."""
        return VALID_TRANSITIONS.get(current, frozenset())

    @staticmethod
    def is_terminal(state: DiagnosisState) -> bool:
        """True se estado não permite mais transições."""
        return state in TERMINAL_STATES

    @staticmethod
    def is_active(state: DiagnosisState) -> bool:
        """True se estado representa diagnóstico ativo no quadro clínico."""
        return state in ACTIVE_STATES