"""Add tenant_id and agent_id to call_logs table

Revision ID: b2c3d4e5f6a7
Revises: f9a8b7c6d5e4
Create Date: 2026-02-19

Adds tenant_id (for multi-tenant isolation) and agent_id (for team performance tracking)
to the call_logs table. Backfills tenant_id from the associated lead's tenant_id and
agent_id from the lead's assigned_to field.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'f9a8b7c6d5e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add tenant_id column (nullable first for backfill)
    op.add_column('call_logs',
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=True)
    )

    # 2. Add agent_id column (nullable, stays nullable)
    op.add_column('call_logs',
        sa.Column('agent_id', UUID(as_uuid=True), nullable=True)
    )

    # 3. Backfill tenant_id from associated leads
    op.execute(sa.text("""
        UPDATE call_logs
        SET tenant_id = leads.tenant_id
        FROM leads
        WHERE call_logs.lead_id = leads.id
          AND call_logs.tenant_id IS NULL
    """))

    # 4. Backfill agent_id from lead's assigned_to
    op.execute(sa.text("""
        UPDATE call_logs
        SET agent_id = leads.assigned_to
        FROM leads
        WHERE call_logs.lead_id = leads.id
          AND leads.assigned_to IS NOT NULL
          AND call_logs.agent_id IS NULL
    """))

    # 5. Add foreign key constraints
    op.create_foreign_key(
        'fk_call_logs_tenant',
        'call_logs', 'tenants',
        ['tenant_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_call_logs_agent',
        'call_logs', 'users',
        ['agent_id'], ['id'],
        ondelete='SET NULL'
    )

    # 6. Add indexes for performance
    op.create_index('idx_call_logs_tenant_id', 'call_logs', ['tenant_id'])
    op.create_index('idx_call_logs_agent_id', 'call_logs', ['agent_id'])


def downgrade() -> None:
    op.drop_index('idx_call_logs_agent_id', table_name='call_logs')
    op.drop_index('idx_call_logs_tenant_id', table_name='call_logs')
    op.drop_constraint('fk_call_logs_agent', 'call_logs', type_='foreignkey')
    op.drop_constraint('fk_call_logs_tenant', 'call_logs', type_='foreignkey')
    op.drop_column('call_logs', 'agent_id')
    op.drop_column('call_logs', 'tenant_id')
