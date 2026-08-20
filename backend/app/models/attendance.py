from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "subject_id",
            "session_date",
            name="uq_attendance_student_subject_session",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        nullable=False,
    )

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id"),
        nullable=False,
    )

    session_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # External record id (transaction-log "Addmission No"/Record ID) used for
    # idempotency when re-importing the same export. NULL for wide-grid sheets.
    external_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    # Audit trail: which source file / import job wrote this row.
    source_import_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_jobs.id"),
        nullable=True,
    )

    source_file: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )