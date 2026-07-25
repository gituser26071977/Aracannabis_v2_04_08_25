"""
AraOS Neurodevelopmental — Value Objects para códigos clínicos.

Códigos versionados e validados de sistemas de classificação clínica:
    - CID-10  (Classificação Internacional de Doenças, 10ª revisão)
    - CID-11  (Classificação Internacional de Doenças, 11ª revisão)
    - DSM-5-TR (Manual Diagnóstico e Estatístico de Transtornos Mentais)
    - ConditionCode  (código interno do AraOS — catálogo versionado)

Todos são frozen dataclasses: imutáveis, hashable, comparáveis por valor.

Invariantes:
    - CID-10 segue regex `^[A-Z]\\d{2}(\\.\\d)?$` (ex.: F84.0, F90).
    - CID-11 segue codificação oficial (placeholder para versão estável).
    - DSM-5-TR é string livre com versão (ex.: "299.00_F84.0").
    - ConditionCode é string não-vazia (referência ao catálogo interno).

Erros:
    - InvalidConditionCodeError quando regex falha.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


CID10_PATTERN = re.compile(r"^[A-Z]\d{2}(\.\d)?$")


class InvalidConditionCodeError(ValueError):
    """Código de condição não respeita formato esperado."""

    def __init__(self, code: str, system: str, expected_pattern: str) -> None:
        super().__init__(
            f"Invalid {system} code '{code}'. Expected pattern: {expected_pattern}"
        )
        self.code = code
        self.system = system


@dataclass(frozen=True)
class CID10Code:
    """
    Código CID-10. Exemplo: 'F84.0' (Autismo Infantil) ou 'F90' (TDAH).

    Regex: ^[A-Z]\\d{2}(\\.\\d)?$

    Invariantes:
        - Primeiro caractere: letra maiúscula (capítulo CID-10).
        - 2 dígitos seguintes.
        - Opcionalmente: ponto + 1 dígito (subcategoria).
    """

    value: str

    def __post_init__(self) -> None:
        if not CID10_PATTERN.match(self.value):
            raise InvalidConditionCodeError(
                code=self.value, system="CID-10", expected_pattern=CID10_PATTERN.pattern
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CID11Code:
    """
    Código CID-11. Formato: 'XA0X40' (placeholder — formato oficial será
    definido quando OMS publicar versão estável).

    Por enquanto aceita strings de 4-10 caracteres alfanuméricos maiúsculos.
    Validação relaxada — quando CID-11 estabilizar, regex será apertada.
    """

    value: str

    def __post_init__(self) -> None:
        if not re.match(r"^[A-Z0-9]{4,10}$", self.value):
            raise InvalidConditionCodeError(
                code=self.value,
                system="CID-11",
                expected_pattern="^[A-Z0-9]{4,10}$",
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DSM5Code:
    """
    Código DSM-5-TR. Formato livre com versão semântica.

    DSM-5-TR não usa códigos únicos — usa descritores. Para interoperabilidade,
    codificamos como 'CODE_LABEL' (ex.: '299.00_AUTISM' ou 'F84.0_AUTISM').

    Invariantes:
        - Não vazio.
        - Sem espaços nas pontas.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise InvalidConditionCodeError(
                code=self.value,
                system="DSM-5-TR",
                expected_pattern="non-empty string",
            )
        if self.value != self.value.strip():
            raise InvalidConditionCodeError(
                code=self.value,
                system="DSM-5-TR",
                expected_pattern="no leading/trailing whitespace",
            )

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ConditionCode:
    """
    Código interno AraOS — referência ao Catálogo de Condições versionado.

    Sistema próprio: 'NEURO_DEV_DISORDER', 'SENSORY_PROCESSING_DISORDER', etc.
    Catálogo versionado (Sprint 3.3 entrega versão completa).

    Invariantes:
        - Não vazio.
        - Apenas letras maiúsculas, dígitos e underscores.
    """

    value: str

    def __post_init__(self) -> None:
        if not re.match(r"^[A-Z][A-Z0-9_]{2,63}$", self.value):
            raise InvalidConditionCodeError(
                code=self.value,
                system="AraOS ConditionCode",
                expected_pattern="^[A-Z][A-Z0-9_]{2,63}$",
            )

    def __str__(self) -> str:
        return self.value