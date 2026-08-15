"""
Deterministic schedule objective for optimization.

The objective ranks complete schedules. It is deliberately separate from
the hard constraint system: a hard violation always rejects a candidate
before any scoring happens (see optimizer.py). The objective only ranks
feasible schedules.

Documented weights
------------------

The weights below are the single documented source for the baseline
optimizer. Where a penalty already exists in the candidate scoring
(``scoring.py``) the same value is reused so the two layers agree:

- ``HARD_CONFLICT_PENALTY``    500.0  per hard violation. Feasible
  schedules have zero hard violations, so this is effectively a guard.
- ``WORKLOAD_OVERLOAD_PENALTY`` 40.0  per overloaded faculty member.
  Matches ``scoring.WORKLOAD_OVERLOAD_PENALTY``.
- ``WORKLOAD_BALANCE_PENALTY``   5.0  per squared-hour deviation of a
  faculty member's workload from their capacity. Favours distributing
  hours evenly across faculty rather than overloading a few.
- ``MOVED_EVENTS_PENALTY``      25.0  per moved event. Matches
  ``scoring.MOVED_EVENTS_PENALTY``.
- ``PRIORITY_MOVE_PENALTY``     10.0  per priority level of a moved
  event. Matches ``scoring.PRIORITY_PENALTY``. Moving high-priority
  events is more expensive than moving normal ones.
- ``ROOM_UTILIZATION_PENALTY``   2.0  per squared-hour deviation of a
  room's usage from the mean room usage. Favours spreading load across
  rooms.

Future optimizers (OR-Tools, genetic, ...) may use their own objective
but must document their weights in the same way.
"""

from .constraint_engine import ConstraintEngine, HARD
from .priorities import get_priority_value
from .workload_optimizer import calculate_event_duration, calculate_workload_report

BASE_SCORE = 1000.0

HARD_CONFLICT_PENALTY = 500.0
WORKLOAD_OVERLOAD_PENALTY = 40.0
WORKLOAD_BALANCE_PENALTY = 5.0
MOVED_EVENTS_PENALTY = 25.0
PRIORITY_MOVE_PENALTY = 10.0
ROOM_UTILIZATION_PENALTY = 2.0

MODE_BALANCED = "BALANCED"
MODE_CONFLICT_MINIMIZATION = "CONFLICT_MINIMIZATION"
MODE_WORKLOAD_BALANCING = "WORKLOAD_BALANCING"

SUPPORTED_MODES = {
    MODE_BALANCED,
    MODE_CONFLICT_MINIMIZATION,
    MODE_WORKLOAD_BALANCING,
}

_MODE_WEIGHT_MULTIPLIERS = {
    MODE_BALANCED: {
        "conflict": 1.0,
        "workload_overload": 1.0,
        "workload_balance": 1.0,
        "moved": 1.0,
        "priority": 1.0,
        "room": 1.0,
    },
    MODE_CONFLICT_MINIMIZATION: {
        "conflict": 2.0,
        "workload_overload": 0.5,
        "workload_balance": 0.5,
        "moved": 0.5,
        "priority": 0.5,
        "room": 0.5,
    },
    MODE_WORKLOAD_BALANCING: {
        "conflict": 1.0,
        "workload_overload": 2.0,
        "workload_balance": 2.0,
        "moved": 0.5,
        "priority": 0.5,
        "room": 0.5,
    },
}


def _event_hours(event) -> float:
    """Return the duration of an event in hours."""
    return calculate_event_duration(event)


def count_hard_conflicts(events, capacities=None, hard_capacities=None) -> int:
    """
    Count hard constraint violations in a schedule.

    Args:
        events: List of timetable event dictionaries.
        capacities: Optional faculty workload capacities.
        hard_capacities: Optional absolute workload capacities.

    Returns:
        Number of hard violations in the schedule.
    """
    violations = ConstraintEngine(
        capacities=capacities,
        hard_capacities=hard_capacities,
    ).evaluate(events)

    return sum(1 for v in violations if v.severity == HARD)


def workload_balance_penalty(events, capacities=None, mode=MODE_BALANCED) -> float:
    """
    Penalty for uneven faculty workload distribution.

    For every faculty member with a configured capacity the squared
    deviation between allocated hours and capacity is penalised. This
    makes a schedule that overloads one faculty member and underloads
    another worse than a schedule that spreads the hours evenly.

    Args:
        events: List of timetable event dictionaries.
        capacities: Optional mapping of faculty_id to max hours.
        mode: Optimization mode controlling the weight.

    Returns:
        Total workload-balance penalty.
    """
    if not capacities:
        return 0.0

    multiplier = _MODE_WEIGHT_MULTIPLIERS[mode]["workload_balance"]

    penalty = 0.0
    for entry in calculate_workload_report(events, capacities):
        faculty_id = entry["faculty_id"]
        capacity = capacities.get(faculty_id)
        if capacity is None:
            continue
        deviation = entry["allocated_hours"] - capacity
        penalty += deviation * deviation * WORKLOAD_BALANCE_PENALTY

    return round(penalty * multiplier, 4)


def workload_overload_penalty(events, capacities=None, mode=MODE_BALANCED) -> float:
    """
    Penalty for faculty members whose workload exceeds their capacity.

    Args:
        events: List of timetable event dictionaries.
        capacities: Optional mapping of faculty_id to max hours.
        mode: Optimization mode controlling the weight.

    Returns:
        Total overload penalty.
    """
    if not capacities:
        return 0.0

    multiplier = _MODE_WEIGHT_MULTIPLIERS[mode]["workload_overload"]

    overloaded = 0
    for entry in calculate_workload_report(events, capacities):
        if entry["status"] == "overloaded":
            overloaded += 1

    return round(overloaded * WORKLOAD_OVERLOAD_PENALTY * multiplier, 4)


def room_utilization_penalty(events, mode=MODE_BALANCED) -> float:
    """
    Penalty for uneven room usage across the timetable.

    The total scheduled hours per room are compared against the mean;
    squared deviations are penalised. Rooms with no scheduled events are
    ignored.

    Args:
        events: List of timetable event dictionaries.
        mode: Optimization mode controlling the weight.

    Returns:
        Total room-utilization penalty.
    """
    room_hours = {}
    for event in events:
        room_id = event.get("room_id")
        if room_id is None:
            continue
        room_hours.setdefault(room_id, 0.0)
        room_hours[room_id] += _event_hours(event)

    if not room_hours:
        return 0.0

    mean = sum(room_hours.values()) / len(room_hours)
    penalty = sum(
        (hours - mean) * (hours - mean) for hours in room_hours.values()
    )

    multiplier = _MODE_WEIGHT_MULTIPLIERS[mode]["room"]
    return round(penalty * ROOM_UTILIZATION_PENALTY * multiplier, 4)


def moved_events_penalty(moved_event_ids, events, mode=MODE_BALANCED) -> tuple[float, float]:
    """
    Penalty for moving events, weighted by event priority.

    Args:
        moved_event_ids: Iterable of event ids that were moved.
        events: The original timetable event dictionaries used to look up
            priorities.
        mode: Optimization mode controlling the weight.

    Returns:
        Tuple of (movement_penalty, priority_penalty).
    """
    multiplier = _MODE_WEIGHT_MULTIPLIERS[mode]["moved"]
    priority_multiplier = _MODE_WEIGHT_MULTIPLIERS[mode]["priority"]

    events_by_id = {event["id"]: event for event in events}

    movement = 0
    priority = 0.0

    for event_id in sorted(set(moved_event_ids)):
        movement += 1
        event = events_by_id.get(event_id)
        if event is None:
            continue
        priority_value = get_priority_value(event.get("priority", 2))
        priority += priority_value * PRIORITY_MOVE_PENALTY

    return (
        round(movement * MOVED_EVENTS_PENALTY * multiplier, 4),
        round(priority * priority_multiplier, 4),
    )


def evaluate_objective(
    events,
    capacities=None,
    moved_event_ids=None,
    original_events=None,
    mode=MODE_BALANCED,
    hard_capacities=None,
) -> dict:
    """
    Evaluate the objective score of a complete schedule.

    Args:
        events: The schedule to score.
        capacities: Optional faculty workload capacities.
        moved_event_ids: Optional iterable of event ids that were moved
            relative to the original timetable.
        original_events: The original timetable used for priority lookup
            of moved events. Defaults to ``events``.
        mode: Optimization mode. One of ``objective.SUPPORTED_MODES``.
        hard_capacities: Optional absolute workload capacities used when
            counting conflicts.

    Returns:
        Dictionary containing:
            - score: Higher is better.
            - penalty: Lower is better.
            - conflicts: Number of hard violations.
            - breakdown: Per-factor penalty breakdown.
    """
    if mode not in SUPPORTED_MODES:
        raise ValueError(
            f"Unsupported optimization mode: {mode}. "
            f"Expected one of: {', '.join(sorted(SUPPORTED_MODES))}"
        )

    conflicts = count_hard_conflicts(
        events,
        capacities=capacities,
        hard_capacities=hard_capacities,
    )

    breakdown = {}
    penalty = 0.0

    if conflicts:
        conflict_penalty = conflicts * HARD_CONFLICT_PENALTY * _MODE_WEIGHT_MULTIPLIERS[mode]["conflict"]
        breakdown["conflicts"] = round(conflict_penalty, 4)
        penalty += conflict_penalty

    overload = workload_overload_penalty(events, capacities, mode)
    if overload:
        breakdown["workload_overload"] = overload
        penalty += overload

    balance = workload_balance_penalty(events, capacities, mode)
    if balance:
        breakdown["workload_balance"] = balance
        penalty += balance

    room = room_utilization_penalty(events, mode)
    if room:
        breakdown["room_utilization"] = room
        penalty += room

    if moved_event_ids:
        lookup = original_events if original_events is not None else events
        movement, priority = moved_events_penalty(moved_event_ids, lookup, mode)
        if movement:
            breakdown["moved_events"] = movement
            penalty += movement
        if priority:
            breakdown["priority"] = priority
            penalty += priority

    penalty = round(penalty, 4)
    score = round(BASE_SCORE - penalty, 4)

    return {
        "score": score,
        "penalty": penalty,
        "conflicts": conflicts,
        "breakdown": breakdown,
    }


def workload_summary(events, capacities=None) -> dict:
    """
    Summarize the workload distribution of a schedule.

    Args:
        events: List of timetable event dictionaries.
        capacities: Optional mapping of faculty_id to max hours.

    Returns:
        Dictionary with total_hours, overloaded, at_capacity, and
        faculty entries.
    """
    report = calculate_workload_report(events, capacities)

    return {
        "total_hours": round(
            sum(entry["allocated_hours"] for entry in report),
            4,
        ),
        "faculty": report,
    }
