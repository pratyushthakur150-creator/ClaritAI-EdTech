"""add lead created_by and updated_by columns

Revision ID: a1b2c3d4e5f6
Revises: 57ffa2e0901c
Create Date: 2026-02-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '57ffa2e0901c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add created_by as nullable first so we can backfill existing rows
    op.add_column('leads', sa.Column('created_by', UUID(as_uuid=True), nullable=True))
    op.add_column('leads', sa.Column('updated_by', UUID(as_uuid=True), nullable=True))

    # Add FK constraints (nullable columns can reference users)
    op.create_foreign_key('fk_leads_created_by_users', 'leads', 'users', ['created_by'], ['id'])
    op.create_foreign_key('fk_leads_updated_by_users', 'leads', 'users', ['updated_by'], ['id'])

    # Backfill created_by: set to first user of same tenant for existing leads
    # (Required before setting NOT NULL; ensure every tenant has at least one user)
    op.execute(sa.text("""
        UPDATE leads l
        SET created_by = (
            SELECT u.id FROM users u
            WHERE u.tenant_id = l.tenant_id
            ORDER BY u.created_at
            LIMIT 1
        )
        WHERE l.created_by IS NULL
    """))

    op.alter_column('leads', 'created_by', nullable=False)
    op.create_index(op.f('ix_leads_created_by'), 'leads', ['created_by'], unique=False)
    op.create_index(op.f('ix_leads_updated_by'), 'leads', ['updated_by'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_leads_updated_by'), table_name='leads')
    op.drop_index(op.f('ix_leads_created_by'), table_name='leads')
    op.drop_constraint('fk_leads_updated_by_users', 'leads', type_='foreignkey')
    op.drop_constraint('fk_leads_created_by_users', 'leads', type_='foreignkey')
    op.drop_column('leads', 'updated_by')
    op.drop_column('leads', 'created_by')
