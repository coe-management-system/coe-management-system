"""update attendance records

Revision ID: 44592af30484
Revises: 66cdf59bcf10
Create Date: 2026-08-13 22:02:16.460501

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "44592af30484"
down_revision: Union[str, Sequence[str], None] = "66cdf59bcf10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "attendance",
        sa.Column("session_date", sa.Date(), nullable=False),
    )

    op.add_column(
        "attendance",
        sa.Column("status", sa.String(length=20), nullable=False),
    )

    op.create_unique_constraint(
        "uq_attendance_student_subject_session",
        "attendance",
        ["student_id", "subject_id", "session_date"],
    )

    op.drop_column("attendance", "total_classes")
    op.drop_column("attendance", "attended_classes")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "attendance",
        sa.Column(
            "total_classes",
            sa.Integer(),
            nullable=False,
        ),
    )

    op.add_column(
        "attendance",
        sa.Column(
            "attended_classes",
            sa.Integer(),
            nullable=False,
        ),
    )

    op.drop_constraint(
        "uq_attendance_student_subject_session",
        "attendance",
        type_="unique",
    )

    op.drop_column("attendance", "status")
    op.drop_column("attendance", "session_date")