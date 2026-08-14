"""merge import migration heads

Revision ID: 66cdf59bcf10
Revises: 7908e3cea13f, 587eb3afcba9
Create Date: 2026-08-13 22:01:29.910282

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66cdf59bcf10'
down_revision: Union[str, Sequence[str], None] = ('7908e3cea13f', '587eb3afcba9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
