from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    issuing_organization: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )


class CertificationAttempt(Base):
    __tablename__ = "certification_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        nullable=False,
    )

    certification_id: Mapped[int] = mapped_column(
        ForeignKey("certifications.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    score: Mapped[float | None] = mapped_column(
        nullable=True,
    )