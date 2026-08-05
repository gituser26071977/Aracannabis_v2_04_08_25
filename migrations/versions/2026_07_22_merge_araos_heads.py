"""merge araos heads — Sprint 4.5 pre-wave governance gate

Une os dois branches ativos de migrations AraOS antes de Sprint 4.5:

    Branch A: 0331305d2b3c → ec450c16ec01 → a1b2c3d4e5f6 → bb2cbd44835d
              → 83c3e98787e1 → ca1ef05ac0d2 → 9b93d2cb67d7
              → 791ba78aa8fb (araos_week5_agent_runtime)

    Branch B: bb2cbd44835d → 2026_07_15_neuro_s1 → 2026_07_15_cee_s31
              → 2026_07_16_neuro_registry_s32 → REDACTED
              → 2026_07_18_clinical_context_s42

Após este merge, existe um único head (`2026_07_22_merge_araos_heads`)
e Sprint 4.5 pode estender deterministicamente.

A migration é no-op (pass-through) — nenhum schema change.

Revision ID: 2026_07_22_merge_araos_heads
Revises: 791ba78aa8fb, 2026_07_18_clinical_context_s42
Create Date: 2026-07-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_07_22_merge_araos_heads"
down_revision = ("791ba78aa8fb", "2026_07_18_clinical_context_s42")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op merge.

    Este migration existe unicamente para consolidar os dois heads AraOS.
    Nenhuma mudança de schema. Não há nenhuma operação a reverter.
    """
    pass


def downgrade() -> None:
    """No-op downgrade.

    Alembic reverterá para os dois branches originais (791ba78aa8fb e
    2026_07_18_clinical_context_s42), cada um seguindo seu próprio
    caminho de downgrade.
    """
    pass
