"""
Constraint-aware candidate slot generation.

This module generates alternative time slots for a timetable event and
evaluates every candidate through the constraint engine. A candidate is
only marked feasible after it passes:

- Faculty availability
- Batch/group availability
- Room availability
- Time validity
- Workload constraints

A candidate is never assumed to be valid simply because it "looks free".
Every candidate must survive the full set of applicable constraints.
"""

from datetime import date, timedelta

from .constraint_engine import (
    ConstraintEngine,
    HARD,
    _normalize_date,
    _time_to_minutes,
)


def build_candidate(event: dict, slot: dict) -> dict:
    """
    Combine an event's resource identity with a proposed slot.

    Args:
        event: The event being rescheduled. Supplies faculty, batch, group,
            room, priority, and id.
        slot: Proposed slot containing date, start_time, and end_time.

    Returns:
        A candidate dictionary suitable for constraint evaluation.
    """
    return {
        "event_id": event["id"],
        "faculty_id": event["faculty_id"],
        "batch_id": event["batch_id"],
        "group_id": event.get("group_id"),
        "room_id": event.get("room_id"),
        "priority": event.get("priority", 2),
        "date": slot["date"],
        "start_time": slot["start_time"],
        "end_time": slot["end_time"],
    }


def generate_slots(
    dates: list,
    day_start: str = "08:00",
    day_end: str = "18:00",
    slot_minutes: int = 60,
    duration_minutes: int = 60,
) -> list[dict]:
    """
    Generate candidate time slots across a set of dates.

    Slots are generated between day_start and day_end using a fixed
    step and duration. Generation is deterministic.

    Args:
        dates: List of dates to generate slots for.
        day_start: Earliest start time, in HH:MM format.
        day_end: Latest allowed end time, in HH:MM format.
        slot_minutes: Step between slot starts, in minutes.
        duration_minutes: Duration of each slot, in minutes.

    Returns:
        List of slot dictionaries containing date, start_time, and
        end_time.
    """
    start_minutes = _time_to_minutes(day_start)
    end_minutes = _time_to_minutes(day_end)

    slots = []

    for day in dates:
        start = start_minutes

        while start + duration_minutes <= end_minutes:
            end = start + duration_minutes

            start_time = f"{start // 60:02d}:{start % 60:02d}"
            end_time = f"{end // 60:02d}:{end % 60:02d}"

            slots.append(
                {
                    "date": _normalize_date(day),
                    "start_time": start_time,
                    "end_time": end_time,
                }
            )

            start += slot_minutes

    return slots


def evaluate_candidates(
    events: list[dict],
    event: dict,
    candidates: list[dict],
    capacities: dict[int, float] | None = None,
    hard_capacities: dict[int, float] | None = None,
) -> list[dict]:
    """
    Evaluate candidate slots through the constraint engine.

    Args:
        events: Existing timetable events.
        event: The event being rescheduled.
        candidates: List of proposed slots (date, start_time, end_time).
        capacities: Optional faculty workload capacities.
        hard_capacities: Optional absolute workload capacities.

    Returns:
        List of candidate evaluation dictionaries containing date,
        start_time, end_time, status ("FEASIBLE" or "REJECTED"), reasons,
        and violations.
    """
    engine = ConstraintEngine(
        capacities=capacities,
        hard_capacities=hard_capacities,
    )

    results = []

    for slot in candidates:
        candidate = build_candidate(event, slot)
        violations = engine.evaluate_candidate(events, candidate)

        hard_violations = [v for v in violations if v.severity == HARD]

        feasible = not hard_violations
        reasons = [v.message for v in hard_violations]

        results.append(
            {
                "date": slot["date"],
                "start_time": slot["start_time"],
                "end_time": slot["end_time"],
                "status": "FEASIBLE" if feasible else "REJECTED",
                "reasons": reasons,
                "violations": [v.to_dict() for v in violations],
            }
        )

    return results


def generate_candidates(
    events: list[dict],
    event: dict,
    dates: list | None = None,
    day_start: str = "08:00",
    day_end: str = "18:00",
    slot_minutes: int = 60,
    duration_minutes: int | None = None,
    capacities: dict[int, float] | None = None,
    hard_capacities: dict[int, float] | None = None,
) -> list[dict]:
    """
    Generate and evaluate candidate slots for an event.

    When no dates are provided, a single default date is used (the
    event's current date is excluded so alternatives are distinct).

    Args:
        events: Existing timetable events.
        event: The event being rescheduled.
        dates: Optional list of dates to consider. Defaults to the next
            five weekdays after the event's current date.
        day_start: Earliest slot start time.
        day_end: Latest allowed slot end time.
        slot_minutes: Step between slot starts.
        duration_minutes: Slot duration. Defaults to the event's duration.
        capacities: Optional faculty workload capacities.
        hard_capacities: Optional absolute workload capacities.

    Returns:
        List of evaluated candidate dictionaries.
    """
    if duration_minutes is None:
        duration_minutes = _duration_of_event(event)

    if dates is None:
        dates = _default_dates(event)

    slots = generate_slots(
        dates=dates,
        day_start=day_start,
        day_end=day_end,
        slot_minutes=slot_minutes,
        duration_minutes=duration_minutes,
    )

    return evaluate_candidates(
        events=events,
        event=event,
        candidates=slots,
        capacities=capacities,
        hard_capacities=hard_capacities,
    )


def _duration_of_event(event: dict) -> int:
    """Return the duration of an event in minutes."""
    start = _time_to_minutes(event["start_time"])
    end = _time_to_minutes(event["end_time"])
    return end - start


def _default_dates(event: dict) -> list[date]:
    """
    Return a deterministic set of alternative dates for an event.

    Uses the five weekdays following the event's current date.
    """
    current = _parse_date(event["date"])

    dates = []
    day = current + timedelta(days=1)
    while len(dates) < 5:
        if day.weekday() < 5:
            dates.append(day)
        day += timedelta(days=1)

    return dates


def _parse_date(value) -> date:
    """Parse a date object or YYYY-MM-DD string into a date object."""
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))