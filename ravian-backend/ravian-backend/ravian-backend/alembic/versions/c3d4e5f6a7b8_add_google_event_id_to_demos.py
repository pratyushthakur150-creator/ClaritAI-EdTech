"""add google_event_id to demos

Revision ID: c3d4e5f6a7b8
Revises: f9a8b7c6d5e4
Create Date: 2026-02-22
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('demos', sa.Column('google_event_id', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('demos', 'google_event_id')
