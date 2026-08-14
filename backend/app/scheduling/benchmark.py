"""
R&D scheduling benchmark.

This module establishes a reproducible baseline scenario that later
optimization algorithms can be compared against. It records the size of
the scenario and the outcome of the current constraint-aware rescheduling
engine.

No genetic algorithms, OR-Tools, reinforcement learning, or AI scheduling
is used. The goal is a deterministic baseline.
"""

import time
from datetime import date, timedelta

from .conflict_detector import detect_conflicts
from .recommendation import recommend_reschedule
from .workload_optimizer import calculate_workload_report


def build_benchmark_scenario():
    """
    Build a reproducible benchmark scenario.

    Returns:
        Dictionary containing events, capacities, and metadata describing
        the number of faculty, rooms, and batches/groups involved.
    """
    capacities = {
        1: 16,
        2: 16,
        3: 12,
    }

    day = date(2026, 9, 7)

    events = [
        {
            "id": 1,
            "subject_id": 1,
            "faculty_id": 1,
            "batch_id": 10,
            "room_id": "101",
            "date": day.isoformat(),
            "start_time": "09:00",
            "end_time": "10:00",
            "priority": 2,
        },
        {
            "id": 2,
            "subject_id": 2,
            "faculty_id": 1,
            "batch_id": 11,
            "room_id": "102",
            "date": day.isoformat(),
            "start_time": "09:30",
            "end_time": "10:30",
            "priority": 2,
        },
        {
            "id": 3,
            "subject_id": 3,
            "faculty_id": 2,
            "batch_id": 10,
            "room_id": "101",
            "date": (day + timedelta(days=1)).isoformat(),
            "start_time": "10:00",
            "end_time": "11:00",
            "priority": 2,
        },
        {
            "id": 4,
            "subject_id": 4,
            "faculty_id": 2,
            "batch_id": 12,
            "room_id": "103",
            "date": (day + timedelta(days=1)).isoformat(),
            "start_time": "11:00",
            "end_time": "12:00",
            "priority": 3,
        },
        {
            "id": 5,
            "subject_id": 5,
            "faculty_id": 3,
            "batch_id": 13,
            "room_id": "104",
            "date": (day + timedelta(days=2)).isoformat(),
            "start_time": "13:00",
            "end_time": "15:00",
            "priority": 2,
        },
    ]

    return {
        "events": events,
        "capacities": capacities,
        "meta": {
            "number_of_events": len(events),
            "number_of_faculty": len(capacities),
            "number_of_rooms": len(
                {e["room_id"] for e in events if e.get("room_id")}
            ),
            "number_of_batches_groups": len({e["batch_id"] for e in events}),
        },
    }


def run_benchmark(scenario=None, conflict_event_id=None):
    """
    Run the rescheduling benchmark on a scenario.

    The scenario contains a faculty conflict (events 1 and 2). The
    benchmark reschedules the conflicting event and records the outcome.

    Args:
        scenario: Optional scenario dictionary. Defaults to
            build_benchmark_scenario().
        conflict_event_id: Optional event id to reschedule. Defaults to 2.

    Returns:
        Dictionary of benchmark metrics including scenario metadata,
        initial/final conflicts, overloaded faculty, moved events, and
        execution time.
    """
    if scenario is None:
        scenario = build_benchmark_scenario()

    events = scenario["events"]
    capacities = scenario["capacities"]
    meta = scenario["meta"]

    initial_conflicts = len(detect_conflicts(events))
    initial_overloaded = _count_overloaded(events, capacities)

    target_event_id = conflict_event_id or 2

    start = time.perf_counter()

    recommendation = recommend_reschedule(
        events,
        target_event_id,
        capacities=capacities,
    )

    elapsed = time.perf_counter() - start

    # The engine never modifies the timetable, so no events are moved.
    final_conflicts = len(detect_conflicts(events))
    final_overloaded = _count_overloaded(events, capacities)

    return {
        "scenario": meta,
        "initial_conflicts": initial_conflicts,
        "final_conflicts": final_conflicts,
        "overloaded_faculty": {
            "initial": initial_overloaded,
            "final": final_overloaded,
        },
        "moved_events": 0,
        "recommendation_status": recommendation.get("status"),
        "execution_time_seconds": round(elapsed, 6),
    }


def _count_overloaded(events, capacities):
    """Count faculty members whose workload exceeds their capacity."""
    report = calculate_workload_report(events, capacities)
    return sum(1 for entry in report if entry["status"] == "overloaded")