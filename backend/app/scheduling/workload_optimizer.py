"""
Faculty workload calculation module.

This module calculates the total allocated timetable hours for a
faculty member.

Current prototype scope:
- Calculate individual event duration.
- Sum durations for a selected faculty member.
- Reject invalid event time ranges.

This module does not currently perform workload balancing,
capacity management, or automatic optimization.
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


def calculate_event_duration(event):
    """
    Calculate the duration of a timetable event in hours.

    Args:
        event: Timetable event dictionary containing start_time and
            end_time.

    Returns:
        Event duration in hours as a float.

    Raises:
        ValueError: If the event's end time is earlier than or equal to
            its start time.
    """
    start = _time_to_minutes(event["start_time"])
    end = _time_to_minutes(event["end_time"])

    if end <= start:
        raise ValueError(
            f"Invalid time range for event {event['id']}: "
            f"{event['start_time']} - {event['end_time']}"
        )

    return (end - start) / 60


def calculate_faculty_workload(events, faculty_id):
    """
    Calculate total allocated timetable hours for a faculty member.

    Args:
        events: List of timetable event dictionaries.
        faculty_id: ID of the faculty member whose workload is calculated.

    Returns:
        Dictionary containing:
            - faculty_id: Requested faculty member ID.
            - allocated_hours: Total duration of matching events.

    Notes:
        Only events assigned to the specified faculty member are included.
        The function does not calculate maximum capacity, remaining
        capacity, or overloaded status.
    """
    total_hours = 0

    for event in events:
        if event["faculty_id"] == faculty_id:
            total_hours += calculate_event_duration(event)

    return {
        "faculty_id": faculty_id,
        "allocated_hours": total_hours,
    }