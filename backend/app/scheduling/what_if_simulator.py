"""
What-if timetable simulation.

This module allows proposed changes or resource unavailability scenarios
to be evaluated without modifying the official timetable data.

Supported scenarios:

- ``room_unavailable``: A room cannot be used during a time window.
- ``faculty_unavailable``: A faculty member cannot teach during a time
  window.
- ``batch_unavailable``: A batch cannot attend classes during a time
  window.
- ``event_change``: A proposed change to a single event.

The simulation always operates on a deep copy of the timetable. The
official timetable is never modified.
"""

from copy import deepcopy

from .candidate_generator import evaluate_candidates, generate_slots
from .conflict_detector import detect_conflicts
from .constraint_engine import ConstraintEngine, _normalize_date, _slots_overlap
from .workload_optimizer import calculate_workload_impact


def simulate_event_change(events, event_id, changes):
    """
    Simulate changes to a timetable event without modifying the original data.

    Args:
        events: List of timetable event dictionaries.
        event_id: ID of the event to modify in the simulation.
        changes: Dictionary containing fields and values to change.

    Returns:
        Dictionary containing:
            - event_id: ID of the simulated event.
            - simulated_event: Updated event from the copied timetable.
            - conflicts: Conflicts detected after applying the changes.
            - has_conflict: True when at least one conflict exists.

    Raises:
        ValueError: If the requested event does not exist.

    Notes:
        The original events list is not modified.
    """
    simulated_events = deepcopy(events)

    target_event = None

    for event in simulated_events:
        if event["id"] == event_id:
            target_event = event
            break

    if target_event is None:
        raise ValueError(f"Event with id {event_id} was not found.")

    target_event.update(changes)

    conflicts = detect_conflicts(simulated_events)

    return {
        "event_id": event_id,
        "simulated_event": target_event,
        "conflicts": conflicts,
        "has_conflict": len(conflicts) > 0,
    }


def simulate_scenario(events, scenario, capacities=None, hard_capacities=None):
    """
    Evaluate a what-if scenario against a copy of the timetable.

    The scenario describes either a resource unavailability or a proposed
    event change. The result reports the affected events, the new
    conflicts, candidate replacements, and the workload impact. The
    official timetable is never modified.

    Args:
        events: List of timetable event dictionaries.
        scenario: Dictionary describing the scenario. See module docstring.
        capacities: Optional faculty workload capacities.
        hard_capacities: Optional absolute workload capacities.

    Returns:
        Dictionary containing:
            - scenario: The scenario that was evaluated.
            - affected_events: List of affected event dictionaries.
            - conflicts: Structured constraint violations introduced by
              the scenario.
            - has_conflict: True when the scenario introduces conflicts.
            - candidate_replacements: Mapping of affected event id to a
              list of evaluated candidate slots.
            - workload_impact: Workload impact for the affected events.
            - timetable_unchanged: Always True. The simulation never
              modifies the official timetable.

    Raises:
        ValueError: If the scenario type is not supported or the requested
            event does not exist.
    """
    scenario_type = scenario.get("type")

    if scenario_type == "event_change":
        return _simulate_event_change_scenario(
            events,
            scenario,
            capacities=capacities,
            hard_capacities=hard_capacities,
        )

    if scenario_type in {"room_unavailable", "faculty_unavailable", "batch_unavailable"}:
        return _simulate_unavailability_scenario(
            events,
            scenario,
            capacities=capacities,
            hard_capacities=hard_capacities,
        )

    raise ValueError(
        f"Unsupported scenario type: {scenario_type}. "
        "Expected one of: room_unavailable, faculty_unavailable, "
        "batch_unavailable, event_change."
    )


def _simulate_event_change_scenario(events, scenario, capacities, hard_capacities):
    """Simulate a proposed change to a single event."""
    event_id = scenario["event_id"]
    changes = scenario.get("changes", {})

    simulated_events = deepcopy(events)
    target_event = _find_event(simulated_events, event_id)
    target_event.update(changes)

    conflicts = [
        violation.to_dict()
        for violation in ConstraintEngine(
            capacities=capacities,
            hard_capacities=hard_capacities,
        ).evaluate(simulated_events)
    ]

    workload_impact = _workload_impact_for_event(
        events,
        target_event,
        capacities=capacities,
    )

    return {
        "scenario": scenario,
        "affected_events": [target_event],
        "conflicts": conflicts,
        "has_conflict": len(conflicts) > 0,
        "candidate_replacements": {},
        "workload_impact": [workload_impact],
        "timetable_unchanged": True,
    }


def _simulate_unavailability_scenario(events, scenario, capacities, hard_capacities):
    """Simulate a resource unavailability scenario."""
    scenario_type = scenario["type"]
    resource = scenario["resource"]
    window = {
        "date": _normalize_date(scenario["date"]),
        "start_time": scenario["start_time"] or "00:00",
        "end_time": scenario["end_time"] or "23:59",
    }

    affected_events = _find_affected_events(events, scenario_type, resource, window)

    blocker = {
        "id": -1,
        "subject_id": -1,
        "faculty_id": (
            resource if scenario_type == "faculty_unavailable" else -1
        ),
        "batch_id": (
            resource if scenario_type == "batch_unavailable" else -1
        ),
        "room_id": (
            str(resource) if scenario_type == "room_unavailable" else None
        ),
        "date": window["date"],
        "start_time": window["start_time"],
        "end_time": window["end_time"],
        "priority": 4,
    }

    simulated_events = deepcopy(events)
    simulated_events.append(blocker)

    conflicts = [
        violation.to_dict()
        for violation in ConstraintEngine(
            capacities=capacities,
            hard_capacities=hard_capacities,
        ).evaluate(simulated_events)
        if violation.event_id == -1 or violation.conflicting_event_id == -1
    ]

    candidate_replacements = {}
    workload_impact = []

    for event in affected_events:
        variants = _build_variants(events, event, scenario_type, resource)
        replacements = []

        for variant in variants:
            evaluated = _evaluate_variant_candidates(
                simulated_events,
                variant,
                window,
                capacities=capacities,
                hard_capacities=hard_capacities,
            )
            replacements.extend(evaluated)

        candidate_replacements[event["id"]] = replacements
        workload_impact.append(
            _workload_impact_for_event(
                events,
                event,
                capacities=capacities,
            )
        )

    return {
        "scenario": scenario,
        "affected_events": affected_events,
        "conflicts": conflicts,
        "has_conflict": len(conflicts) > 0,
        "candidate_replacements": candidate_replacements,
        "workload_impact": workload_impact,
        "timetable_unchanged": True,
    }


def _find_affected_events(events, scenario_type, resource, window):
    """Return events affected by a resource unavailability."""
    affected = []

    for event in events:
        if _normalize_date(event["date"]) != window["date"]:
            continue

        if not _slots_overlap(
            window["start_time"],
            window["end_time"],
            event["start_time"],
            event["end_time"],
        ):
            continue

        matches = False

        if scenario_type == "room_unavailable":
            matches = str(event.get("room_id")) == str(resource)
        elif scenario_type == "faculty_unavailable":
            matches = event["faculty_id"] == resource
        elif scenario_type == "batch_unavailable":
            matches = event["batch_id"] == resource

        if matches:
            affected.append(event)

    return affected


def _build_variants(events, event, scenario_type, resource):
    """
    Build event variants for candidate generation under unavailability.

    - room_unavailable: try every other room present in the timetable.
    - faculty_unavailable: try every other faculty present in the
      timetable.
    - batch_unavailable: keep the event unchanged (only the time can
      change).
    """
    if scenario_type == "room_unavailable":
        rooms = sorted(
            {
                str(e["room_id"])
                for e in events
                if e.get("room_id") is not None
            }
        )
        rooms = [r for r in rooms if r != str(resource)] or [None]

        return [
            {**event, "room_id": room} for room in rooms
        ]

    if scenario_type == "faculty_unavailable":
        faculty_ids = sorted({e["faculty_id"] for e in events})
        faculty_ids = [f for f in faculty_ids if f != resource]

        if not faculty_ids:
            return []

        return [
            {**event, "faculty_id": faculty_id}
            for faculty_id in faculty_ids
        ]

    return [event]


def _evaluate_variant_candidates(
    simulated_events,
    variant,
    window,
    capacities,
    hard_capacities,
):
    """
    Evaluate candidate time slots for a variant event.

    The unavailable window itself is excluded because the blocker pseudo
    event already rejects candidates that collide with it.
    """
    duration_minutes = _duration_minutes(variant)

    slots = generate_slots(
        dates=[_parse_date(window["date"])],
        slot_minutes=60,
        duration_minutes=duration_minutes,
    )

    return evaluate_candidates(
        simulated_events,
        variant,
        slots,
        capacities=capacities,
        hard_capacities=hard_capacities,
    )


def _workload_impact_for_event(events, event, capacities):
    """Calculate the workload impact of an event for its faculty."""
    return calculate_workload_impact(
        events,
        {
            "faculty_id": event["faculty_id"],
            "start_time": event["start_time"],
            "end_time": event["end_time"],
        },
        capacities=capacities,
    )


def _duration_minutes(event):
    """Return the duration of an event in minutes."""
    from .constraint_engine import _time_to_minutes

    return (
        _time_to_minutes(event["end_time"])
        - _time_to_minutes(event["start_time"])
    )


def _find_event(events, event_id):
    """Return the event with the given id or raise ValueError."""
    for event in events:
        if event["id"] == event_id:
            return event

    raise ValueError(f"Event with id {event_id} was not found.")


def _parse_date(value):
    """Parse a date object or YYYY-MM-DD string into a date object."""
    from datetime import date as _date

    if isinstance(value, _date):
        return value
    return _date.fromisoformat(str(value))