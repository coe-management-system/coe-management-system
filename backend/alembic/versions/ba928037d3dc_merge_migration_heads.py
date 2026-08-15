"""merge migration heads

Revision ID: ba928037d3dc
Revises: 37bebe8a4e74, 855012450635
Create Date: 2026-08-15 01:10:39.527914

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba928037d3dc'
down_revision: Union[str, Sequence[str], None] = ('37bebe8a4e74', '855012450635')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
