"""ARAOS Week 1: Tenant Layer

Revision ID: 83c3e98787e1
Revises: bb2cbd44835d
Create Date: 2026-06-07 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83c3e98787e1'
down_revision = 'bb2cbd44835d'
branch_labels = None
depends_on = None


def upgrade():
    # ─── Organization ────────────────────────────────────────────────
    op.create_table(
        'araos_organizations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('legal_name', sa.String(255), nullable=True),
        sa.Column('document', sa.String(20), nullable=True),
        sa.Column('plan', sa.String(50), nullable=False, server_default='free'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('primary_color', sa.String(7), nullable=True),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('favicon_url', sa.String(500), nullable=True),
        sa.Column('settings', sa.JSON, nullable=True, default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_org_status_plan', 'araos_organizations', ['status', 'plan'])
    op.create_index('ix_org_document', 'araos_organizations', ['document'])

    # ─── Clinic ──────────────────────────────────────────────────────
    op.create_table(
        'araos_clinics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('araos_organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=True),
        sa.Column('code', sa.String(50), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('state', sa.String(2), nullable=True),
        sa.Column('zip_code', sa.String(10), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='America/Sao_Paulo'),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('settings', sa.JSON, nullable=True, default=dict),
        sa.Column('active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_clinic_org_active', 'araos_clinics', ['organization_id', 'active'])
    op.create_unique_constraint('uq_clinic_org_slug', 'araos_clinics', ['organization_id', 'slug'])
    op.create_unique_constraint('uq_clinic_org_code', 'araos_clinics', ['organization_id', 'code'])

    # ─── Professional ────────────────────────────────────────────────
    op.create_table(
        'araos_professionals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('araos_organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('specialty', sa.String(100), nullable=True),
        sa.Column('professional_registry', sa.String(50), nullable=True),
        sa.Column('registry_state', sa.String(2), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('clinic_ids', sa.JSON, nullable=True, default=list),
        sa.Column('settings', sa.JSON, nullable=True, default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_professional_org_status', 'araos_professionals', ['organization_id', 'status'])
    op.create_index('ix_professional_registry', 'araos_professionals', ['professional_registry'])

    # ─── User ────────────────────────────────────────────────────────
    op.create_table(
        'araos_users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('araos_organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('roles', sa.JSON, nullable=False, default=list),
        sa.Column('permissions', sa.JSON, nullable=True, default=list),
        sa.Column('clinic_ids', sa.JSON, nullable=True, default=list),
        sa.Column('active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('email_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('mfa_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('failed_login_attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_user_org_active', 'araos_users', ['organization_id', 'active'])
    op.create_unique_constraint('uq_user_org_email', 'araos_users', ['organization_id', 'email'])

    # ─── Service Account ─────────────────────────────────────────────
    op.create_table(
        'araos_service_accounts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('araos_organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('service_type', sa.String(50), nullable=False),
        sa.Column('api_key_hash', sa.String(255), nullable=False),
        sa.Column('api_key_prefix', sa.String(8), nullable=False),
        sa.Column('permissions', sa.JSON, nullable=False, default=list),
        sa.Column('rate_limit_per_minute', sa.Integer, nullable=False, server_default='60'),
        sa.Column('clinic_ids', sa.JSON, nullable=True, default=list),
        sa.Column('active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_svc_acc_org_type', 'araos_service_accounts', ['organization_id', 'service_type'])
    op.create_index('ix_svc_acc_active', 'araos_service_accounts', ['organization_id', 'active'])

    # ─── Feature Flag ────────────────────────────────────────────────
    op.create_table(
        'araos_feature_flags',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), sa.ForeignKey('araos_organizations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('scope', sa.String(20), nullable=False, server_default='global'),
        sa.Column('target', sa.String(100), nullable=True),
        sa.Column('flag_metadata', sa.JSON, nullable=True, default=dict),
        sa.Column('rollout_percentage', sa.Integer, nullable=False, server_default='100'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_feature_flag_org_key', 'araos_feature_flags', ['organization_id', 'key'])
    op.create_index('ix_feature_flag_enabled', 'araos_feature_flags', ['organization_id', 'enabled'])
    op.create_unique_constraint(
        'uq_feature_flag_org_key_scope_target',
        'araos_feature_flags',
        ['organization_id', 'key', 'scope', 'target']
    )


def downgrade():
    op.drop_table('araos_feature_flags')
    op.drop_table('araos_service_accounts')
    op.drop_table('araos_users')
    op.drop_table('araos_professionals')
    op.drop_table('araos_clinics')
    op.drop_table('araos_organizations')
