"""
Scheduling optimization abstraction and deterministic baseline optimizer.

This module establishes the optimization layer introduced on Day 4. It
defines a pluggable :class:`SchedulingOptimizer` interface so future
algorithms (OR-Tools, genetic algorithms, AI-guided search, ...) can be
added without rewriting the API, database, or service layers.

The first implementation is :class:`BaselineOptimizer`, which is
deterministic and explainable:

1. Copy the official timetable into an isolated scenario.
2. Detect hard constraint violations (faculty/batch/group/room/time).
3. Generate feasible candidate slots for every conflicting event.
4. Evaluate every candidate through the constraint engine.
5. Discard candidates that violate a hard constraint (never scored).
6. Score the feasible candidates with the documented objective.
7. Select the best feasible schedule and compare it with the current one.
8. Return a structured :class:`OptimizationResult`.

The optimizer never modifies the official timetable. It only builds a
proposed schedule inside the scenario, mirroring the Day 3 what-if
isolation principle.
"""

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, timedelta

from .candidate_generator import evaluate_candidates, generate_slots
from .constraint_engine import ConstraintEngine, HARD
from .objective import (
    MODE_BALANCED,
    SUPPORTED_MODES,
    evaluate_objective,
    workload_summary,
)
from .priorities import get_priority_value
from .scoring import score_candidate
from .workload_optimizer import calculate_workload_impact

OPTIMIZED = "OPTIMIZED"
ALREADY_OPTIMAL = "ALREADY_OPTIMAL"
NO_FEASIBLE_SCHEDULE = "NO_FEASIBLE_SCHEDULE"

_STATUS_OPTIMIZED = OPTIMIZED
_STATUS_ALREADY_OPTIMAL = ALREADY_OPTIMAL
_STATUS_NO_FEASIBLE = NO_FEASIBLE_SCHEDULE


@dataclass
class OptimizationConfig:
    """
    Search boundaries and behavior for the baseline optimizer.

    Attributes:
        dates: Explicit list of dates to consider for candidate slots.
            When None, a deterministic window of the next five weekdays
            after each conflicting event is used.
        day_start: Earliest candidate slot start time, HH:MM.
        day_end: Latest allowed candidate slot end time, HH:MM.
        slot_minutes: Step between slot starts.
        mode: Objective mode. One of the ``objective.SUPPORTED_MODES``.
        max_moves: Upper bound on how many conflicting events are moved.
    """

    dates: list | None = None
    day_start: str = "08:00"
    day_end: str = "18:00"
    slot_minutes: int = 60
    mode: str = MODE_BALANCED
    max_moves: int = 50

    def __post_init__(self):
        if self.mode not in SUPPORTED_MODES:
            raise ValueError(
                f"Unsupported optimization mode: {self.mode}. "
                f"Expected one of: {', '.join(sorted(SUPPORTED_MODES))}"
            )


@dataclass
class OptimizationResult:
    """
    Structured result of an optimization run.

    The result is intentionally rich so the API, frontend, and AI layers
    can consume it without recomputing anything themselves.
    """

    status: str
    original_score: float
    optimized_score: float
    events_changed: int
    conflicts_before: int
    conflicts_after: int
    workload_before: dict
    workload_after: dict
    objective_breakdown: dict
    recommended_changes: list
    proposed_schedule: list
    rejected_candidates: list = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict:
        """Return the result as a serializable dictionary."""
        return {
            "status": self.status,
            "original_score": self.original_score,
            "optimized_score": self.optimized_score,
            "events_changed": self.events_changed,
            "conflicts_before": self.conflicts_before,
            "conflicts_after": self.conflicts_after,
            "workload_before": self.workload_before,
            "workload_after": self.workload_after,
            "objective_breakdown": self.objective_breakdown,
            "recommended_changes": self.recommended_changes,
            "proposed_schedule": self.proposed_schedule,
            "rejected_candidates": self.rejected_candidates,
            "message": self.message,
        }


class SchedulingOptimizer(ABC):
    """
    Interface implemented by every scheduling optimizer.

    Future algorithms plug in here without leaking into the API, database,
    frontend, or authentication layers.
    """

    @abstractmethod
    def optimize(
        self,
        events: list[dict],
        capacities: dict[int, float] | None = None,
        hard_capacities: dict[int, float] | None = None,
        config: OptimizationConfig | None = None,
    ) -> OptimizationResult:
        """
        Optimize a timetable scenario.

        Args:
            events: Timetable event dictionaries representing the official
                timetable. This is never modified.
            capacities: Optional mapping of faculty_id to preferred max
                hours used by the workload constraint.
            hard_capacities: Optional absolute workload capacities.
            config: Optional optimization configuration.

        Returns:
            An :class:`OptimizationResult` describing the proposed
            schedule and how it differs from the current one.
        """


class BaselineOptimizer(SchedulingOptimizer):
    """
    Deterministic, explainable baseline optimizer.

    Algorithm:

    1. Detect conflicting events through the constraint engine.
    2. If there are no hard conflicts the schedule is already optimal
       with respect to conflict minimization.
    3. Otherwise generate candidate slots for each conflicting event,
       evaluate them, discard hard-infeasible candidates, and score the
       remaining ones using the documented objective.
    4. Build the proposed schedule by moving the conflicting event with
       the best feasible candidate.
    5. Re-evaluate the proposed schedule, compare with the current one,
       and return a structured result.

    Tie-breaking is fully deterministic: candidates with equal scores are
    ordered by date, start time, then end time. No randomness is used.
    """

    def __init__(
        self,
        capacities: dict[int, float] | None = None,
        hard_capacities: dict[int, float] | None = None,
        config: OptimizationConfig | None = None,
    ) -> None:
        self.capacities = capacities or {}
        self.hard_capacities = hard_capacities or {}
        self.config = config or OptimizationConfig()

    def optimize(
        self,
        events: list[dict],
        capacities: dict[int, float] | None = None,
        hard_capacities: dict[int, float] | None = None,
        config: OptimizationConfig | None = None,
    ) -> OptimizationResult:
        capacities = capacities or self.capacities
        hard_capacities = hard_capacities or self.hard_capacities
        config = config or self.config

        scenario = deepcopy(events)
        engine = ConstraintEngine(
            capacities=capacities,
            hard_capacities=hard_capacities,
        )

        original_violations = engine.evaluate(scenario)
        original_hard = [v for v in original_violations if v.severity == HARD]
        conflicts_before = len(original_hard)

        original_objective = evaluate_objective(
            scenario,
            capacities=capacities,
            moved_event_ids=[],
            mode=config.mode,
            hard_capacities=hard_capacities,
        )
        workload_before = workload_summary(scenario, capacities)

        if conflicts_before == 0:
            return _build_result(
                status=ALREADY_OPTIMAL,
                original_objective=original_objective,
                optimized_objective=original_objective,
                original_events=scenario,
                proposed_events=scenario,
                changes=[],
                workloads=(workload_before, workload_before),
                capacities=capacities,
            )

        conflicting_ids = _conflicting_event_ids(original_hard)
        changes, rejected = self._resolve_conflicts(
            scenario,
            conflicting_ids,
            engine=engine,
            capacities=capacities,
            hard_capacities=hard_capacities,
            config=config,
        )

        proposed = scenario
        conflicts_after = _count_hard(engine.evaluate(proposed))

        optimized_objective = evaluate_objective(
            proposed,
            capacities=capacities,
            moved_event_ids=[c["event_id"] for c in changes],
            original_events=events,
            mode=config.mode,
            hard_capacities=hard_capacities,
        )
        workload_after = workload_summary(proposed, capacities)

        if conflicts_after > 0:
            return _build_no_feasible(
                original_objective=original_objective,
                conflicts_before=conflicts_before,
                conflicts_after=conflicts_after,
                proposed_events=proposed,
                changes=changes,
                rejected=rejected,
                workloads=(workload_before, workload_after),
            )

        status = (
            OPTIMIZED
            if optimized_objective["score"] > original_objective["score"]
            else ALREADY_OPTIMAL
        )

        return _build_result(
            status=status,
            original_objective=original_objective,
            optimized_objective=optimized_objective,
            original_events=events,
            proposed_events=proposed,
            changes=changes,
            workloads=(workload_before, workload_after),
            capacities=capacities,
        )

    def _resolve_conflicts(
        self,
        scenario,
        conflicting_ids,
        engine,
        capacities,
        hard_capacities,
        config,
    ):
        """
        Attempt to resolve every conflicting event by moving it to its
        best feasible candidate slot.

        After each move the constraint engine re-evaluates the scenario,
        so events that are no longer conflicting are left untouched.

        Returns:
            Tuple of (changes, rejected) where changes is a list of
            recommended change dictionaries and rejected aggregates the
            rejection reasons for diagnostics.
        """
        changes = []
        rejected = []
        attempted = 0

        remaining = set(conflicting_ids)
        blocked = set()

        while (remaining - blocked) and attempted < config.max_moves:
            event_id = _lowest_priority_event_id(scenario, remaining - blocked)
            event = _find_event(scenario, event_id)
            if event is None:
                blocked.add(event_id)
                continue

            candidates = self._generate_and_evaluate(
                scenario,
                event,
                capacities=capacities,
                hard_capacities=hard_capacities,
                config=config,
            )

            feasible = [c for c in candidates if c["status"] == "FEASIBLE"]
            feasible = [
                c for c in feasible if _is_different_slot(event, c)
            ]
            rejected.extend(
                _rejection_summary(c)
                for c in candidates
                if c["status"] == "REJECTED"
            )

            if not feasible:
                blocked.add(event_id)
                continue

            for candidate in feasible:
                impact = calculate_workload_impact(
                    scenario,
                    {
                        "faculty_id": event["faculty_id"],
                        "start_time": candidate["start_time"],
                        "end_time": candidate["end_time"],
                    },
                    capacities=capacities,
                    exclude_event_id=event_id,
                )
                candidate["workload_impact"] = impact
                candidate["score_info"] = score_candidate(
                    candidate,
                    workload_impact=impact,
                    priority=event.get("priority", "normal"),
                    moved_events=0,
                )

            best = self._pick_best(feasible)

            change = _build_change(
                event,
                best,
                event.get("priority", "normal"),
            )

            _apply_candidate(scenario, event, best)

            changes.append(change)
            attempted += 1

            remaining = _conflicting_event_ids(
                [v for v in engine.evaluate(scenario) if v.severity == HARD]
            )

        return changes, rejected

    def _generate_and_evaluate(
        self,
        scenario,
        event,
        capacities,
        hard_capacities,
        config,
    ):
        """
        Generate and evaluate candidate slots for an event.

        Returns:
            List of candidate evaluation dictionaries.
        """
        dates = config.dates or _default_dates(event)

        duration = _duration_minutes(event)

        slots = generate_slots(
            dates=dates,
            day_start=config.day_start,
            day_end=config.day_end,
            slot_minutes=config.slot_minutes,
            duration_minutes=duration,
        )

        return evaluate_candidates(
            scenario,
            event,
            slots,
            capacities=capacities,
            hard_capacities=hard_capacities,
        )

    def _pick_best(self, feasible):
        """
        Select the best feasible candidate deterministically.

        The best candidate has the highest score. Ties are broken by
        date, then start time, then end time (all ascending).
        """
        return sorted(
            feasible,
            key=lambda c: (
                -c["score_info"]["score"],
                c["date"],
                c["start_time"],
                c["end_time"],
            ),
        )[0]


def _conflicting_event_ids(violations) -> set:
    """Collect the event ids involved in hard violations."""
    ids = set()
    for violation in violations:
        ids.add(violation.event_id)
        if violation.conflicting_event_id is not None:
            ids.add(violation.conflicting_event_id)
    return {event_id for event_id in ids if event_id > 0}


def _count_hard(violations) -> int:
    """Count hard violations."""
    return sum(1 for v in violations if v.severity == HARD)


def _is_different_slot(event, candidate) -> bool:
    """Return True when the candidate slot differs from the event's slot."""
    return not (
        str(event["date"]) == str(candidate["date"])
        and event["start_time"] == candidate["start_time"]
        and event["end_time"] == candidate["end_time"]
    )


def _lowest_priority_event_id(scenario, candidate_ids) -> int:
    """
    Select the conflicting event that should move first.

    Lower-priority events move before higher-priority ones so that
    urgent/high-priority events are preserved whenever possible. Ties are
    broken by event id ascending for determinism.
    """
    def sort_key(event_id):
        event = _find_event(scenario, event_id)
        if event is None:
            return (0, event_id)
        try:
            priority = get_priority_value(event.get("priority", 2))
        except ValueError:
            priority = 2
        return (priority, event_id)

    return sorted(candidate_ids, key=sort_key)[0]


def _find_event(events, event_id):
    """Return the event with the given id, or None."""
    for event in events:
        if event["id"] == event_id:
            return event
    return None


def _apply_candidate(scenario, event, candidate) -> None:
    """Move an event to a candidate slot inside the scenario in place."""
    event["date"] = candidate["date"]
    event["start_time"] = candidate["start_time"]
    event["end_time"] = candidate["end_time"]


def _duration_minutes(event) -> int:
    """Return the duration of an event in minutes."""
    start_h, start_m = map(int, event["start_time"].split(":"))
    end_h, end_m = map(int, event["end_time"].split(":"))
    return (end_h * 60 + end_m) - (start_h * 60 + start_m)


def _default_dates(event) -> list[date]:
    """
    Return a deterministic set of alternative dates for an event.

    Uses the five weekdays following the event's current date.
    """
    current = event["date"]
    if not isinstance(current, date):
        current = date.fromisoformat(str(current))

    dates = []
    day = current + timedelta(days=1)
    while len(dates) < 5:
        if day.weekday() < 5:
            dates.append(day)
        day += timedelta(days=1)

    return dates


def _build_change(event, candidate, priority) -> dict:
    """Build a recommended change dictionary with structured reasons."""
    return {
        "event_id": event["id"],
        "faculty_id": event["faculty_id"],
        "batch_id": event["batch_id"],
        "room_id": event.get("room_id"),
        "from": {
            "date": event["date"],
            "start_time": event["start_time"],
            "end_time": event["end_time"],
        },
        "to": {
            "date": candidate["date"],
            "start_time": candidate["start_time"],
            "end_time": candidate["end_time"],
        },
        "priority": priority,
        "score": candidate["score_info"]["score"],
        "reasons": _build_reasons(candidate),
    }


def _build_reasons(candidate) -> list[str]:
    """Build the structured reasons explaining why a slot is recommended."""
    reasons = [
        "no faculty conflict",
        "no batch conflict",
        "no room conflict",
        "valid time range",
        "within workload capacity",
    ]

    workload_status = candidate.get("workload_impact", {}).get("status")
    if workload_status == "overloaded":
        reasons.append("avoids workload overload")
    elif workload_status == "at_capacity":
        reasons.append("workload stays at capacity")

    return reasons


def _rejection_summary(candidate) -> dict:
    """Summarize the rejection reasons for a candidate."""
    reasons = candidate.get("reasons", [])
    return {
        "date": candidate["date"],
        "start_time": candidate["start_time"],
        "end_time": candidate["end_time"],
        "reasons": reasons,
    }


def _build_result(
    status,
    original_objective,
    optimized_objective,
    original_events,
    proposed_events,
    changes,
    workloads,
    capacities,
) -> OptimizationResult:
    workload_before, workload_after = workloads

    message = ""
    if status == ALREADY_OPTIMAL:
        message = (
            "The timetable is already conflict-free and no improvement "
            "was found."
        )

    return OptimizationResult(
        status=status,
        original_score=original_objective["score"],
        optimized_score=optimized_objective["score"],
        events_changed=len(changes),
        conflicts_before=original_objective["conflicts"],
        conflicts_after=optimized_objective["conflicts"],
        workload_before=workload_before,
        workload_after=workload_after,
        objective_breakdown={
            "before": original_objective["breakdown"],
            "after": optimized_objective["breakdown"],
        },
        recommended_changes=changes,
        proposed_schedule=[deepcopy(e) for e in proposed_events],
        message=message,
    )


def _build_no_feasible(
    original_objective,
    conflicts_before,
    conflicts_after,
    proposed_events,
    changes,
    rejected,
    workloads,
) -> OptimizationResult:
    workload_before, workload_after = workloads

    return OptimizationResult(
        status=NO_FEASIBLE_SCHEDULE,
        original_score=original_objective["score"],
        optimized_score=original_objective["score"],
        events_changed=len(changes),
        conflicts_before=conflicts_before,
        conflicts_after=conflicts_after,
        workload_before=workload_before,
        workload_after=workload_after,
        objective_breakdown={
            "before": original_objective["breakdown"],
            "after": {},
        },
        recommended_changes=changes,
        proposed_schedule=[deepcopy(e) for e in proposed_events],
        rejected_candidates=rejected,
        message=(
            "No feasible schedule satisfies all hard constraints. "
            "Conflicts could not be fully resolved."
        ),
    )
