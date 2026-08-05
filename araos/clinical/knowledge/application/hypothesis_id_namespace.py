"""
Hypothesis ID tenant-namespacing — Sprint 4.5 task #197 (RC1 pre-requisito).

PROBLEMA:
    ``ClinicalHypothesis.hypothesis_id`` é derivado deterministicamente de
    ``rule_id | gene_ids | correlation_ids | claim`` (vide
    ``araos.clinical.knowledge.domain.hypothesis._deterministic_hypothesis_id``).

    Isso significa que Tenant A com Patient X e Tenant B com Patient Y
    podem emitir o MESMO ``hypothesis_id`` quando ``rule_id``, genes,
    correlations e claim colidem — ainda que em corpos completamente
    diferentes. Em SQL, a chave composta ``(tenant_id, hypothesis_id)``
    impede a colisão no nível da PK, mas qualquer código que indexe por
    ``hypothesis_id`` sem escopo de tenant produziria falsos positivos
    cross-tenant.

SOLUÇÃO (não-domínio):
    O domain está FROZEN por Architecture Freeze v1.0. Modificar
    ``_deterministic_hypothesis_id`` é proibido.

    Este módulo aplica **post-processing determinístico** no boundary
    application: para cada ``ClinicalHypothesis`` produzido pela engine,
    re-deriva o ``hypothesis_id`` incluindo ``tenant_id`` no hash,
    preservando o significado clínico do conteúdo (regra, genes,
    correlations, claim) através do reuso da estrutura interna.

GARANTIAS:
    1. **Lossless do conteúdo.** Todos os campos exceto ``hypothesis_id``
       permanecem inalterados (claim, confidence, genes, expressions,
       correlations_used, evidence, status, rule_id, created_at,
       explanation).
    2. **Tenant-uniqueness.** Hypothesis IDs de tenants distintos
       NUNCA colidem (independentemente de genes/correlations/claim).
    3. **Determinístico.** Mesma tupla ``(tenant_id, rule_id, gene_ids,
       correlation_ids, claim)`` produz sempre o mesmo ``hypothesis_id``.
    4. **Idempotente.** Aplicar o namespacing 1× ou N× produz o mesmo ID.
    5. **Compatibilidade retroativa.** Hypotheses antigas (criadas antes
       do patch) continuam funcionando — o caller passa a usar o
       namespaced ID após a engine retornar.

NÃO-OBJETIVOS:
    - NÃO modifica ``hypothesis.py`` (domain FROZEN).
    - NÃO muda o contrato do ``HypothesisEngine``.
    - NÃO recalcula nenhum campo além do ``hypothesis_id``.
"""
from __future__ import annotations

import hashlib
from dataclasses import replace

from ..domain.hypothesis import ClinicalHypothesis


def _scoped_hypothesis_id(h: ClinicalHypothesis, tenant_id: str) -> str:
    """Deriva hypothesis_id tenant-scoped preservando a estrutura do hash."""
    # Estrutura idêntica à de _deterministic_hypothesis_id, com tenant_id
    # na frente. claim/gene_ids/correlation_ids/rule_id ficam preservados
    # no hash — garantindo que a ID permanece content-derived (auditável).
    raw = (
        f"{tenant_id}|{h.rule_id}|"
        f"{','.join(sorted(h.supporting_genes + h.contradicting_genes))}|"
        f"{','.join(sorted(h.correlations_used))}|"
        f"{h.claim}"
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"hyp_{digest}"


def namespace_hypothesis_ids(
    hypotheses: tuple[ClinicalHypothesis, ...],
    tenant_id: str,
) -> tuple[ClinicalHypothesis, ...]:
    """Aplica tenant-namespacing em lote.

    Args:
        hypotheses: tuple original produzido por ``HypothesisEngine.generate``.
        tenant_id: identificador do tenant (organização).

    Returns:
        tuple com hypothesis_id re-derivado para cada hypothesis.

    Note:
        - Não recalcula o conteúdo clínico.
        - Se o ``hypothesis_id`` já for tenant-scoped (idempotência),
          a saída será idêntica ao que já estava lá.
    """
    if not tenant_id:
        raise ValueError(
            "namespace_hypothesis_ids requer tenant_id não-vazio"
        )
    return tuple(
        replace(h, hypothesis_id=_scoped_hypothesis_id(h, tenant_id))
        for h in hypotheses
    )
