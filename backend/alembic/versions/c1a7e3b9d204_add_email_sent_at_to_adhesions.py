"""add email_sent_at to adhesions

Revision ID: c1a7e3b9d204
Revises: fae29ada105d
Create Date: 2026-07-30 12:40:00.000000

Trace la date d'envoi de l'email de confirmation. NULL sur une adhésion validée
signifie que l'envoi n'est pas confirmé : le back-office le signale et propose un
renvoi. Les adhésions existantes restent volontairement à NULL — rien en base ne
permet de savoir lesquelles ont réellement reçu leur email, et la clé Brevo a été
désactivée pendant 90 jours. Pour les considérer comme envoyées :

    UPDATE adhesions SET email_sent_at = NOW()
     WHERE status IN ('validated', 'paid') AND email_sent_at IS NULL;
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a7e3b9d204'
down_revision: Union[str, Sequence[str], None] = 'fae29ada105d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('adhesions', sa.Column('email_sent_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('adhesions', 'email_sent_at')
