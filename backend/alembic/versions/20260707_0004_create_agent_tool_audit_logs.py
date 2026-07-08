"""create agent tool audit logs table

Revision ID: 20260707_0004
Revises: 20260707_0003
Create Date: 2026-07-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = '20260707_0004'
down_revision = '20260707_0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'agent_tool_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tool_name', sa.String(length=120), nullable=False),
        sa.Column('audit_event', sa.String(length=160), nullable=False),
        sa.Column('ok', sa.Boolean(), nullable=False),
        sa.Column('input_payload', sa.JSON(), nullable=False),
        sa.Column('output_summary', sa.JSON(), nullable=True),
        sa.Column('error', sa.JSON(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_agent_tool_audit_logs_audit_event'), 'agent_tool_audit_logs', ['audit_event'], unique=False)
    op.create_index(op.f('ix_agent_tool_audit_logs_created_at'), 'agent_tool_audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_agent_tool_audit_logs_id'), 'agent_tool_audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_agent_tool_audit_logs_tool_name'), 'agent_tool_audit_logs', ['tool_name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_agent_tool_audit_logs_tool_name'), table_name='agent_tool_audit_logs')
    op.drop_index(op.f('ix_agent_tool_audit_logs_id'), table_name='agent_tool_audit_logs')
    op.drop_index(op.f('ix_agent_tool_audit_logs_created_at'), table_name='agent_tool_audit_logs')
    op.drop_index(op.f('ix_agent_tool_audit_logs_audit_event'), table_name='agent_tool_audit_logs')
    op.drop_table('agent_tool_audit_logs')
