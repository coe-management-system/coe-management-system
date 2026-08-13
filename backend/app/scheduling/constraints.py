"""
Scheduling constraint validation module.

This module provides basic validation for timetable events and proposed
time slots.

The current prototype validates:
- Required timetable event fields
- Start and end time ordering
- Supported priority values
- Basic time-slot validity

These constraints are intentionally simple and can be extended as the
scheduling engine becomes more sophisticated.
"""


def validate_event(event):
    """
    Validate the basic structure of a timetable event.

    Args:
        event: Timetable event dictionary containing scheduling data.

    Returns:
        List of validation error messages.
        An empty list means the event is valid.

    Required fields:
        id
        subject_id
        faculty_id
        batch_id
        room_id
        date
        start_time
        end_time
        priority
    """
    required_fields = [
        "id",
        "subject_id",
        "faculty_id",
        "batch_id",
        "room_id",
        "date",
        "start_time",
        "end_time",
        "priority",
    ]

    errors = []

    for field in required_fields:
        if field not in event:
            errors.append(f"Missing required field: {field}")

    if errors:
        return errors

    if event["start_time"] >= event["end_time"]:
        errors.append("start_time must be earlier than end_time")

    valid_priorities = {"low", "normal", "high", "urgent"}

    if event["priority"] not in valid_priorities:
        errors.append(
            f"Invalid priority: {event['priority']}"
        )

    return errors


def is_slot_valid(start_time, end_time):
    """
    Check whether a proposed time slot has a valid time range.

    Args:
        start_time: Slot start time in HH:MM format.
        end_time: Slot end time in HH:MM format.

    Returns:
        True if start_time is earlier than end_time,
        otherwise False.
    """
    return start_time < end_time