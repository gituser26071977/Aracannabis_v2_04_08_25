"""
conftest.py — fixtures Sprint 4.3 (Clinical Genome Engine — Phase 1).

Reuso de padrões Sprint 4.1/4.2:

- sys.path injection (project root)
- Imports diretos do domínio (Phase 1 não usa DB)
"""

from __future__ import annotations

import os
import sys

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".."),
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)