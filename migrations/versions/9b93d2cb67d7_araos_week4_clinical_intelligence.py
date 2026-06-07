"""ARAOS Week 4: Clinical Intelligence Foundation

Revision ID: 9b93d2cb67d7
Revises: ca1ef05ac0d2
Create Date: 2026-06-07 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b93d2cb67d7'
down_revision = 'ca1ef05ac0d2'
branch_labels = None
depends_on = None


def upgrade():
    # ─── Clinical Diagnoses ──────────────────────────────────────────
    op.create_table(
        'araos_clinical_diagnoses',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('patient_id', sa.String(36), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('recorded_by', sa.String(36), nullable=True),
        sa.Column('entity_metadata', sa.JSON, nullable=True, default=dict),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('is_current', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('previous_version_id', sa.String(36), nullable=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('icd10_code', sa.String(10), nullable=True, index=True),
        sa.Column('icd10_description', sa.Text, nullable=True),
        sa.Column('snomed_code', sa.String(20), nullable=True, index=True),
        sa.Column('snomed_description', sa.Text, nullable=True),
        sa.Column('onset_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_primary', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_chronic', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('laterality', sa.String(20), nullable=True),
        sa.Column('severity', sa.String(20), nullable=True),
    )
    op.create_index('ix_diagnosis_patient_current', 'araos_clinical_diagnoses', ['patient_id', 'is_current'])
    op.create_index('ix_diagnosis_icd10', 'araos_clinical_diagnoses', ['icd10_code'])

    # ─── Clinical Medications ────────────────────────────────────────
    op.create_table(
        'araos_clinical_medications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('patient_id', sa.String(36), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('recorded_by', sa.String(36), nullable=True),
        sa.Column('entity_metadata', sa.JSON, nullable=True, default=dict),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('is_current', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('previous_version_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('generic_name', sa.String(255), nullable=True),
        sa.Column('dosage', sa.String(100), nullable=True),
        sa.Column('frequency', sa.String(100), nullable=True),
        sa.Column('route', sa.String(50), nullable=True),
        sa.Column('prescribed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stopped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stopped_reason', sa.Text, nullable=True),
        sa.Column('prescribed_by', sa.String(36), nullable=True),
    )
    op.create_index('ix_medication_patient_current', 'araos_clinical_medications', ['patient_id', 'is_current'])

    # ─── Clinical Allergies ──────────────────────────────────────────
    op.create_table(
        'araos_clinical_allergies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('patient_id', sa.String(36), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('recorded_by', sa.String(36), nullable=True),
        sa.Column('entity_metadata', sa.JSON, nullable=True, default=dict),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('is_current', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('previous_version_id', sa.String(36), nullable=True),
        sa.Column('substance', sa.String(255), nullable=False),
        sa.Column('substance_category', sa.String(100), nullable=True),
        sa.Column('reaction', sa.Text, nullable=True),
        sa.Column('severity', sa.String(20), nullable=True),
        sa.Column('onset_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified', sa.Boolean, nullable=False, server_default='false'),
    )
    op.create_index('ix_allergy_patient_current', 'araos_clinical_allergies', ['patient_id', 'is_current'])

    # ─── Clinical Procedures ─────────────────────────────────────────
    op.create_table(
        'araos_clinical_procedures',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('patient_id', sa.String(36), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('recorded_by', sa.String(36), nullable=True),
        sa.Column('entity_metadata', sa.JSON, nullable=True, default=dict),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('is_current', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('previous_version_id', sa.String(36), nullable=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('procedure_code', sa.String(20), nullable=True),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('performed_by', sa.String(36), nullable=True),
        sa.Column('result_summary', sa.Text, nullable=True),
    )
    op.create_index('ix_procedure_patient_date', 'araos_clinical_procedures', ['patient_id', 'performed_at'])

    # ─── Clinical Risk Factors ───────────────────────────────────────
    op.create_table(
        'araos_clinical_risk_factors',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('patient_id', sa.String(36), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('recorded_by', sa.String(36), nullable=True),
        sa.Column('entity_metadata', sa.JSON, nullable=True, default=dict),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('is_current', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('previous_version_id', sa.String(36), nullable=True),
        sa.Column('factor_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('severity', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('identified_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_risk_patient_active', 'araos_clinical_risk_factors', ['patient_id', 'is_active'])

    # ─── Clinical Profiles ───────────────────────────────────────────
    op.create_table(
        'araos_clinical_profiles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('patient_id', sa.String(36), nullable=False, unique=True, index=True),
        sa.Column('active_diagnoses', sa.JSON, nullable=False, default=list),
        sa.Column('active_medications', sa.JSON, nullable=False, default=list),
        sa.Column('allergies', sa.JSON, nullable=False, default=list),
        sa.Column('risk_factors', sa.JSON, nullable=False, default=list),
        sa.Column('procedures', sa.JSON, nullable=False, default=list),
        sa.Column('family_history', sa.JSON, nullable=True, default=dict),
        sa.Column('social_history', sa.JSON, nullable=True, default=dict),
        sa.Column('last_exams', sa.JSON, nullable=True, default=dict),
        sa.Column('last_summary', sa.Text, nullable=True),
        sa.Column('summary_version', sa.Integer, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('profile_metadata', sa.JSON, nullable=True, default=dict),
    )
    op.create_index('ix_clinical_profile_tenant', 'araos_clinical_profiles', ['tenant_id'])

    # ─── Clinical Timeline Entries ───────────────────────────────────
    op.create_table(
        'araos_clinical_timeline_entries',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False, index=True),
        sa.Column('patient_id', sa.String(36), nullable=False, index=True),
        sa.Column('event_id', sa.String(36), nullable=False, index=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_category', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', sa.String(36), nullable=True),
        sa.Column('entity_data', sa.JSON, nullable=True, default=dict),
        sa.Column('recorded_by', sa.String(36), nullable=True),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_timeline_patient_date', 'araos_clinical_timeline_entries', ['patient_id', 'event_date'])
    op.create_index('ix_timeline_event', 'araos_clinical_timeline_entries', ['event_id'])


def downgrade():
    op.drop_table('araos_clinical_timeline_entries')
    op.drop_table('araos_clinical_profiles')
    op.drop_table('araos_clinical_risk_factors')
    op.drop_table('araos_clinical_procedures')
    op.drop_table('araos_clinical_allergies')
    op.drop_table('araos_clinical_medications')
    op.drop_table('araos_clinical_diagnoses')
