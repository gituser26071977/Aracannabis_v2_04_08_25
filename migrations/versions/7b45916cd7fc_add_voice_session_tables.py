"""add voice session tables

Revision ID: 7b45916cd7fc
Revises: bb2cbd44835d
Create Date: 2026-06-07 05:04:09.907869

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7b45916cd7fc'
down_revision = 'bb2cbd44835d'
branch_labels = None
depends_on = None


def upgrade():
    # Tabela de sessões de voz
    op.create_table('voice_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), nullable=False),
        sa.Column('patient_id', sa.String(36), nullable=False),
        sa.Column('doctor_id', sa.String(36), nullable=False),
        sa.Column('specialty', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), default=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer, nullable=True),
        sa.Column('wake_word', sa.String(50), server_default='Ara'),
        sa.Column('language', sa.String(10), server_default='pt-BR'),
        sa.Column('mode', sa.String(20), server_default='full'),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('total_audio_duration_ms', sa.Integer, server_default='0'),
        sa.Column('speech_duration_ms', sa.Integer, server_default='0'),
        sa.Column('doctor_speech_duration_ms', sa.Integer, server_default='0'),
        sa.Column('patient_speech_duration_ms', sa.Integer, server_default='0'),
        sa.Column('structured_data', sa.JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_voice_sessions_patient', 'voice_sessions', ['patient_id', 'started_at'])
    op.create_index('idx_voice_sessions_tenant', 'voice_sessions', ['tenant_id', 'started_at'])

    # Tabela de transcrições
    op.create_table('voice_transcripts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('voice_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('segment_index', sa.Integer, nullable=False),
        sa.Column('speaker', sa.String(20), nullable=False),
        sa.Column('start_time_ms', sa.Integer, nullable=False),
        sa.Column('end_time_ms', sa.Integer, nullable=False),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('text_normalized', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('is_final', sa.Boolean, server_default='true'),
        sa.Column('language', sa.String(10), server_default='pt-BR'),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now()),
        sa.UniqueConstraint('session_id', 'segment_index'),
    )
    op.create_index('idx_voice_transcripts_session', 'voice_transcripts', ['session_id', 'segment_index'])

    # Tabela de entidades clínicas
    op.create_table('voice_entities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('voice_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('transcript_id', sa.String(36), sa.ForeignKey('voice_transcripts.id'), nullable=True),
        sa.Column('entity_type', sa.String(30), nullable=False),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('normalized_name', sa.String(255), nullable=True),
        sa.Column('cui', sa.String(20), nullable=True),
        sa.Column('icd10', sa.String(20), nullable=True),
        sa.Column('atc', sa.String(20), nullable=True),
        sa.Column('loinc', sa.String(20), nullable=True),
        sa.Column('value', sa.Text, nullable=True),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('temporal', sa.String(50), nullable=True),
        sa.Column('negated', sa.Boolean, server_default='false'),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('source', sa.String(20), server_default='patient'),
        sa.Column('start_time_ms', sa.Integer, nullable=True),
        sa.Column('end_time_ms', sa.Integer, nullable=True),
        sa.Column('persisted_to_ehr', sa.Boolean, server_default='false'),
        sa.Column('persisted_record_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now()),
    )
    op.create_index('idx_voice_entities_session', 'voice_entities', ['session_id', 'entity_type'])

    # Tabela de ações
    op.create_table('voice_actions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('voice_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('parameters', sa.JSON(), server_default='{}'),
        sa.Column('preview', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), server_default='proposed'),
        sa.Column('confirmed_by', sa.String(36), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confirmation_method', sa.String(20), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=sa.func.now()),
    )

    # Tabela de audit log
    op.create_table('voice_audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('session_id', sa.String(36), sa.ForeignKey('voice_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_data', sa.JSON(), server_default='{}'),
        sa.Column('doctor_id', sa.String(36), nullable=False),
        sa.Column('patient_id', sa.String(36), nullable=False),
        sa.Column('occurred_at', sa.DateTime(timezone=True), default=sa.func.now()),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
    )
    op.create_index('idx_voice_audit_session', 'voice_audit_logs', ['session_id', 'occurred_at'])


def downgrade():
    op.drop_index('idx_voice_audit_session', table_name='voice_audit_logs')
    op.drop_table('voice_audit_logs')
    op.drop_table('voice_actions')
    op.drop_index('idx_voice_entities_session', table_name='voice_entities')
    op.drop_table('voice_entities')
    op.drop_index('idx_voice_transcripts_session', table_name='voice_transcripts')
    op.drop_table('voice_transcripts')
    op.drop_index('idx_voice_sessions_tenant', table_name='voice_sessions')
    op.drop_index('idx_voice_sessions_patient', table_name='voice_sessions')
    op.drop_table('voice_sessions')
