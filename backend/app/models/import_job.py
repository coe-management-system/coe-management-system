from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    import_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="student",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="created",
    )

    total_rows: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    valid_rows: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    invalid_rows: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    duplicate_rows: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    
    file_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    file_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )

    validation_result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
