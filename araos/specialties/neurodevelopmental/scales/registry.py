"""
AraOS Neurodevelopmental — Scale Registry.

Registro central de todas as escalas neuropsicológicas disponíveis no
módulo NEURODESENVOLVIMENTO. Cada escala é registrada como um
`ScaleSpec` imutável. Versões diferentes de uma mesma escala coexistem
indexadas por `(code, version)`.

Garantias:
    - Thread-safe: escrita feita na carga inicial (import-time).
    - Idempotente: registrar duas vezes o mesmo `(code, version)` levanta erro.
    - Versionamento: `latest()` resolve para a maior versão semântica.

Convenção de versão:
    "1.0" → release inicial
    "1.1" → pequena correção
    "2.0" → revisão maior (ex: mudança de pontuação de corte)
    "2.0-R" → revisão beta em produção

Uso típico (em `builtins/__init__.py`):

    from araos.specialties.neurodevelopmental.scales.registry import ScaleRegistry
    from .gad7 import GAD7_SPEC
    from .phq9 import PHQ9_SPEC

    ScaleRegistry.register(GAD7_SPEC)
    ScaleRegistry.register(PHQ9_SPEC)

Uso pelo runner:

    spec = ScaleRegistry.get("GAD7")
    result = ScaleRunner(spec).run(raw_responses)
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .base import ScaleSpec


class ScaleAlreadyRegisteredError(Exception):
    """Tentativa de registrar duas vezes o mesmo (code, version)."""


class ScaleNotFoundError(Exception):
    """Escala ou versão não encontrada no registry."""


class ScaleRegistry:
    """
    Registry singleton-like de escalas.

    Armazenamento: `_registry[code][version] = ScaleSpec`.
    """

    _registry: Dict[str, Dict[str, ScaleSpec]] = {}

    # ─── Escrita ────────────────────────────────────────────────────
    @classmethod
    def register(cls, spec: ScaleSpec) -> None:
        """
        Registra uma escala.

        Raises:
            ScaleAlreadyRegisteredError: se (code, version) já existe.
        """
        if spec.code not in cls._registry:
            cls._registry[spec.code] = {}
        versions = cls._registry[spec.code]
        if spec.version in versions:
            raise ScaleAlreadyRegisteredError(
                f"Escala {spec.code!r} versão {spec.version!r} já registrada"
            )
        versions[spec.version] = spec

    @classmethod
    def unregister(cls, code: str, version: Optional[str] = None) -> None:
        """
        Remove escala do registry. Se version=None, remove todas as versões.
        Útil apenas em testes.
        """
        if version is None:
            cls._registry.pop(code, None)
        else:
            versions = cls._registry.get(code, {})
            versions.pop(version, None)
            if not versions:
                cls._registry.pop(code, None)

    @classmethod
    def clear(cls) -> None:
        """Limpa todo o registry. Apenas para testes."""
        cls._registry.clear()

    # ─── Leitura ────────────────────────────────────────────────────
    @classmethod
    def get(cls, code: str, version: str = "latest") -> ScaleSpec:
        """
        Busca escala por código e versão.

        Args:
            code: código da escala (case-sensitive).
            version: versão específica ou "latest" (maior versão semântica).

        Raises:
            ScaleNotFoundError: se não encontrada.
        """
        versions = cls._registry.get(code)
        if not versions:
            raise ScaleNotFoundError(f"Escala {code!r} não registrada")
        if version == "latest":
            return cls._latest(versions)
        spec = versions.get(version)
        if spec is None:
            raise ScaleNotFoundError(
                f"Escala {code!r} versão {version!r} não encontrada. "
                f"Disponíveis: {sorted(versions.keys())}"
            )
        return spec

    @classmethod
    def has(cls, code: str, version: Optional[str] = None) -> bool:
        """Verifica se (code, version) existe. version=None → qualquer versão."""
        versions = cls._registry.get(code)
        if not versions:
            return False
        if version is None:
            return True
        return version in versions

    @classmethod
    def list(cls) -> List[ScaleSpec]:
        """Lista todas as escalas (versão latest de cada)."""
        return [cls._latest(versions) for versions in cls._registry.values()]

    @classmethod
    def list_by_age(cls, age_months: Optional[int]) -> List[ScaleSpec]:
        """Lista escalas aplicáveis para idade em meses."""
        return [s for s in cls.list() if s.is_applicable_for_age(age_months)]

    @classmethod
    def list_public(cls) -> List[ScaleSpec]:
        """Lista apenas escalas públicas (is_public=True)."""
        return [s for s in cls.list() if s.is_public]

    @classmethod
    def codes(cls) -> List[str]:
        """Lista códigos únicos de escalas registradas."""
        return sorted(cls._registry.keys())

    @classmethod
    def versions_of(cls, code: str) -> List[str]:
        """Lista versões disponíveis de uma escala."""
        versions = cls._registry.get(code, {})
        return sorted(versions.keys())

    # ─── Helpers internos ───────────────────────────────────────────
    @classmethod
    def _latest(cls, versions: Dict[str, ScaleSpec]) -> ScaleSpec:
        """Resolve a maior versão semântica entre as registradas."""
        if len(versions) == 1:
            return next(iter(versions.values()))

        def _sort_key(v: Tuple[str, ScaleSpec]) -> Tuple[int, ...]:
            version_str, _ = v
            # Versões como "1.0", "2.0-R". Strip suffix não-numérico.
            base = version_str.split("-")[0]
            try:
                parts = tuple(int(p) for p in base.split("."))
            except ValueError:
                return (0,)
            # Sufixo "-R" é anterior ao release base:
            #   "2.0"   → suffix_flag=1 (mais recente)
            #   "2.0-R" → suffix_flag=0 (beta)
            suffix_flag = 0 if "-" in version_str else 1
            return (suffix_flag,) + parts

        sorted_versions = sorted(versions.items(), key=_sort_key)
        return sorted_versions[-1][1]