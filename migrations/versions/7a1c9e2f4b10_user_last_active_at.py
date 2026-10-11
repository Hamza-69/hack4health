"""user last_active_at, for chat retention

Revision ID: 7a1c9e2f4b10
Revises: 58c2d20ad12d
Create Date: 2026-10-11 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7a1c9e2f4b10'
down_revision: Union[str, Sequence[str], None] = '58c2d20ad12d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('last_active_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'last_active_at')
