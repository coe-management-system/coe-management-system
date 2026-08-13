from app.models.import_status import ImportStatus
from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImportJob(Base):
    """
    Tracks a single Excel import attempt end-to-end: upload, validation,
    preview, and commit. One row per uploaded file.
    """
    __tablename__ = "imports"

    id: Mapped[int] = mapped_column(primary_key=True)

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)

    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=ImportStatus.CREATED,
    )

    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class ImportError(Base):
    """
    Row-level error/warning entries for a given ImportJob.
    Enough detail to let the frontend point the user at the exact
    sheet/row/column that failed and why.
    """
    __tablename__ = "import_errors"

    id: Mapped[int] = mapped_column(primary_key=True)

    import_id: Mapped[int] = mapped_column(
        ForeignKey("imports.id"),
        nullable=False,
        index=True,
    )

    sheet: Mapped[str] = mapped_column(String(100), nullable=False)

    row_number: Mapped[int] = mapped_column(Integer, nullable=False)

    column_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    error_code: Mapped[str] = mapped_column(String(50), nullable=False)

    message: Mapped[str] = mapped_column(Text, nullable=False)