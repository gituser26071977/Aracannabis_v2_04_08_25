"""
AraOS Neurodevelopmental — Diagnosis Classification (multi-classificação).

Um Diagnosis pode pertencer simultaneamente a múltiplos sistemas de
classificação:
    - CID-10 + CID-11 + DSM-5-TR + SNOMED + códigos internos
    - Cada um é OPCIONAL (mas o agregado deve ter ao menos uma classificação ativa)
    - Múltiplas classificações do mesmo sistema são permitidas (raro, mas válido)

Invariantes:
    - Pelo menos uma classificação ativa deve existir.
    - Classificações removidas permanecem no histórico (via Domain Events).
    - is_primary determina qual classificação aparece primeiro em relatórios.

ADR-0002 §2.7: 'Multi-classificação: cada diagnóstico poderá possuir
simultaneamente CID-10, CID-11, DSM-5-TR, SNOMED (reservado para futuro),
Classificações internas. Não assumir exclusividade.'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

from .condition import CID10Code, CID11Code, ConditionCode, DSM5Code


class ClassificationType(str, Enum):
    """Tipo de sistema de classificação."""

    CID10 = "cid10"
    CID11 = "cid11"
    DSM5_TR = "dsm5_tr"
    SNOMED = "snomed"
    INTERNAL = "internal"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ClassificationEntry:
    """
    Entrada unitária de classificação.

    `added_in_event_id` rastreia qual Domain Event originou esta classificação.
    Garante audit chain — se classificação for removida, evento ainda existe.
    """

    type: ClassificationType
    code: str
    is_primary: bool = False
    added_in_event_id: Optional[str] = None


@dataclass(frozen=True)
class DiagnosisClassification:
    """
    Composição de classificações ativas de um Diagnosis.

    Multi-classificação simultânea: zero ou mais entries de cada tipo.
    Invariante: `has_any()` deve ser True — pelo menos 1 classificação ativa.
    """

    entries: Tuple[ClassificationEntry, ...] = field(default_factory=tuple)

    @classmethod
    def empty(cls) -> "DiagnosisClassification":
        """Classificação vazia (estado inicial — antes da 1ª classificação)."""
        return cls(entries=tuple())

    @classmethod
    def of(
        cls,
        cid10: Optional[CID10Code] = None,
        cid11: Optional[CID11Code] = None,
        dsm5_tr: Optional[DSM5Code] = None,
        internal: Optional[ConditionCode] = None,
        added_in_event_id: Optional[str] = None,
    ) -> "DiagnosisClassification":
        """
        Builder para classificação inicial. Marca CID-10 como primário se presente.
        """
        entries: List[ClassificationEntry] = []
        if cid10 is not None:
            entries.append(
                ClassificationEntry(
                    type=ClassificationType.CID10,
                    code=str(cid10),
                    is_primary=True,
                    added_in_event_id=added_in_event_id,
                )
            )
        if cid11 is not None:
            entries.append(
                ClassificationEntry(
                    type=ClassificationType.CID11,
                    code=str(cid11),
                    is_primary=False,
                    added_in_event_id=added_in_event_id,
                )
            )
        if dsm5_tr is not None:
            entries.append(
                ClassificationEntry(
                    type=ClassificationType.DSM5_TR,
                    code=str(dsm5_tr),
                    is_primary=False,
                    added_in_event_id=added_in_event_id,
                )
            )
        if internal is not None:
            entries.append(
                ClassificationEntry(
                    type=ClassificationType.INTERNAL,
                    code=str(internal),
                    is_primary=False,
                    added_in_event_id=added_in_event_id,
                )
            )
        return cls(entries=tuple(entries))

    def has_any(self) -> bool:
        """True se há ao menos uma classificação ativa."""
        return len(self.entries) > 0

    def by_type(self, type: ClassificationType) -> Tuple[ClassificationEntry, ...]:
        """Retorna entries do tipo especificado."""
        return tuple(e for e in self.entries if e.type == type)

    def primary(self) -> Optional[ClassificationEntry]:
        """Retorna a classificação primária (None se nenhuma marcada)."""
        primaries = [e for e in self.entries if e.is_primary]
        if len(primaries) == 1:
            return primaries[0]
        if len(primaries) > 1:
            # Invariante violada: deve haver apenas 1 primária.
            # Retornamos a primeira; invariante é validada em `validate()`.
            return primaries[0]
        return None

    def with_added(
        self,
        type: ClassificationType,
        code: str,
        added_in_event_id: Optional[str],
        is_primary: bool = False,
    ) -> "DiagnosisClassification":
        """
        Retorna nova DiagnosisClassification com a entrada adicionada.

        Imutável — não muta self.
        """
        new_entry = ClassificationEntry(
            type=type,
            code=code,
            is_primary=is_primary,
            added_in_event_id=added_in_event_id,
        )
        # Se estamos marcando is_primary=True, desmarcar outras.
        new_entries: List[ClassificationEntry] = []
        if is_primary:
            new_entries = [
                ClassificationEntry(
                    type=e.type,
                    code=e.code,
                    is_primary=False,
                    added_in_event_id=e.added_in_event_id,
                )
                for e in self.entries
            ]
        else:
            new_entries = list(self.entries)
        new_entries.append(new_entry)
        return DiagnosisClassification(entries=tuple(new_entries))

    def with_removed(
        self,
        type: ClassificationType,
        code: str,
    ) -> "DiagnosisClassification":
        """
        Retorna nova DiagnosisClassification sem a entrada especificada.

        Imutável — não muta self. Se a entry não existir, retorna self.
        """
        new_entries = [
            e for e in self.entries if not (e.type == type and e.code == code)
        ]
        if len(new_entries) == len(self.entries):
            return self  # nada a remover
        return DiagnosisClassification(entries=tuple(new_entries))

    def validate(self) -> None:
        """
        Valida invariantes. Levanta ValueError se violar.

        Invariantes:
            - Pelo menos 1 classificação ativa.
            - No máximo 1 classificação marcada como primária.
        """
        if not self.has_any():
            raise ValueError(
                "DiagnosisClassification must have at least one active classification"
            )
        primaries = [e for e in self.entries if e.is_primary]
        if len(primaries) > 1:
            raise ValueError(
                f"DiagnosisClassification must have at most 1 primary classification; "
                f"found {len(primaries)}"
            )

    def to_dict(self) -> dict:
        """Serialização para JSON (API response, event payload)."""
        return {
            "entries": [
                {
                    "type": e.type.value,
                    "code": e.code,
                    "is_primary": e.is_primary,
                    "added_in_event_id": e.added_in_event_id,
                }
                for e in self.entries
            ],
            "primary_code": (
                self.primary().code if self.primary() is not None else None
            ),
            "primary_type": (
                self.primary().type.value if self.primary() is not None else None
            ),
        }