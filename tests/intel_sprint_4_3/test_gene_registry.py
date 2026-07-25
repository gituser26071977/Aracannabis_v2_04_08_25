"""
Test suite — Sprint 4.3 Phase 1: Clinical Gene Registry v1.0.

Cobre:

- ``ClinicalGeneId`` enum.
- ``RegistryVersion`` VO.
- ``GeneDefinition`` VO + invariantes.
- ``ClinicalGeneRegistry`` collection + invariantes.
- Seed canônico Registry v1.0.
- Loader + Repository (InMemory).
- Serialização roundtrip.
- Compatibilidade futura (Registry v1.1 simulado).

Cobertura alvo: ≥90%.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from araos.clinical.genome.domain import (
    CURRENT_REGISTRY_VERSION,
    ClinicalGeneId,
    ClinicalGeneRegistry,
    GeneDefinition,
    REGISTRY_V1_EFFECTIVE_FROM,
    RegistryVersion,
    build_registry_v1_definitions,
)
from araos.clinical.genome.infrastructure import (
    ClinicalGeneRegistryRepository,
    REDACTED,
    RegistryLoadError,
    load_registry,
    load_registry_v1,
    validate_gene_id,
    validate_registry_compatibility,
)


# ─── ClinicalGeneId ───────────────────────────────────────────────


class TestClinicalGeneId:
    """Enumeração canônica de Genes."""

    def test_seven_genes_present(self):
        """Registry v1.0 contém exatamente 7 Genes."""
        assert len(ClinicalGeneId) == 7

    def test_all_expected_values(self):
        """Os 7 valores canônicos estão presentes."""
        expected = {
            "SOCIAL_COMMUNICATION",
            "EXECUTIVE_FUNCTION",
            "SLEEP",
            "LANGUAGE",
            "EMOTIONAL_REGULATION",
            "ANXIETY_REGULATION",
            "MOBILITY",
        }
        assert set(ClinicalGeneId.values()) == expected

    def REDACTED(self):
        """SLEEP_QUALITY foi renomeado para SLEEP no Registry v1.0."""
        assert ClinicalGeneId.contains("SLEEP")
        assert not ClinicalGeneId.contains("SLEEP_QUALITY")

    def REDACTED(self):
        """ANXIETY foi renomeado para ANXIETY_REGULATION."""
        assert ClinicalGeneId.contains("ANXIETY_REGULATION")
        assert not ClinicalGeneId.contains("ANXIETY")

    def REDACTED(self):
        assert isinstance(ClinicalGeneId.values(), list)
        assert all(isinstance(v, str) for v in ClinicalGeneId.values())

    def test_contains_known(self):
        assert ClinicalGeneId.contains("SLEEP") is True
        assert ClinicalGeneId.contains("BOGUS_GENE") is False
        assert ClinicalGeneId.contains("") is False


# ─── RegistryVersion ──────────────────────────────────────────────


class TestRegistryVersion:
    """Versionamento SemVer do Registry."""

    def test_current_is_v1_0(self):
        """A versão atual é 1.0 (fixada por ADR-0005)."""
        assert CURRENT_REGISTRY_VERSION == "1.0"
        assert RegistryVersion.current().version_string == "1.0"

    def test_parse_minor_only(self):
        v = RegistryVersion.parse("1.0")
        assert v.major == 1
        assert v.minor == 0
        assert v.patch is None
        assert v.version_string == "1.0"

    def test_parse_minor_patch(self):
        v = RegistryVersion.parse("1.0.3")
        assert v.major == 1
        assert v.minor == 0
        assert v.patch == 3
        assert v.version_string == "1.0.3"

    def test_parse_invalid_format_raises(self):
        with pytest.raises(ValueError):
            RegistryVersion.parse("1")
        with pytest.raises(ValueError):
            RegistryVersion.parse("1.0.3.4")
        with pytest.raises(ValueError):
            RegistryVersion.parse("abc")

    def REDACTED(self):
        with pytest.raises(ValueError):
            RegistryVersion.parse("a.b")

    def test_major_must_be_at_least_1(self):
        with pytest.raises(ValueError):
            RegistryVersion(major=0, minor=0)

    def test_minor_must_be_non_negative(self):
        with pytest.raises(ValueError):
            RegistryVersion(major=1, minor=-1)

    def test_patch_must_be_non_negative(self):
        with pytest.raises(ValueError):
            RegistryVersion(major=1, minor=0, patch=-1)

    def REDACTED(self):
        with pytest.raises(ValueError):
            RegistryVersion(
                major=1,
                minor=0,
                effective_from=datetime(2026, 7, 17),  # naive
            )

    def test_compatibility_same_major(self):
        v1 = RegistryVersion(major=1, minor=0)
        v11 = RegistryVersion(major=1, minor=1)
        assert v1.is_compatible_with(v11)
        assert v11.is_compatible_with(v1)

    def REDACTED(self):
        v1 = RegistryVersion(major=1, minor=0)
        v2 = RegistryVersion(major=2, minor=0)
        assert not v1.is_compatible_with(v2)

    def test_immutable(self):
        v = RegistryVersion.current()
        with pytest.raises(Exception):  # FrozenInstanceError
            v.major = 99  # type: ignore[misc]

    def test_str(self):
        assert str(RegistryVersion(major=1, minor=0)) == "1.0"
        assert str(RegistryVersion(major=1, minor=0, patch=3)) == "1.0.3"


# ─── GeneDefinition ───────────────────────────────────────────────


class TestGeneDefinition:
    """Value Object imutável."""

    def _make(self, gene_id: ClinicalGeneId = ClinicalGeneId.SLEEP) -> GeneDefinition:
        return GeneDefinition(
            id=gene_id,
            display_name="Sleep",
            description="Sono — função clínica fundamental.",
            clinical_functions=("sleep", "circadian"),
            registry_version=RegistryVersion.current(),
        )

    def test_basic_construction(self):
        d = self._make()
        assert d.id == ClinicalGeneId.SLEEP
        assert d.display_name == "Sleep"
        assert d.clinical_functions == ("sleep", "circadian")
        assert d.registry_version.version_string == "1.0"

    def test_primary_clinical_function(self):
        d = self._make()
        assert d.primary_clinical_function == "sleep"

    def test_empty_display_name_raises(self):
        with pytest.raises(ValueError, match="display_name"):
            GeneDefinition(
                id=ClinicalGeneId.SLEEP,
                display_name="",
                description="x",
                clinical_functions=("sleep",),
                registry_version=RegistryVersion.current(),
            )

    def REDACTED(self):
        with pytest.raises(ValueError, match="display_name"):
            GeneDefinition(
                id=ClinicalGeneId.SLEEP,
                display_name="   ",
                description="x",
                clinical_functions=("sleep",),
                registry_version=RegistryVersion.current(),
            )

    def test_empty_description_raises(self):
        with pytest.raises(ValueError, match="description"):
            GeneDefinition(
                id=ClinicalGeneId.SLEEP,
                display_name="Sleep",
                description="",
                clinical_functions=("sleep",),
                registry_version=RegistryVersion.current(),
            )

    def REDACTED(self):
        with pytest.raises(ValueError, match="clinical_functions"):
            GeneDefinition(
                id=ClinicalGeneId.SLEEP,
                display_name="Sleep",
                description="x",
                clinical_functions=(),
                registry_version=RegistryVersion.current(),
            )

    def REDACTED(self):
        with pytest.raises(ValueError, match="clinical_functions"):
            GeneDefinition(
                id=ClinicalGeneId.SLEEP,
                display_name="Sleep",
                description="x",
                clinical_functions=("sleep", ""),
                registry_version=RegistryVersion.current(),
            )

    def REDACTED(self):
        with pytest.raises(ValueError, match="registry_version"):
            GeneDefinition(
                id=ClinicalGeneId.SLEEP,
                display_name="Sleep",
                description="x",
                clinical_functions=("sleep",),
                registry_version="1.0",  # type: ignore[arg-type]
            )

    def test_naive_created_at_raises(self):
        with pytest.raises(ValueError, match="timezone"):
            GeneDefinition(
                id=ClinicalGeneId.SLEEP,
                display_name="Sleep",
                description="x",
                clinical_functions=("sleep",),
                registry_version=RegistryVersion.current(),
                created_at=datetime(2026, 7, 17),  # naive
            )

    def test_immutable(self):
        d = self._make()
        with pytest.raises(Exception):  # FrozenInstanceError
            d.display_name = "Renamed"  # type: ignore[misc]

    def test_metadata_immutable(self):
        d = self._make()
        with pytest.raises(TypeError):
            d.metadata["new_key"] = "value"  # type: ignore[index]

    def test_metadata_default_is_empty(self):
        d = self._make()
        assert len(d.metadata) == 0


# ─── ClinicalGeneRegistry ─────────────────────────────────────────


class TestClinicalGeneRegistry:
    """Coleção imutável de GeneDefinitions."""

    def test_construction_from_seed(self):
        registry = ClinicalGeneRegistry(
            version=RegistryVersion.current(),
            definitions=build_registry_v1_definitions(),
        )
        assert len(registry) == 7
        assert registry.version.version_string == "1.0"

    def test_empty_registry_raises(self):
        with pytest.raises(ValueError, match="vazio"):
            ClinicalGeneRegistry(
                version=RegistryVersion.current(),
                definitions=(),
            )

    def test_get_by_enum(self):
        registry = load_registry_v1()
        d = registry.get(ClinicalGeneId.SLEEP)
        assert d is not None
        assert d.id == ClinicalGeneId.SLEEP

    def test_get_by_string(self):
        registry = load_registry_v1()
        d = registry.get("SLEEP")
        assert d is not None
        assert d.id == ClinicalGeneId.SLEEP

    def test_get_unknown_returns_none(self):
        registry = load_registry_v1()
        assert registry.get("BOGUS") is None

    def test_contains(self):
        registry = load_registry_v1()
        assert ClinicalGeneId.SLEEP in registry
        assert "SLEEP" in registry
        assert "BOGUS" not in registry

    def test_iteration_yields_definitions(self):
        registry = load_registry_v1()
        ids = [d.id for d in registry]
        assert ClinicalGeneId.SLEEP in ids
        assert len(ids) == 7

    def test_len(self):
        registry = load_registry_v1()
        assert len(registry) == 7

    def test_duplicate_ids_raises(self):
        defs = build_registry_v1_definitions()
        duplicate = defs[0]
        # Replace last definition with duplicate of first
        bad_defs = defs[:-1] + (duplicate,)
        with pytest.raises(ValueError, match="IDs duplicados"):
            ClinicalGeneRegistry(
                version=RegistryVersion.current(),
                definitions=bad_defs,
            )

    def REDACTED(self):
        # Two GeneDefinitions with different ids but same display_name
        v = RegistryVersion.current()
        d1 = GeneDefinition(
            id=ClinicalGeneId.SLEEP,
            display_name="Sleep",
            description="d1",
            clinical_functions=("sleep",),
            registry_version=v,
        )
        d2 = GeneDefinition(
            id=ClinicalGeneId.LANGUAGE,
            display_name="Sleep",  # duplicate
            description="d2",
            clinical_functions=("language",),
            registry_version=v,
        )
        with pytest.raises(ValueError, match="display_names"):
            ClinicalGeneRegistry(
                version=v,
                definitions=(d1, d2),
            )

    def REDACTED(self):
        v = RegistryVersion.current()
        d1 = GeneDefinition(
            id=ClinicalGeneId.SLEEP,
            display_name="Sleep",
            description="d1",
            clinical_functions=("sleep",),
            registry_version=v,
        )
        d2 = GeneDefinition(
            id=ClinicalGeneId.LANGUAGE,
            display_name="Language",
            description="d2",
            clinical_functions=("sleep",),  # duplicate primary
            registry_version=v,
        )
        with pytest.raises(ValueError, match="primary_clinical_function"):
            ClinicalGeneRegistry(
                version=v,
                definitions=(d1, d2),
            )

    def test_gene_not_in_enum_raises(self):
        v = RegistryVersion.current()
        # Manually create a definition with a bogus id (bypassing enum)
        bogus = GeneDefinition.__new__(GeneDefinition)
        object.__setattr__(bogus, "id", "BOGUS_GENE")
        object.__setattr__(bogus, "display_name", "Bogus")
        object.__setattr__(bogus, "description", "x")
        object.__setattr__(bogus, "clinical_functions", ("x",))
        object.__setattr__(bogus, "registry_version", v)
        object.__setattr__(
            bogus, "created_at", datetime.now(timezone.utc)
        )
        from types import MappingProxyType
        object.__setattr__(bogus, "metadata", MappingProxyType({}))

        with pytest.raises(ValueError, match="não existe em ClinicalGeneId"):
            ClinicalGeneRegistry(version=v, definitions=(bogus,))

    def REDACTED(self):
        v1 = RegistryVersion(major=1, minor=0)
        v11 = RegistryVersion(major=1, minor=1)
        d = GeneDefinition(
            id=ClinicalGeneId.SLEEP,
            display_name="Sleep",
            description="x",
            clinical_functions=("sleep",),
            registry_version=v11,  # mismatch
        )
        with pytest.raises(ValueError, match="versão"):
            ClinicalGeneRegistry(version=v1, definitions=(d,))

    def REDACTED(self):
        with pytest.raises(ValueError, match="definição inválida"):
            ClinicalGeneRegistry(
                version=RegistryVersion.current(),
                definitions=("not a definition",),  # type: ignore[arg-type]
            )

    def test_naive_created_at_raises(self):
        v = RegistryVersion.current()
        d = build_registry_v1_definitions()[0]
        with pytest.raises(ValueError, match="timezone"):
            ClinicalGeneRegistry(
                version=v,
                definitions=(d,),
                created_at=datetime(2026, 7, 17),  # naive
            )

    def test_immutable(self):
        registry = load_registry_v1()
        with pytest.raises(Exception):  # FrozenInstanceError
            registry.definitions = ()  # type: ignore[misc]

    def test_metadata_default_is_empty(self):
        registry = load_registry_v1()
        assert len(registry.metadata) == 0

    def test_metadata_immutable(self):
        registry = load_registry_v1()
        with pytest.raises(TypeError):
            registry.metadata["x"] = 1  # type: ignore[index]


# ─── Seed ─────────────────────────────────────────────────────────


class TestSeedRegistryV1:
    """Seed canônico Registry v1.0."""

    def test_seven_genes(self):
        defs = build_registry_v1_definitions()
        assert len(defs) == 7

    def test_all_genes_in_seed(self):
        defs = build_registry_v1_definitions()
        ids = {d.id for d in defs}
        assert ids == set(ClinicalGeneId)

    def test_all_at_registry_v1(self):
        defs = build_registry_v1_definitions()
        for d in defs:
            assert d.registry_version.version_string == "1.0"

    def test_effective_from_fixed(self):
        defs = build_registry_v1_definitions()
        for d in defs:
            assert d.created_at == REGISTRY_V1_EFFECTIVE_FROM

    def test_unique_display_names(self):
        defs = build_registry_v1_definitions()
        names = [d.display_name for d in defs]
        assert len(names) == len(set(names))

    def test_unique_primary_functions(self):
        defs = build_registry_v1_definitions()
        functions = [d.primary_clinical_function for d in defs]
        assert len(functions) == len(set(functions))

    def test_all_have_clinical_functions(self):
        defs = build_registry_v1_definitions()
        for d in defs:
            assert len(d.clinical_functions) >= 1

    def test_seed_is_reproducible(self):
        """Duas chamadas produzem o mesmo Seed (mesmo effective_from)."""
        defs1 = build_registry_v1_definitions()
        defs2 = build_registry_v1_definitions()
        assert defs1 == defs2


# ─── Loader ───────────────────────────────────────────────────────


class TestRegistryLoader:
    """Loader + validation."""

    def test_load_v1(self):
        registry = load_registry_v1()
        assert len(registry) == 7
        assert registry.version.version_string == "1.0"

    def test_load_empty_raises(self):
        with pytest.raises(RegistryLoadError):
            load_registry(RegistryVersion.current(), [])

    def test_validate_gene_id_valid(self):
        gene_id = validate_gene_id("SLEEP")
        assert gene_id == ClinicalGeneId.SLEEP

    def test_validate_gene_id_invalid(self):
        with pytest.raises(RegistryLoadError):
            validate_gene_id("BOGUS_GENE")

    def REDACTED(self):
        registry = load_registry_v1()
        validate_registry_compatibility(registry, ClinicalGeneId.SLEEP)

    def REDACTED(self):
        registry = load_registry_v1()
        with pytest.raises(RegistryLoadError):
            validate_registry_compatibility(registry, "BOGUS")


# ─── Serialization Roundtrip ──────────────────────────────────────


class TestSerializationRoundtrip:
    """Serialização/desserialização canônica."""

    def test_registry_roundtrip(self):
        registry = load_registry_v1()
        serialized = registry.to_dict()
        restored = ClinicalGeneRegistry.from_dict(serialized)
        assert restored == registry

    def test_gene_definition_roundtrip(self):
        d = build_registry_v1_definitions()[0]
        restored = GeneDefinition.from_dict(d.to_dict())
        assert restored == d

    def test_registry_to_dict_shape(self):
        registry = load_registry_v1()
        d = registry.to_dict()
        assert d["version"] == "1.0"
        assert "effective_from" in d
        assert "definitions" in d
        assert len(d["definitions"]) == 7
        for defn in d["definitions"]:
            assert "id" in defn
            assert "display_name" in defn
            assert "description" in defn
            assert "clinical_functions" in defn
            assert "registry_version" in defn
            assert "registry_version_effective_from" in defn
            assert "created_at" in defn

    def REDACTED(self):
        with pytest.raises(ValueError, match="version"):
            ClinicalGeneRegistry.from_dict({"definitions": []})

    def REDACTED(self):
        with pytest.raises(ValueError, match="registry_version"):
            GeneDefinition.from_dict(
                {
                    "id": "SLEEP",
                    "display_name": "Sleep",
                    "description": "x",
                    "clinical_functions": ["sleep"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )


# ─── Repository ───────────────────────────────────────────────────


class TestInMemoryRepository:
    """Repositório in-memory."""

    def test_default_preloads_v1(self):
        repo = REDACTED()
        assert repo.list_versions() == ["1.0"]

    def test_no_preload_is_empty(self):
        repo = REDACTED(preload=False)
        assert repo.list_versions() == []
        with pytest.raises(RuntimeError):
            repo.get_current()

    def test_save_persists(self):
        repo = REDACTED(preload=False)
        repo.save(load_registry_v1())
        assert repo.list_versions() == ["1.0"]

    def test_save_idempotent_same_version(self):
        repo = REDACTED()
        reg1 = load_registry_v1()
        reg2 = load_registry_v1()
        repo.save(reg1)
        repo.save(reg2)
        assert repo.list_versions() == ["1.0"]

    def test_get_version_returns_registry(self):
        repo = REDACTED()
        reg = repo.get_version("1.0")
        assert reg is not None
        assert len(reg) == 7

    def REDACTED(self):
        repo = REDACTED()
        assert repo.get_version("99.0") is None

    def test_get_current_v1(self):
        repo = REDACTED()
        current = repo.get_current()
        assert current.version.version_string == "1.0"

    def test_is_known(self):
        repo = REDACTED()
        assert repo.is_known(ClinicalGeneId.SLEEP)
        assert repo.is_known("SLEEP")
        assert not repo.is_known("BOGUS")

    def test_contains_protocol(self):
        repo = REDACTED()
        assert ClinicalGeneId.SLEEP in repo
        assert "SLEEP" in repo
        assert "BOGUS" not in repo

    def test_len(self):
        repo = REDACTED()
        assert len(repo) == 1  # only v1.0

    def test_is_abstract(self):
        assert issubclass(
            REDACTED,
            ClinicalGeneRegistryRepository,
        )


# ─── Future Compatibility ─────────────────────────────────────────


class TestFutureCompatibility:
    """Garantias para futuras versões do Registry."""

    def test_load_v1_1_simulated(self):
        """Carregar Registry v1.1 com Gene novo coexiste com v1.0."""
        repo = REDACTED()
        # v1.0 já carregado
        v10 = repo.get_version("1.0")
        assert v10 is not None

        # Simular v1.1 com definições PRÓPRIAS (vinculadas a v1.1)
        v11_version = RegistryVersion(major=1, minor=1)
        v11_def = GeneDefinition(
            id=ClinicalGeneId.SLEEP,
            display_name="Sleep",
            description="Sleep gene at v1.1",
            clinical_functions=("sleep", "circadian", "rest"),
            registry_version=v11_version,
        )
        v11_registry = ClinicalGeneRegistry(
            version=v11_version,
            definitions=(v11_def,),
        )
        repo.save(v11_registry)

        assert sorted(repo.list_versions()) == ["1.0", "1.1"]
        assert repo.get_version("1.1") is not None
        assert repo.get_current().version.version_string == "1.1"

    def test_is_compatible_v1_0_and_v1_1(self):
        v10 = RegistryVersion(major=1, minor=0)
        v11 = RegistryVersion(major=1, minor=1)
        assert v10.is_compatible_with(v11)

    def test_incompatible_v1_and_v2(self):
        v1 = RegistryVersion(major=1, minor=0)
        v2 = RegistryVersion(major=2, minor=0)
        assert not v1.is_compatible_with(v2)

    def REDACTED(self):
        """Loader aceita qualquer versão + definições (testes, futuro)."""
        v_future = RegistryVersion(major=2, minor=0)
        # Definição vinculada a v2.0
        future_def = GeneDefinition(
            id=ClinicalGeneId.SLEEP,
            display_name="Sleep",
            description="Sleep gene at v2.0",
            clinical_functions=("sleep",),
            registry_version=v_future,
        )
        registry = load_registry(v_future, (future_def,))
        assert registry.version.version_string == "2.0"
        assert len(registry) == 1


# ─── Linguagem Ubíqua ─────────────────────────────────────────────


class TestUbiquitousLanguage:
    """Garantias de uso correto da Linguagem Ubíqua consolidada."""

    def test_no_sleep_quality_in_seed(self):
        """SLEEP_QUALITY foi renomeado para SLEEP (Registry v1.0)."""
        defs = build_registry_v1_definitions()
        ids = [d.id.value for d in defs]
        assert "SLEEP_QUALITY" not in ids
        assert "SLEEP" in ids

    def test_no_anxiety_as_gene(self):
        """ANXIETY foi renomeado para ANXIETY_REGULATION."""
        defs = build_registry_v1_definitions()
        ids = [d.id.value for d in defs]
        assert "ANXIETY" not in ids
        assert "ANXIETY_REGULATION" in ids

    def REDACTED(self):
        """Genes representam Funções Clínicas Fundamentais, não capabilities."""
        # Verificar que GeneDefinition usa `clinical_functions` (plural).
        d = build_registry_v1_definitions()[0]
        assert hasattr(d, "clinical_functions")
        assert isinstance(d.clinical_functions, tuple)

        # Verificar que `capability` (singular) NÃO é nome de campo
        # no módulo gene_definition.py.
        import inspect
        from araos.clinical.genome.domain import gene_definition as gd_mod
        source = inspect.getsource(gd_mod)
        # Não deve ter campo/atributo `capability` (singular)
        # usado como conceito central.
        assert "self.capability" not in source
        assert "self.capabilities" not in source
        # Deve usar `clinical_functions` (plural).
        assert "clinical_functions" in source

    def REDACTED(self):
        """Toda GeneDefinition carrega registry_version."""
        defs = build_registry_v1_definitions()
        for d in defs:
            assert isinstance(d.registry_version, RegistryVersion)
            assert d.registry_version.version_string == "1.0"

    def REDACTED(self):
        """Toda ClinicalGeneRegistry carrega RegistryVersion."""
        registry = load_registry_v1()
        assert isinstance(registry.version, RegistryVersion)
        assert registry.version.version_string == "1.0"