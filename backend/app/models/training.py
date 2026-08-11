from sqlalchemy import ForeignKey, String, Text
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