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


def calculate_workload_impact(
    events,
    candidate,
    capacities=None,
    exclude_event_id=None,
):
    """
    Evaluate the workload impact of a proposed candidate change.

    The impact is the projected workload for the candidate's faculty after
    applying the candidate, compared against the faculty's capacity.

    Args:
        events: List of timetable event dictionaries.
        candidate: Candidate dictionary containing faculty_id, start_time,
            and end_time.
        capacities: Optional mapping of faculty_id to max hours. When the
            faculty is absent (or capacities is None), capacity fields are
            reported as None.
        exclude_event_id: Optional event id to exclude from the current
            workload. Used when the candidate moves an existing event.

    Returns:
        Dictionary containing:
            - faculty_id
            - current_hours: Hours currently allocated.
            - candidate_hours: Hours the candidate would add.
            - projected_hours: Projected hours after the candidate.
            - capacity: Maximum hours for the faculty, or None.
            - overload: Projected hours minus capacity, or None.
            - status: "optimal", "at_capacity", or "overloaded" when a
              capacity is known, otherwise "unknown".
    """
    faculty_id = candidate["faculty_id"]

    current_hours = 0.0
    for event in events:
        if event["faculty_id"] != faculty_id:
            continue
        if exclude_event_id is not None and event["id"] == exclude_event_id:
            continue
        current_hours += calculate_event_duration(event)

    candidate_hours = calculate_event_duration(candidate)
    projected_hours = current_hours + candidate_hours

    capacity = (capacities or {}).get(faculty_id)

    if capacity is None:
        return {
            "faculty_id": faculty_id,
            "current_hours": current_hours,
            "candidate_hours": candidate_hours,
            "projected_hours": projected_hours,
            "capacity": None,
            "overload": None,
            "status": "unknown",
        }

    overload = projected_hours - capacity

    if projected_hours > capacity:
        status = "overloaded"
    elif projected_hours == capacity:
        status = "at_capacity"
    else:
        status = "optimal"

    return {
        "faculty_id": faculty_id,
        "current_hours": current_hours,
        "candidate_hours": candidate_hours,
        "projected_hours": projected_hours,
        "capacity": capacity,
        "overload": overload,
        "status": status,
    }


def calculate_workload_report(events, capacities=None):
    """
    Calculate a workload report for every faculty member in the timetable.

    Args:
        events: List of timetable event dictionaries.
        capacities: Optional mapping of faculty_id to max hours.

    Returns:
        List of workload dictionaries, one per faculty member. Each entry
        contains faculty_id, allocated_hours, capacity, overload, and
        status.
    """
    faculty_ids = sorted({event["faculty_id"] for event in events})

    report = []

    for faculty_id in faculty_ids:
        allocated = calculate_faculty_workload(events, faculty_id)[
            "allocated_hours"
        ]
        capacity = (capacities or {}).get(faculty_id)

        if capacity is None:
            report.append(
                {
                    "faculty_id": faculty_id,
                    "allocated_hours": allocated,
                    "capacity": None,
                    "overload": None,
                    "status": "unknown",
                }
            )
            continue

        overload = allocated - capacity

        if allocated > capacity:
            status = "overloaded"
        elif allocated == capacity:
            status = "at_capacity"
        else:
            status = "optimal"

        report.append(
            {
                "faculty_id": faculty_id,
                "allocated_hours": allocated,
                "capacity": capacity,
                "overload": overload,
                "status": status,
            }
        )

    return report