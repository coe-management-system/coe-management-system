"""
Rescheduling recommendation.

This module turns a detected conflict into an explainable rescheduling
recommendation without ever modifying the official timetable.

Workflow:

1. Identify the affected event.
2. Generate candidate slots.
3. Apply hard constraints (faculty, batch/group, room, time, workload).
4. Calculate the workload impact of each feasible candidate.
5. Calculate a deterministic score for each candidate.
6. Rank the candidates.
7. Return the recommendation with an explanation of why it was chosen.

When no candidate satisfies all hard constraints the module returns a
``NO_FEASIBLE_SLOT`` result with useful information about why candidates
were rejected.
"""

from .candidate_generator import evaluate_candidates, generate_candidates
from .scoring import score_candidate
from .workload_optimizer import calculate_workload_impact

NO_FEASIBLE_SLOT = "NO_FEASIBLE_SLOT"


def recommend_reschedule(
    events,
    event_id,
    candidates=None,
    dates=None,
    capacities=None,
    hard_capacities=None,
    preferred_time=None,
):
    """
    Generate a rescheduling recommendation for an event.

    Args:
        events: List of timetable event dictionaries.
        event_id: ID of the event to reschedule.
        candidates: Optional explicit candidate slots. When None, candidate
            slots are generated automatically.
        dates: Optional dates to generate candidates across.
        capacities: Optional faculty workload capacities.
        hard_capacities: Optional absolute workload capacities.
        preferred_time: Optional preferred start time in HH:MM format used
            for scoring.

    Returns:
        A recommendation dictionary. When at least one feasible candidate
        exists it contains status "recommendation", the top candidate, a
        human-readable reason, and the ranked candidate list. When no
        feasible candidate exists it contains status "NO_FEASIBLE_SLOT"
        and the aggregated rejection reasons.

    Raises:
        ValueError: If the requested event does not exist.
    """
    event = _find_event(events, event_id)

    if candidates is None:
        candidate_results = generate_candidates(
            events,
            event,
            dates=dates,
            capacities=capacities,
            hard_capacities=hard_capacities,
        )
    else:
        candidate_results = evaluate_candidates(
            events,
            event,
            candidates,
            capacities=capacities,
            hard_capacities=hard_capacities,
        )

    feasible = [c for c in candidate_results if c["status"] == "FEASIBLE"]

    if not feasible:
        return _no_feasible_result(candidate_results, event_id)

    for candidate in feasible:
        candidate_impact = calculate_workload_impact(
            events,
            {
                "faculty_id": event["faculty_id"],
                "start_time": candidate["start_time"],
                "end_time": candidate["end_time"],
            },
            capacities=capacities,
            exclude_event_id=event_id,
        )

        candidate["workload_impact"] = candidate_impact
        candidate["score_info"] = score_candidate(
            candidate,
            workload_impact=candidate_impact,
            preferred_time=preferred_time,
            priority=event.get("priority", "normal"),
            moved_events=0,
        )

    ranked = sorted(feasible, key=lambda c: c["score_info"]["score"], reverse=True)

    top = ranked[0]

    return {
        "status": "recommendation",
        "event_id": event_id,
        "recommended": {
            "date": top["date"],
            "start_time": top["start_time"],
            "end_time": top["end_time"],
        },
        "reason": _build_reason(top, event),
        "score": top["score_info"]["score"],
        "penalty": top["score_info"]["penalty"],
        "feasible_count": len(ranked),
        "ranked_candidates": ranked,
    }


def _find_event(events, event_id):
    """Return the event with the given id or raise ValueError."""
    for event in events:
        if event["id"] == event_id:
            return event

    raise ValueError(f"Event with id {event_id} was not found.")


def _no_feasible_result(candidate_results, event_id):
    """Build a NO_FEASIBLE_SLOT result with aggregated rejection reasons."""
    reasons: list[str] = []

    for candidate in candidate_results:
        for reason in candidate.get("reasons", []):
            if reason not in reasons:
                reasons.append(reason)

    return {
        "status": NO_FEASIBLE_SLOT,
        "event_id": event_id,
        "reasons": reasons,
        "message": (
            "No feasible time slot satisfies all hard constraints for "
            f"event {event_id}."
        ),
    }


def _build_reason(candidate, event):
    """Build a human-readable explanation for the top candidate."""
    reasons = [
        f"no faculty conflict for Faculty {event['faculty_id']}",
        f"no batch conflict for Batch {event['batch_id']}",
        "no room conflict",
        "no workload overload",
        "does not move another event",
    ]

    workload_status = candidate.get("workload_impact", {}).get("status")

    if workload_status == "overloaded":
        reasons.append("workload overload avoided")
    elif workload_status == "at_capacity":
        reasons.append("workload stays at capacity")

    return (
        f"Recommended: {candidate['date']} {candidate['start_time']}"
        f"-{candidate['end_time']}. Reason: {', '.join(reasons)}."
    )