"""Add missing EventType enum values to PostgreSQL

Revision ID: f9a8b7c6d5e4
Revises: 2096e83ae875
Create Date: 2026-02-13

Adds the following values to the PostgreSQL 'eventtype' enum:
- LEAD_CONTEXT_MERGED, LEAD_ASSIGNED, LEAD_DELETED, LEAD_STATUS_CHANGED
- CALL_TRIGGERED, CALL_UPDATED
- ENROLLMENT_CREATED
- DEMO_CANCELLED, DEMO_REMINDER_SENT
"""
from alembic import op

# revision identifiers
revision = 'f9a8b7c6d5e4'
down_revision = '2096e83ae875'
branch_labels = None
depends_on = None

# New EventType values to add
NEW_VALUES = [
    'LEAD_CONTEXT_MERGED',
    'LEAD_ASSIGNED',
    'LEAD_DELETED',
    'LEAD_STATUS_CHANGED',
    'CALL_TRIGGERED',
    'CALL_UPDATED',
    'ENROLLMENT_CREATED',
    'DEMO_CANCELLED',
    'DEMO_REMINDER_SENT',
]


def upgrade():
    # ALTER TYPE ... ADD VALUE cannot run inside a transaction block in PostgreSQL,
    # so we must execute outside the transaction.
    op.execute("COMMIT")
    for value in NEW_VALUES:
        op.execute(f"ALTER TYPE eventtype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade():
    # PostgreSQL does not support removing values from an enum type.
    # To fully downgrade, you would need to create a new enum type without
    # these values and migrate the column. This is intentionally left as a no-op.
    pass
