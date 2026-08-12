"""Helper de log de atividade com tenant (P0-08/P0-12 compliant).

Resolve o `associacao_id` do contexto atual (g.current_association) e cria
o registro em `logs_atividades`. Todos os call sites devem usar esta função
em vez de instanciar `LogAtividade` direto, para nunca violar a regra P0-08
(INSERT sem tenant bloqueado pelo tenant_lib).
"""

from __future__ import annotations

from typing import Optional

from models import db, LogAtividade


def _resolve_assoc_id(profissional_id: Optional[int] = None) -> Optional[int]:
    """Resolve o tenant da requisição atual."""
    from flask import g, has_request_context

    if has_request_context():
        assoc = getattr(g, "current_association", None)
        if assoc is not None:
            return getattr(assoc, "id", None)

    # Fallback: primeiro vínculo ativo do profissional (multi-tenant)
    if profissional_id:
        from models_extra import UsuarioAssociacao

        vinculo = UsuarioAssociacao.query.filter_by(
            profissional_id=profissional_id, status="active"
        ).first()
        if vinculo:
            return vinculo.associacao_id

    return None


def registrar_atividade(
    profissional_id: Optional[int],
    acao: str,
    detalhes: Optional[str] = None,
) -> LogAtividade:
    """Cria e persiste um LogAtividade com associacao_id resolvido."""
    log = LogAtividade(
        profissional_id=profissional_id,
        associacao_id=_resolve_assoc_id(profissional_id),
        acao=acao,
        detalhes=detalhes,
    )
    db.session.add(log)
    try:
        db.session.commit()
    except Exception:  # noqa: BLE001 — log nunca deve quebrar o fluxo
        db.session.rollback()
    return log
