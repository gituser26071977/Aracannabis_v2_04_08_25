"""merge heads

Revision ID: bb2cbd44835d
Revises: a1b2c3d4e5f6, f3a8c9d2e1b4_add_catalog_fields
Create Date: 2026-06-07 05:01:48.771395

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bb2cbd44835d'
down_revision = ('a1b2c3d4e5f6', 'f3a8c9d2e1b4_add_catalog_fields')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
