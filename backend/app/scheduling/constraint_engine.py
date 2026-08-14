"""
First-class constraint system for scheduling.

This module turns scheduling rules into independently testable constraints.
The constraint engine is the single place where scheduling rules live:

- Faculty constraint (hard): a faculty member cannot teach two events that
  overlap in time.
- Batch/group constraint (hard): a batch or group cannot attend two events
  that overlap in time.
- Room constraint (hard): the same room cannot hold two overlapping events.
- Time constraint (hard): an event cannot have an end time earlier than or
  equal to its start time.
- Workload constraint (soft/hard): moving an event that pushes a faculty
  member beyond their capacity is penalised (soft) or rejected (hard)
  depending on the configured capacity limits.

Every constraint produces structured :class:`ConstraintViolation` objects
that explain what failed, why, and which resources are involved. This makes
the engine explainable and ready for the later optimization work.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any


HARD = "hard"
SOFT = "soft"

FACULTY_CONSTRAINT = "faculty"
BATCH_CONSTRAINT = "batch"
GROUP_CONSTRAINT = "group"
ROOM_CONSTRAINT = "room"
TIME_CONSTRAINT = "time"
WORKLOAD_CONSTRAINT = "workload"

HARD_CONSTRAINT_TYPES = {
    FACULTY_CONSTRAINT,
    BATCH_CONSTRAINT,
    GROUP_CONSTRAINT,
    ROOM_CONSTRAINT,
    TIME_CONSTRAINT,
}

SOFT_CONSTRAINT_TYPES = {WORKLOAD_CONSTRAINT}


@dataclass(frozen=True)
class ConstraintViolation:
    """
    Structured explanation of a constraint failure.

    Attributes:
        constraint_type: Type of the violated constraint such as faculty,
            batch, group, room, time, or workload.
        severity: Whether the constraint is hard or soft.
        event_id: ID of the event being evaluated.
        conflicting_event_id: ID of the other event involved, when the
            violation is a pairwise conflict. Otherwise None.
        resource: The shared resource involved (faculty/batch/group/room id,
            or time range). Otherwise None.
        message: Human-readable explanation of the violation.
    """

    constraint_type: str
    severity: str
    event_id: int
    conflicting_event_id: int | None = None
    resource: Any = None
    message: str = ""

    def to_dict(self) -> dict:
        """Return the violation as a serializable dictionary."""
        return {
            "constraint_type": self.constraint_type,
            "severity": self.severity,
            "event_id": self.event_id,
            "conflicting_event_id": self.conflicting_event_id,
            "resource": self.resource,
            "message": self.message,
        }


def _time_to_minutes(time_string) -> int:
    """
    Convert a HH:MM time string into minutes since midnight.

    Args:
        time_string: Time value in HH:MM format.

    Returns:
        Integer number of minutes since midnight.
    """
    hours, minutes = map(int, time_string.split(":"))
    return hours * 60 + minutes


def _normalize_date(value) -> str:
    """
    Normalize a date object or date string into an ISO date string.

    Args:
        value: A date object or a YYYY-MM-DD string.

    Returns:
        The date as a YYYY-MM-DD string.
    """
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _slots_overlap(start1, end1, start2, end2) -> bool:
    """
    Check whether two time ranges overlap.

    Time ranges that touch at their boundary are considered non-overlapping.

    Args:
        start1: Start time of the first slot.
        end1: End time of the first slot.
        start2: Start time of the second slot.
        end2: End time of the second slot.

    Returns:
        True if the time ranges overlap, otherwise False.
    """
    return (
        _time_to_minutes(start1) < _time_to_minutes(end2)
        and _time_to_minutes(start2) < _time_to_minutes(end1)
    )


def _events_overlap(event1: dict, event2: dict) -> bool:
    """
    Check whether two events overlap on the same date and time.

    Args:
        event1: First event dictionary.
        event2: Second event dictionary.

    Returns:
        True if the events overlap, otherwise False.
    """
    if _normalize_date(event1["date"]) != _normalize_date(event2["date"]):
        return False

    return _slots_overlap(
        event1["start_time"],
        event1["end_time"],
        event2["start_time"],
        event2["end_time"],
    )


def _event_duration_hours(start_time: str, end_time: str) -> float:
    """
    Calculate the duration of a time range in hours.

    Args:
        start_time: Slot start time in HH:MM format.
        end_time: Slot end time in HH:MM format.

    Returns:
        Duration in hours.

    Raises:
        ValueError: If the end time is earlier than or equal to the start time.
    """
    start = _time_to_minutes(start_time)
    end = _time_to_minutes(end_time)

    if end <= start:
        raise ValueError(
            f"Invalid time range: {start_time} - {end_time}"
        )

    return (end - start) / 60


def _event_identifier(event: dict) -> int:
    """
    Return the event id from a dictionary that may use id or event_id.

    Args:
        event: Event or candidate dictionary.

    Returns:
        The event identifier, or -1 when it cannot be determined.
    """
    return event.get("id") or event.get("event_id") or -1


def check_time_constraint(event: dict) -> list[ConstraintViolation]:
    """
    Check that an event has a valid time range.

    Args:
        event: Event dictionary containing start_time and end_time.

    Returns:
        List of violations. Empty when the event time is valid.
    """
    if event["start_time"] >= event["end_time"]:
        return [
            ConstraintViolation(
                constraint_type=TIME_CONSTRAINT,
                severity=HARD,
                event_id=_event_identifier(event),
                resource=f"{event['start_time']} - {event['end_time']}",
                message=(
                    f"Event {_event_identifier(event)} has an invalid time range: "
                    f"{event['start_time']} - {event['end_time']} "
                    "(end must be later than start)."
                ),
            )
        ]

    return []


def check_resource_conflicts(event1: dict, event2: dict) -> list[ConstraintViolation]:
    """
    Check pairwise resource conflicts between two overlapping events.

    Args:
        event1: First event dictionary.
        event2: Second event dictionary.

    Returns:
        List of faculty, batch, group, and room violations between the
        two events. Empty when the events do not share a conflicting
        resource.
    """
    violations = []

    if not _events_overlap(event1, event2):
        return violations

    if event1["faculty_id"] == event2["faculty_id"]:
        violations.append(
            ConstraintViolation(
                constraint_type=FACULTY_CONSTRAINT,
                severity=HARD,
                event_id=event1["id"],
                conflicting_event_id=event2["id"],
                resource=event1["faculty_id"],
                message=(
                    f"Faculty {event1['faculty_id']} is assigned to two "
                    f"overlapping events ({event1['id']} and {event2['id']})."
                ),
            )
        )

    if event1["batch_id"] == event2["batch_id"]:
        violations.append(
            ConstraintViolation(
                constraint_type=BATCH_CONSTRAINT,
                severity=HARD,
                event_id=event1["id"],
                conflicting_event_id=event2["id"],
                resource=event1["batch_id"],
                message=(
                    f"Batch {event1['batch_id']} is assigned to two "
                    f"overlapping events ({event1['id']} and {event2['id']})."
                ),
            )
        )

    group_1 = event1.get("group_id")
    group_2 = event2.get("group_id")

    if group_1 is not None and group_1 == group_2:
        violations.append(
            ConstraintViolation(
                constraint_type=GROUP_CONSTRAINT,
                severity=HARD,
                event_id=event1["id"],
                conflicting_event_id=event2["id"],
                resource=group_1,
                message=(
                    f"Group {group_1} is assigned to two overlapping "
                    f"events ({event1['id']} and {event2['id']})."
                ),
            )
        )

    room_1 = event1.get("room_id")
    room_2 = event2.get("room_id")

    if room_1 is not None and room_1 == room_2:
        violations.append(
            ConstraintViolation(
                constraint_type=ROOM_CONSTRAINT,
                severity=HARD,
                event_id=event1["id"],
                conflicting_event_id=event2["id"],
                resource=room_1,
                message=(
                    f"Room {room_1} is assigned to two overlapping "
                    f"events ({event1['id']} and {event2['id']})."
                ),
            )
        )

    return violations


def check_workload_constraint(
    events: list[dict],
    candidate: dict,
    capacities: dict[int, float] | None = None,
    hard_capacities: dict[int, float] | None = None,
) -> list[ConstraintViolation]:
    """
    Check the workload impact of placing an event at a candidate slot.

    The projected workload for the candidate's faculty is the current
    workload (excluding the event being moved, if any) plus the candidate
    duration.

    - When the projected workload exceeds the hard capacity the violation
      is hard (the candidate is rejected).
    - When it only exceeds the soft capacity the violation is soft (the
      candidate is feasible but should be scored lower).

    Args:
        events: Existing timetable events.
        candidate: Candidate slot dictionary containing faculty_id,
            start_time, end_time, and optionally event_id of the event
            being moved.
        capacities: Mapping of faculty_id to preferred max hours.
            When a faculty is absent, no workload constraint applies.
        hard_capacities: Mapping of faculty_id to absolute max hours.
            Defaults to the soft capacity for each faculty.

    Returns:
        List of workload violations. Empty when no constraint applies or
        the projected workload stays within capacity.
    """
    if not capacities:
        return []

    faculty_id = candidate["faculty_id"]

    if faculty_id not in capacities:
        return []

    excluded_id = candidate.get("event_id")

    current_hours = 0.0
    for event in events:
        if event["faculty_id"] != faculty_id:
            continue
        if excluded_id is not None and event["id"] == excluded_id:
            continue
        current_hours += _event_duration_hours(
            event["start_time"],
            event["end_time"],
        )

    candidate_hours = _event_duration_hours(
        candidate["start_time"],
        candidate["end_time"],
    )
    projected_hours = current_hours + candidate_hours

    soft_capacity = capacities[faculty_id]
    hard_capacity = (hard_capacities or {}).get(faculty_id, soft_capacity)

    if projected_hours > hard_capacity:
        return [
            ConstraintViolation(
                constraint_type=WORKLOAD_CONSTRAINT,
                severity=HARD,
                event_id=candidate.get("event_id") or -1,
                resource=faculty_id,
                message=(
                    f"Workload constraint: candidate would push Faculty "
                    f"{faculty_id} to {projected_hours:.2f} hours, exceeding "
                    f"the hard capacity of {hard_capacity:.2f} hours."
                ),
            )
        ]

    if projected_hours > soft_capacity:
        return [
            ConstraintViolation(
                constraint_type=WORKLOAD_CONSTRAINT,
                severity=SOFT,
                event_id=candidate.get("event_id") or -1,
                resource=faculty_id,
                message=(
                    f"Workload constraint: candidate would push Faculty "
                    f"{faculty_id} to {projected_hours:.2f} hours, exceeding "
                    f"the preferred capacity of {soft_capacity:.2f} hours."
                ),
            )
        ]

    return []


class ConstraintEngine:
    """
    Evaluates scheduling events and candidate slots against constraints.

    The engine keeps scheduling rules in one place so that adding a new
    scheduling rule does not require rewriting the rescheduler.
    """

    def __init__(
        self,
        capacities: dict[int, float] | None = None,
        hard_capacities: dict[int, float] | None = None,
    ) -> None:
        """
        Initialize the constraint engine.

        Args:
            capacities: Mapping of faculty_id to preferred max hours used
                by the workload constraint.
            hard_capacities: Mapping of faculty_id to absolute max hours.
                Defaults to the soft capacity per faculty.
        """
        self.capacities = capacities or {}
        self.hard_capacities = hard_capacities or {}

    def evaluate(self, events: list[dict]) -> list[ConstraintViolation]:
        """
        Evaluate a timetable for all constraint violations.

        Args:
            events: List of timetable event dictionaries.

        Returns:
            List of constraint violations across the timetable.
        """
        violations: list[ConstraintViolation] = []

        for event in events:
            violations.extend(check_time_constraint(event))

        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                violations.extend(check_resource_conflicts(events[i], events[j]))

        return violations

    def evaluate_candidate(
        self,
        events: list[dict],
        candidate: dict,
    ) -> list[ConstraintViolation]:
        """
        Evaluate whether an event can be placed at a candidate slot.

        The candidate must be checked against:
        - Faculty, batch, group, and room availability
        - Time validity
        - Workload constraints

        Args:
            events: Existing timetable events.
            candidate: Candidate slot dictionary containing date,
                start_time, end_time, faculty_id, batch_id, room_id,
                group_id, and optionally event_id.

        Returns:
            List of violations. Empty when the candidate is feasible.
        """
        violations = check_time_constraint(candidate)

        pseudo_event = {
            "id": candidate.get("event_id") or -1,
            "faculty_id": candidate["faculty_id"],
            "batch_id": candidate["batch_id"],
            "room_id": candidate.get("room_id"),
            "group_id": candidate.get("group_id"),
            "date": candidate["date"],
            "start_time": candidate["start_time"],
            "end_time": candidate["end_time"],
        }

        for event in events:
            event_id = candidate.get("event_id")
            if event_id is not None and event["id"] == event_id:
                continue
            violations.extend(check_resource_conflicts(pseudo_event, event))

        violations.extend(
            check_workload_constraint(
                events,
                candidate,
                capacities=self.capacities,
                hard_capacities=self.hard_capacities,
            )
        )

        return violations


def detect_violations(events: list[dict]) -> list[dict]:
    """
    Detect structured constraint violations in a timetable.

    This is the constraint-aware counterpart of the Day 1/2 conflict
    detector. It returns structured, explainable violations.

    Args:
        events: List of timetable event dictionaries.

    Returns:
        List of violation dictionaries.
    """
    return [v.to_dict() for v in ConstraintEngine().evaluate(events)]