"""
Timetable Version Model (M3-11)

Stores versioned timetable changes for audit trail and comparison.
"""

from datetime import date, datetime, time
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VersionStatus(str, Enum):
    """Status of a timetable version."""
    DRAFT = "draft"
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class TimetableVersion(Base):
    """
    Represents a versioned snapshot of the timetable.
    
    Allows tracking of changes, comparison between versions,
    and audit trail of scheduling decisions.
    """

    __tablename__ = "timetable_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    status: Mapped[VersionStatus] = mapped_column(
        SQLEnum(VersionStatus),
        default=VersionStatus.DRAFT,
        nullable=False,
    )

    # Snapshot data - stores the full timetable state as JSON
    snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Change summary
    changes_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    events_added: Mapped[int] = mapped_column(Integer, default=0)
    events_modified: Mapped[int] = mapped_column(Integer, default=0)
    events_removed: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    approved_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])


class TimetableVersionEvent(Base):
    """
    Individual event stored within a timetable version.
    
    Allows querying specific events within a version.
    """

    __tablename__ = "timetable_version_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    version_id: Mapped[int] = mapped_column(
        ForeignKey("timetable_versions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Original event reference
    original_event_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Event data
    subject_id: Mapped[int] = mapped_column(Integer, nullable=False)
    faculty_id: Mapped[int] = mapped_column(Integer, nullable=False)
    batch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    room_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    event_date: Mapped[date] = mapped_column(nullable=False)
    start_time: Mapped[time] = mapped_column(nullable=False)
    end_time: Mapped[time] = mapped_column(nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1)

    # Change tracking
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)  # added, modified, removed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    version = relationship("TimetableVersion", backref="version_events")