"""attendance hardening: student admission id + aggregates, attendance audit

Revision ID: 5f6a1b2c3d4e
Revises: 3613d151db58
Create Date: 2026-08-17 10:00:00.000000

Adds:
- students.admission_id        (unique institution-wide identifier)
- students.total_classes_held / total_present / total_absent / attendance_percentage
  (denormalised aggregate columns recomputed after every attendance import)
- students.attendance_updated_at / attendance_source_file (audit trail)
- attendance.external_id       (transaction-log record id, idempotency)
- attendance.source_import_id / source_file / updated_at (audit trail)

This is additive only: existing rows keep their current values and existing
attendance events are untouched. No backfill/recomputation is performed here;
see docs/attendance-import.md for the one-time recompute procedure.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5f6a1b2c3d4e"
down_revision: Union[str, Sequence[str], None] = "3613d151db58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "import_jobs",
        sa.Column("subject_hint", sa.String(length=30), nullable=True),
    )

    op.add_column(
        "students",
        sa.Column("admission_id", sa.String(length=50), nullable=True),
    )
    op.create_index(
        op.f("ix_students_admission_id"),
        "students",
        ["admission_id"],
        unique=True,
    )

    op.add_column(
        "students",
        sa.Column("total_classes_held", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "students",
        sa.Column("total_present", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "students",
        sa.Column("total_absent", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "students",
        sa.Column("attendance_percentage", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "students",
        sa.Column("attendance_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "students",
        sa.Column("attendance_source_file", sa.String(length=500), nullable=True),
    )

    op.add_column(
        "attendance",
        sa.Column("external_id", sa.String(length=50), nullable=True),
    )
    op.create_index(
        op.f("ix_attendance_external_id"),
        "attendance",
        ["external_id"],
        unique=False,
    )
    op.add_column(
        "attendance",
        sa.Column("source_import_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_attendance_source_import_id_import_jobs",
        "attendance",
        "import_jobs",
        ["source_import_id"],
        ["id"],
    )
    op.add_column(
        "attendance",
        sa.Column("source_file", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "attendance",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("import_jobs", "subject_hint")

    op.drop_column("attendance", "updated_at")
    op.drop_column("attendance", "source_file")
    op.drop_constraint(
        "fk_attendance_source_import_id_import_jobs",
        "attendance",
        type_="foreignkey",
    )
    op.drop_column("attendance", "source_import_id")
    op.drop_index(op.f("ix_attendance_external_id"), table_name="attendance")
    op.drop_column("attendance", "external_id")

    op.drop_column("students", "attendance_source_file")
    op.drop_column("students", "attendance_updated_at")
    op.drop_column("students", "attendance_percentage")
    op.drop_column("students", "total_absent")
    op.drop_column("students", "total_present")
    op.drop_column("students", "total_classes_held")
    op.drop_index(op.f("ix_students_admission_id"), table_name="students")
    op.drop_column("students", "admission_id")
