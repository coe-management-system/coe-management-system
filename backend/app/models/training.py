from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TrainingProgram(Base):
    __tablename__ = "training_programs"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    coe_id: Mapped[int] = mapped_column(
        ForeignKey("coes.id"),
        nullable=False,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False,
    )

    technology_id: Mapped[int] = mapped_column(
        ForeignKey("technologies.id"),
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    planned_hours: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    program_id: Mapped[int] = mapped_column(
        ForeignKey("training_programs.id"),
        nullable=False,
    )

    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id"),
        nullable=False,
    )

    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    faculty_id: Mapped[int] = mapped_column(
        ForeignKey("faculty.id"),
        nullable=False,
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    end_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    hours: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )