"""
Timetable conflict detection module.

This module detects overlapping timetable events that create conflicts
for shared scheduling resources:

- Faculty
- Batch
- Room

The conflict detector does not modify timetable events. It only analyzes
the provided events and returns a list of detected conflicts.
"""


def _time_to_minutes(time_string):
    """
    Convert a HH:MM time string into minutes since midnight.

    Args:
        time_string: Time value in HH:MM format.

    Returns:
        Integer number of minutes since midnight.
    """
    hours, minutes = map(int, time_string.split(":"))
    return hours * 60 + minutes


def _events_overlap(event1, event2):
    """
    Check whether two timetable events overlap on the same date.

    Events that end exactly when another event starts are considered
    non-overlapping.

    Args:
        event1: First timetable event.
        event2: Second timetable event.

    Returns:
        True if the events overlap, otherwise False.
    """
    if event1["date"] != event2["date"]:
        return False

    start1 = _time_to_minutes(event1["start_time"])
    end1 = _time_to_minutes(event1["end_time"])

    start2 = _time_to_minutes(event2["start_time"])
    end2 = _time_to_minutes(event2["end_time"])

    return start1 < end2 and start2 < end1


def detect_conflicts(events):
    """
    Detect faculty, batch, and room conflicts in timetable events.

    Two events are considered conflicting when they overlap in time
    and share the same faculty, batch, or room.

    Args:
        events: List of timetable event dictionaries.

    Returns:
        List of detected conflicts. Each conflict contains:
            - event_1: ID of the first event.
            - event_2: ID of the second event.
            - type: Conflict type (faculty, batch, or room).
            - reason: Human-readable explanation of the conflict.

    Notes:
        This function does not modify the input events.
    """
    conflicts = []

    for i in range(len(events)):
        for j in range(i + 1, len(events)):
            event1 = events[i]
            event2 = events[j]

            if not _events_overlap(event1, event2):
                continue

            if event1["faculty_id"] == event2["faculty_id"]:
                conflicts.append(
                    {
                        "event_1": event1["id"],
                        "event_2": event2["id"],
                        "type": "faculty",
                        "reason": (
                            f"Faculty {event1['faculty_id']} is assigned "
                            "to two overlapping classes."
                        ),
                    }
                )

            if event1["batch_id"] == event2["batch_id"]:
                conflicts.append(
                    {
                        "event_1": event1["id"],
                        "event_2": event2["id"],
                        "type": "batch",
                        "reason": (
                            f"Batch {event1['batch_id']} has "
                            "two overlapping classes."
                        ),
                    }
                )

            if event1["room_id"] == event2["room_id"]:
                conflicts.append(
                    {
                        "event_1": event1["id"],
                        "event_2": event2["id"],
                        "type": "room",
                        "reason": (
                            f"Room {event1['room_id']} is assigned "
                            "to two overlapping classes."
                        ),
                    }
                )

    return conflicts