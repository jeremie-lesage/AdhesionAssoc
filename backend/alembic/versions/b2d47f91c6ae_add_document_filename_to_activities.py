"""add document_filename to activities

Revision ID: b2d47f91c6ae
Revises: d4b8f1c60e77
Create Date: 2026-07-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2d47f91c6ae'
down_revision: Union[str, Sequence[str], None] = 'd4b8f1c60e77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('activities', sa.Column('document_filename', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('activities', 'document_filename')
