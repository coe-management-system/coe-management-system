"""
Schedule comparison (before / after optimization).

Day 4 introduces a comparison capability that identifies how an
optimized (proposed) schedule differs from the current schedule:

- events unchanged
- events moved
- events added / removed (when applicable)
- conflicts changed
- workload changed
- objective score changed

Metrics are computed in the scheduling layer, never in the frontend.
"""

from .objective import evaluate_objective, workload_summary


def _slot(event):
    """Return the time slot of an event as a comparable tuple."""
    return (
        str(event["date"]),
        event["start_time"],
        event["end_time"],
    )


def compare_schedules(
    current_events,
    proposed_events,
    capacities=None,
    mode="BALANCED",
    hard_capacities=None,
) -> dict:
    """
    Compare the current schedule with a proposed schedule.

    Args:
        current_events: List of current timetable event dictionaries.
        proposed_events: List of proposed timetable event dictionaries.
        capacities: Optional mapping of faculty_id to max hours.
        mode: Objective mode used for the score comparison.
        hard_capacities: Optional absolute workload capacities.

    Returns:
        Dictionary containing:
            - events: total, unchanged, moved, added, removed.
            - conflicts: before and after hard-violation counts.
            - workload: before and after workload summaries.
            - objective: before and after objective scores.
    """
    current_by_id = {e["id"]: e for e in current_events}
    proposed_by_id = {e["id"]: e for e in proposed_events}

    all_ids = sorted(set(current_by_id) | set(proposed_by_id))

    unchanged = []
    moved = []
    added = []
    removed = []

    for event_id in all_ids:
        current = current_by_id.get(event_id)
        proposed = proposed_by_id.get(event_id)

        if current is None:
            added.append(event_id)
            continue

        if proposed is None:
            removed.append(event_id)
            continue

        if _slot(current) == _slot(proposed):
            unchanged.append(event_id)
        else:
            moved.append(event_id)

    conflicts_before = evaluate_objective(
        current_events,
        capacities=capacities,
        mode=mode,
        hard_capacities=hard_capacities,
    )["conflicts"]
    conflicts_after = evaluate_objective(
        proposed_events,
        capacities=capacities,
        mode=mode,
        hard_capacities=hard_capacities,
    )["conflicts"]

    return {
        "events": {
            "total": len(all_ids),
            "unchanged": len(unchanged),
            "moved": len(moved),
            "added": len(added),
            "removed": len(removed),
        },
        "conflicts": {
            "before": conflicts_before,
            "after": conflicts_after,
        },
        "workload": {
            "before": workload_summary(current_events, capacities),
            "after": workload_summary(proposed_events, capacities),
        },
        "objective": {
            "before": evaluate_objective(
                current_events,
                capacities=capacities,
                mode=mode,
                hard_capacities=hard_capacities,
            )["score"],
            "after": evaluate_objective(
                proposed_events,
                capacities=capacities,
                mode=mode,
                hard_capacities=hard_capacities,
            )["score"],
        },
    }
