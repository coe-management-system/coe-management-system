"""
Deterministic candidate scoring and ranking.

Every feasible candidate is scored using project-supported factors:

- Conflicts (feasible candidates have no hard violations)
- Workload impact (overload / capacity pressure)
- Priority impact (moving high-priority events is costly)
- Number of moved events
- Other penalties such as deviation from a preferred time

Scoring is fully deterministic. No machine learning or external services
are involved. The lowest penalty / highest score candidate is preferred.
"""

from .priorities import get_priority_value

BASE_SCORE = 1000.0

SOFT_VIOLATION_PENALTY = 50.0
WORKLOAD_OVERLOAD_PENALTY = 40.0
WORKLOAD_PRESSURE_PENALTY = 15.0
MOVED_EVENTS_PENALTY = 25.0
PRIORITY_PENALTY = 10.0
TIME_DEVIATION_PENALTY = 5.0


def _time_to_minutes(time_string) -> int:
    """Convert a HH:MM time string into minutes since midnight."""
    hours, minutes = map(int, time_string.split(":"))
    return hours * 60 + minutes


def score_candidate(
    candidate,
    workload_impact=None,
    preferred_time=None,
    priority=None,
    moved_events=0,
):
    """
    Calculate a deterministic score for a feasible candidate.

    Args:
        candidate: Feasible candidate dictionary containing start_time and
            end_time.
        workload_impact: Optional result of
            workload_optimizer.calculate_workload_impact for the candidate.
        preferred_time: Optional preferred start time in HH:MM format. When
            provided, deviation from it is penalised.
        priority: Optional priority name/value of the event being moved.
            Moving high-priority events is penalised.
        moved_events: Number of other events that would be moved. Defaults
            to zero.

    Returns:
        Dictionary containing:
            - score: Higher is better.
            - penalty: Lower is better.
            - breakdown: Per-factor penalty breakdown for explainability.
    """
    penalty = 0.0
    breakdown = {}

    soft_violations = 0
    for violation in candidate.get("violations", []):
        if violation.get("severity") == "soft":
            soft_violations += 1

    if soft_violations:
        soft_penalty = soft_violations * SOFT_VIOLATION_PENALTY
        penalty += soft_penalty
        breakdown["soft_violations"] = soft_penalty

    if workload_impact is not None:
        status = workload_impact.get("status")

        if status == "overloaded":
            penalty += WORKLOAD_OVERLOAD_PENALTY
            breakdown["workload_overload"] = WORKLOAD_OVERLOAD_PENALTY
        elif status == "at_capacity":
            penalty += WORKLOAD_PRESSURE_PENALTY
            breakdown["workload_pressure"] = WORKLOAD_PRESSURE_PENALTY

    if priority is not None:
        priority_value = get_priority_value(priority)
        priority_penalty = priority_value * PRIORITY_PENALTY
        penalty += priority_penalty
        breakdown["priority"] = priority_penalty

    if moved_events:
        movement_penalty = moved_events * MOVED_EVENTS_PENALTY
        penalty += movement_penalty
        breakdown["moved_events"] = movement_penalty

    if preferred_time is not None:
        deviation = _time_deviation_minutes(
            candidate["start_time"],
            preferred_time,
        )
        if deviation:
            time_penalty = (deviation // 30) * TIME_DEVIATION_PENALTY
            penalty += time_penalty
            breakdown["time_deviation"] = time_penalty

    penalty = round(penalty, 4)
    score = round(BASE_SCORE - penalty, 4)

    return {
        "score": score,
        "penalty": penalty,
        "breakdown": breakdown,
    }


def rank_candidates(candidates):
    """
    Rank candidate evaluations by score, highest first.

    Args:
        candidates: List of candidate evaluation dictionaries as produced
            by candidate_generator.evaluate_candidates, enriched with a
            score dictionary under the key "score_info".

    Returns:
        A new list sorted by score descending. Candidates without a
        "score_info" are sorted last by their original order.
    """

    def sort_key(item):
        score_info = item.get("score_info")
        if score_info is None:
            return -1.0
        return score_info["score"]

    return sorted(candidates, key=sort_key, reverse=True)


def _time_deviation_minutes(start_time: str, preferred_time: str) -> int:
    """Return the absolute deviation in minutes from a preferred time."""
    start = _time_to_minutes(start_time)
    preferred = _time_to_minutes(preferred_time)
    return abs(start - preferred)