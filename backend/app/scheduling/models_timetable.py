"""
Bridge between the timetable database model and the scheduling engine.

This module loads the application's real TimetableEvent model rows into
scheduling domain events. It keeps the scheduling engine independent of
SQLAlchemy while allowing the service to operate on real database data.
"""

from sqlalchemy import select

from .domain import SchedulingEvent


def load_timetable_events(db):
    """
    Load all timetable events from the database as scheduling events.

    Args:
        db: SQLAlchemy session.

    Returns:
        List of SchedulingEvent objects.
    """
    from app.models.timetable import TimetableEvent

    rows = db.scalars(select(TimetableEvent)).all()

    return [
        SchedulingEvent.from_timetable_data(
            id=row.id,
            subject_id=row.subject_id,
            faculty_id=row.faculty_id,
            batch_id=row.batch_id,
            room_id=row.room_id,
            event_date=row.event_date,
            start_time=row.start_time,
            end_time=row.end_time,
            priority=row.priority,
        )
        for row in rows
    ]