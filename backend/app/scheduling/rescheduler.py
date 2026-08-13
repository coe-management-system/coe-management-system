"""
Basic timetable rescheduling support.

This module identifies candidate time slots that are available for a
faculty member, batch, and room.

The current prototype does not automatically move timetable events or
perform optimization. It evaluates proposed candidate slots and reports
whether they are feasible, including rejection reasons.
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


def _slots_overlap(start1, end1, start2, end2):
    """
    Check whether two time ranges overlap.

    Time ranges that touch at their boundary are considered
    non-overlapping.

    Args:
        start1: Start time of the first slot.
        end1: End time of the first slot.
        start2: Start time of the second slot.
        end2: End time of the second slot.

    Returns:
        True if the time ranges overlap, otherwise False.
    """
    start1 = _time_to_minutes(start1)
    end1 = _time_to_minutes(end1)
    start2 = _time_to_minutes(start2)
    end2 = _time_to_minutes(end2)

    return start1 < end2 and start2 < end1


def _get_slot_rejection_reasons(
    events,
    faculty_id,
    batch_id,
    room_id,
    date,
    start_time,
    end_time,
):
    """
    Determine why a proposed candidate slot is infeasible.

    Returns:
        List of human-readable rejection reasons.
    """
    reasons = []

    if _time_to_minutes(start_time) >= _time_to_minutes(end_time):
        reasons.append(
            "Candidate slot has an invalid time range."
        )

    for event in events:
        if event["date"] != date:
            continue

        if not _slots_overlap(
            start_time,
            end_time,
            event["start_time"],
            event["end_time"],
        ):
            continue

        if event["faculty_id"] == faculty_id:
            reasons.append(
                f"Faculty {faculty_id} is unavailable due to "
                f"event {event['id']}."
            )

        if event["batch_id"] == batch_id:
            reasons.append(
                f"Batch {batch_id} is unavailable due to "
                f"event {event['id']}."
            )

        if event["room_id"] == room_id:
            reasons.append(
                f"Room {room_id} is unavailable due to "
                f"event {event['id']}."
            )

    return reasons


def _slot_is_available(
    events,
    faculty_id,
    batch_id,
    room_id,
    date,
    start_time,
    end_time,
):
    """
    Check whether a proposed slot is available.

    A slot is unavailable when an overlapping event uses the same:
    - Faculty
    - Batch
    - Room

    Args:
        events: Existing timetable events.
        faculty_id: Faculty assigned to the proposed slot.
        batch_id: Batch assigned to the proposed slot.
        room_id: Room assigned to the proposed slot.
        date: Proposed slot date.
        start_time: Proposed slot start time.
        end_time: Proposed slot end time.

    Returns:
        True if the slot is available for all required resources,
        otherwise False.
    """
    return not _get_slot_rejection_reasons(
        events=events,
        faculty_id=faculty_id,
        batch_id=batch_id,
        room_id=room_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
    )


def find_available_slots(
    events,
    faculty_id,
    batch_id,
    room_id,
    candidate_slots,
):
    """
    Find candidate slots where all required resources are available.

    Args:
        events: Existing timetable events.
        faculty_id: Faculty assigned to the class.
        batch_id: Batch assigned to the class.
        room_id: Room assigned to the class.
        candidate_slots: List of proposed time slots. Each slot should
            contain date, start_time, and end_time.

    Returns:
        List containing only the candidate slots that do not conflict
        with the existing timetable.

    Notes:
        This function does not modify existing events. It only evaluates
        candidate slots.
    """
    available_slots = []

    for slot in candidate_slots:
        if _slot_is_available(
            events=events,
            faculty_id=faculty_id,
            batch_id=batch_id,
            room_id=room_id,
            date=slot["date"],
            start_time=slot["start_time"],
            end_time=slot["end_time"],
        ):
            available_slots.append(slot)

    return available_slots


def evaluate_candidate_slots(
    events,
    faculty_id,
    batch_id,
    room_id,
    candidate_slots,
):
    """
    Evaluate candidate slots and explain whether each is feasible.

    Returns:
        List of dictionaries containing:
            - date
            - start_time
            - end_time
            - status
            - reasons

        Status is either:
            "feasible"
            "rejected"
    """
    results = []

    for slot in candidate_slots:
        reasons = _get_slot_rejection_reasons(
            events=events,
            faculty_id=faculty_id,
            batch_id=batch_id,
            room_id=room_id,
            date=slot["date"],
            start_time=slot["start_time"],
            end_time=slot["end_time"],
        )

        results.append(
            {
                "date": slot["date"],
                "start_time": slot["start_time"],
                "end_time": slot["end_time"],
                "status": "feasible" if not reasons else "rejected",
                "reasons": reasons,
            }
        )

    return results