"""
Scheduling domain representations.

This module defines lightweight representations used by the scheduling
engine. The scheduling layer remains independent of SQLAlchemy.
"""

from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class SchedulingEvent:
    """
    Engine-level representation of a timetable event.
    """

    id: int
    subject_id: int
    faculty_id: int
    batch_id: int
    room_id: str | None
    date: date
    start_time: str
    end_time: str
    priority: int
<<<<<<< HEAD
    group_id: int | None = None
=======
>>>>>>> origin/develop

    @classmethod
    def from_timetable_data(
        cls,
        *,
        id: int,
        subject_id: int,
        faculty_id: int,
        batch_id: int,
        room_id: str | None,
        event_date: date,
        start_time: time,
        end_time: time,
        priority: int,
<<<<<<< HEAD
        group_id: int | None = None,
=======
>>>>>>> origin/develop
    ) -> "SchedulingEvent":
        """
        Convert timetable model data into a scheduling event.

        This method accepts values from the application's timetable model
        without importing or depending on SQLAlchemy.
        """

        return cls(
            id=id,
            subject_id=subject_id,
            faculty_id=faculty_id,
            batch_id=batch_id,
            room_id=room_id,
            date=event_date,
            start_time=start_time.strftime("%H:%M"),
            end_time=end_time.strftime("%H:%M"),
            priority=priority,
<<<<<<< HEAD
            group_id=group_id,
=======
>>>>>>> origin/develop
        )

    def to_dict(self) -> dict:
        """
        Convert the domain event to the structure used by the Day 1
        scheduling modules.
        """

        return {
            "id": self.id,
            "subject_id": self.subject_id,
            "faculty_id": self.faculty_id,
            "batch_id": self.batch_id,
            "room_id": self.room_id,
            "date": self.date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "priority": self.priority,
<<<<<<< HEAD
            "group_id": self.group_id,
=======
>>>>>>> origin/develop
        }