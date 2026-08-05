"""Knowledge API — public re-exports.

This module exposes the Blueprint for the AraOS Clinical Intelligence
Knowledge API (RC1 Gate 2 / Sprint 4.5 §W3). It is intended to be the
single import surface for ``app_cors_livre.py``.

Usage in ``app_cors_livre.py``::

    from interfaces.rest.v1 import knowledge_bp
    app.register_blueprint(knowledge_bp)
"""

from interfaces.rest.v1.knowledge import knowledge_bp


__all__ = ["knowledge_bp"]
