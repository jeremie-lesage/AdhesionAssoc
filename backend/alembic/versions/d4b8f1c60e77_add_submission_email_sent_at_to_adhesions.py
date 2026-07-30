"""add submission_email_sent_at to adhesions

Revision ID: d4b8f1c60e77
Revises: c1a7e3b9d204
Create Date: 2026-07-30 13:10:00.000000

Trace l'accusé de réception envoyé à la soumission du formulaire. Colonne
distincte de `email_sent_at` (email de validation) : les deux envois ont des
causes d'échec indépendantes, et réutiliser la même colonne ferait passer une
adhésion pour « email envoyé » alors que seul l'accusé serait parti.

Les adhésions existantes restent à NULL : elles ont été créées avant l'ajout de
cet email, aucune n'a reçu d'accusé de réception.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4b8f1c60e77'
down_revision: Union[str, Sequence[str], None] = 'c1a7e3b9d204'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('adhesions', sa.Column('submission_email_sent_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('adhesions', 'submission_email_sent_at')
