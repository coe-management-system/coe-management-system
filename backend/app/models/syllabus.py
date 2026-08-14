from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SyllabusTopic(Base):
    __tablename__ = "syllabus_topics"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id"),
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    topic: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    planned_classes: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    completed_classes: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    target_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    actual_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )