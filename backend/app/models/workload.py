from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkloadAllocation(Base):
    __tablename__ = "workload_allocations"

    id: Mapped[int] = mapped_column(primary_key=True)

    faculty_id: Mapped[int] = mapped_column(
        ForeignKey("faculty.id"),
        nullable=False,
    )

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id"),
        nullable=False,
    )

    allocated_hours: Mapped[float] = mapped_column(
        default=0,
        nullable=False,
    )

    completed_hours: Mapped[float] = mapped_column(
        default=0,
        nullable=False,
    )