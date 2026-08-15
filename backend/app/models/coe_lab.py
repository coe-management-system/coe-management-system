from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CoELab(Base):
    __tablename__ = "coe_labs"

    id: Mapped[int] = mapped_column(primary_key=True)

    coe_id: Mapped[int] = mapped_column(
        ForeignKey("coes.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    capacity: Mapped[int | None] = mapped_column(
        nullable=True,
    )