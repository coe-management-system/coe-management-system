"""
R&D scheduling benchmark.

This module establishes a reproducible baseline scenario that later
optimization algorithms can be compared against. It records the size of
the scenario and the outcome of the current constraint-aware rescheduling
engine and the Day 4 deterministic baseline optimizer.

No genetic algorithms, OR-Tools, reinforcement learning, or AI scheduling
is used. The goal is a deterministic baseline.

M3-12 R&D Evaluation: Compares greedy, constraint-based, and optimization
approaches. Measures conflicts, overload, syllabus delay, moved classes,
and runtime.
"""

import time
from datetime import date, timedelta
from typing import Dict, Any, List, Optional

from .comparison import compare_schedules
from .conflict_detector import detect_conflicts
from .candidate_generator import generate_slots, evaluate_candidates
from .objective import evaluate_objective
from .optimizer import BaselineOptimizer, OptimizationConfig
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


def build_optimization_scenario():
    """
    Build a reproducible optimization benchmark scenario.

    The scenario contains multiple overlapping events that produce hard
    conflicts, so the Day 4 optimizer has something meaningful to resolve.

    Returns:
        Dictionary containing events, capacities, and metadata describing
        the number of faculty, rooms, and batches/groups involved.
    """
    capacities = {
        1: 16,
        2: 16,
        3: 12,
        4: 12,
    }

    day = date(2026, 9, 14)

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
            "date": day.isoformat(),
            "start_time": "10:00",
            "end_time": "11:00",
            "priority": 3,
        },
        {
            "id": 4,
            "subject_id": 4,
            "faculty_id": 2,
            "batch_id": 11,
            "room_id": "102",
            "date": day.isoformat(),
            "start_time": "10:30",
            "end_time": "11:30",
            "priority": 2,
        },
        {
            "id": 5,
            "subject_id": 5,
            "faculty_id": 3,
            "batch_id": 12,
            "room_id": "103",
            "date": (day + timedelta(days=1)).isoformat(),
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


def run_optimization_benchmark(scenario=None, config=None):
    """
    Run the Day 4 baseline optimizer benchmark on a scenario.

    Args:
        scenario: Optional scenario dictionary. Defaults to
            build_optimization_scenario().
        config: Optional OptimizationConfig.

    Returns:
        Dictionary of benchmark metrics including scenario metadata,
        conflicts/workload/objective before and after, moved events, and
        execution time.
    """
    if scenario is None:
        scenario = build_optimization_scenario()

    events = scenario["events"]
    capacities = scenario["capacities"]
    meta = scenario["meta"]

    objective_before = evaluate_objective(
        events,
        capacities=capacities,
    )

    start = time.perf_counter()

    optimizer = BaselineOptimizer(
        capacities=capacities,
        config=config or OptimizationConfig(),
    )
    result = optimizer.optimize(
        events,
        capacities=capacities,
        config=config,
    )

    elapsed = time.perf_counter() - start

    proposed = result.proposed_schedule
    comparison = compare_schedules(
        events,
        proposed,
        capacities=capacities,
    )

    return {
        "scenario": meta,
        "status": result.status,
        "conflicts": {
            "before": result.conflicts_before,
            "after": result.conflicts_after,
        },
        "workload": {
            "before": objective_before["breakdown"].get(
                "workload_overload",
                0.0,
            ),
            "after": result.objective_breakdown["after"].get(
                "workload_overload",
                0.0,
            ),
        },
        "objective_score": {
            "before": result.original_score,
            "after": result.optimized_score,
        },
        "moved_events": result.events_changed,
        "comparison": comparison["events"],
        "execution_time_seconds": round(elapsed, 6),
    }


def run_performance_benchmark(sizes=(10, 50, 100), runs=3):
    """
    Measure the optimizer performance baseline on synthetic timetables.

    Args:
        sizes: Timetable sizes (number of events) to measure.
        runs: How many times each size is run.

    Returns:
        Dictionary mapping event count to recorded metrics: input size,
        candidate evaluation cost, execution time, and result quality.
    """
    results = {}

    for size in sizes:
        scenario = _synthetic_scenario(size)
        times = []
        statuses = set()
        moved = set()

        for _ in range(runs):
            start = time.perf_counter()
            optimizer = BaselineOptimizer(
                capacities=scenario["capacities"],
            )
            result = optimizer.optimize(
                scenario["events"],
                capacities=scenario["capacities"],
            )
            times.append(time.perf_counter() - start)
            statuses.add(result.status)
            moved.add(result.events_changed)

        results[size] = {
            "input_size": size,
            "execution_time_seconds": {
                "min": round(min(times), 6),
                "max": round(max(times), 6),
                "mean": round(sum(times) / len(times), 6),
            },
            "statuses": sorted(statuses),
            "moved_events": sorted(moved),
            "result_quality": "conflict-free"
            if all(s == "OPTIMIZED" or s == "ALREADY_OPTIMAL" for s in statuses)
            else "conflicting",
        }

    return results


def _synthetic_scenario(size):
    """
    Build a synthetic timetable of the given size.

    Odd-numbered events share a faculty member and overlap with the
    following event, producing deterministic conflicts for the optimizer.
    """
    capacities = {}
    events = []
    day = date(2026, 10, 5)

    for index in range(1, size + 1):
        faculty_id = ((index - 1) % 6) + 1
        capacities.setdefault(faculty_id, 40)

        hour = 8 + (index - 1) % 9
        start = f"{hour:02d}:00"
        end = f"{hour + 1:02d}:00"

        if index % 2 == 0:
            hour = 8 + (index - 1) % 9
            start = f"{hour:02d}:30"
            end = f"{hour + 1:02d}:30"

        events.append(
            {
                "id": index,
                "subject_id": index,
                "faculty_id": faculty_id,
                "batch_id": 100 + index,
                "room_id": f"{(index % 5) + 100}",
                "date": (day + timedelta(days=(index - 1) // 8)).isoformat(),
                "start_time": start,
                "end_time": end,
                "priority": 2,
            }
        )

    return {
        "events": events,
        "capacities": capacities,
    }


# =============================================================================
# M3-12 R&D Evaluation Functions
# =============================================================================

def run_greedy_baseline(
    events: List[Dict],
    capacities: Dict[int, float],
    config: Optional[OptimizationConfig] = None,
) -> Dict[str, Any]:
    """
    Run the greedy baseline approach (recommend_reschedule).
    
    This is the Day 3 approach - single event rescheduling with
    constraint-aware candidate evaluation and scoring.
    """
    # Create a copy to avoid mutation
    events_copy = [dict(e) for e in events]
    
    # Find first conflicted event
    conflicts = detect_conflicts(events_copy)
    if not conflicts:
        return {
            "approach": "greedy_baseline",
            "status": "NO_CONFLICTS",
            "initial_conflicts": 0,
            "final_conflicts": 0,
            "moved_events": 0,
            "execution_time_seconds": 0.0,
        }
    
    # Get the first conflicted event
    conflicted_event = conflicts[0]
    target_event_id = conflicted_event.get("event_id", 1)
    
    start = time.perf_counter()
    
    recommendation = recommend_reschedule(
        events_copy,
        target_event_id,
        capacities=capacities,
    )
    
    elapsed = time.perf_counter() - start
    
    # Greedy doesn't actually move events, just recommends
    final_conflicts = len(detect_conflicts(events_copy))
    
    return {
        "approach": "greedy_baseline",
        "status": recommendation.get("status", "UNKNOWN"),
        "initial_conflicts": len(conflicts),
        "final_conflicts": final_conflicts,
        "conflicts_resolved": len(conflicts) - final_conflicts,
        "moved_events": 0,  # Greedy only recommends, doesn't move
        "recommendation": recommendation,
        "execution_time_seconds": round(elapsed, 6),
    }


def run_constraint_based_approach(
    events: List[Dict],
    capacities: Dict[int, float],
    config: Optional[OptimizationConfig] = None,
) -> Dict[str, Any]:
    """
    Run the constraint-based approach (candidate generation + scoring).
    
    This evaluates all feasible candidates and selects the best
    without global optimization.
    """
    events_copy = [dict(e) for e in events]
    
    start = time.perf_counter()
    
    # Generate all feasible slots for the date range in events
    dates = list(set(e["date"] for e in events_copy))
    slots = generate_slots(dates=dates)
    
    # Evaluate candidates for each event
    evaluations = []
    for event in events_copy:
        event_evals = evaluate_candidates(
            events_copy,
            event,
            slots,
            capacities=capacities,
        )
        evaluations.extend(event_evals)
    
    # Filter feasible
    feasible = [e for e in evaluations if e.get("status") == "FEASIBLE"]
    
    # Select best by score (if scoring is available)
    best = None
    if feasible:
        best = max(feasible, key=lambda x: x.get("score", -float('inf')))
    
    elapsed = time.perf_counter() - start
    
    return {
        "approach": "constraint_based",
        "status": "OPTIMIZED" if best else "NO_FEASIBLE",
        "initial_conflicts": len(detect_conflicts(events_copy)),
        "final_conflicts": len(detect_conflicts(events_copy)),  # Constraint-based doesn't move
        "candidates_evaluated": len(evaluations),
        "feasible_candidates": len([e for e in evaluations if e.get("status") == "FEASIBLE"]),
        "best_candidate_score": best.get("score") if best else None,
        "execution_time_seconds": round(time.perf_counter() - start, 6),
    }


def run_optimization_approach(
    events: List[Dict],
    capacities: Dict[int, float],
    config: Optional[OptimizationConfig] = None,
) -> Dict[str, Any]:
    """
    Run the full optimization approach (BaselineOptimizer).
    
    This is the Day 4 approach - global optimization with objective
    function and iterative improvement.
    """
    events_copy = [dict(e) for e in events]
    
    start = time.perf_counter()
    
    optimizer = BaselineOptimizer(
        capacities=capacities,
        config=config or OptimizationConfig(),
    )
    result = optimizer.optimize(
        events_copy,
        capacities=capacities,
        config=config,
    )
    
    elapsed = time.perf_counter() - start
    
    return {
        "approach": "optimization",
        "status": result.status,
        "initial_conflicts": result.conflicts_before,
        "final_conflicts": result.conflicts_after,
        "conflicts_resolved": result.conflicts_before - result.conflicts_after,
        "moved_events": result.events_changed,
        "objective_improvement": result.original_score - result.optimized_score,
        "objective_breakdown": result.objective_breakdown,
        "execution_time_seconds": round(elapsed, 6),
    }


def run_rnd_evaluation(
    scenario: Optional[Dict] = None,
    config: Optional[OptimizationConfig] = None,
) -> Dict[str, Any]:
    """
    Run comprehensive R&D evaluation comparing all three approaches.
    
    Measures: conflicts, overload, syllabus delay, moved classes, runtime.
    
    Args:
        scenario: Optional scenario dict. Defaults to build_optimization_scenario().
        config: Optional OptimizationConfig.
        
    Returns:
        Dictionary with comparison metrics for all approaches.
    """
    if scenario is None:
        scenario = build_optimization_scenario()
    
    events = scenario["events"]
    capacities = scenario["capacities"]
    meta = scenario.get("meta") or _derive_meta(events)
    
    # Calculate syllabus delay proxy (based on pending classes)
    # This is a placeholder - real implementation would use syllabus data
    syllabus_delay = _estimate_syllabus_delay(events, capacities)
    
    # Run all three approaches
    greedy_result = run_greedy_baseline(events, capacities, config)
    constraint_result = run_constraint_based_approach(events, capacities, config)
    optimization_result = run_optimization_approach(events, capacities, config)
    
    # Workload metrics
    workload_before = evaluate_objective(events, capacities=capacities)["breakdown"].get("workload_overload", 0.0)
    
    comparison = {
        "scenario": meta,
        "syllabus_delay_estimate": syllabus_delay,
        "approaches": {
            "greedy_baseline": greedy_result,
            "constraint_based": constraint_result,
            "optimization": optimization_result,
        },
        "comparison": {
            "conflicts": {
                "greedy": {"initial": greedy_result["initial_conflicts"], "final": greedy_result["final_conflicts"]},
                "constraint_based": {"initial": constraint_result["initial_conflicts"], "final": constraint_result["final_conflicts"]},
                "optimization": {"initial": optimization_result["initial_conflicts"], "final": optimization_result["final_conflicts"]},
            },
            "moved_events": {
                "greedy": greedy_result.get("moved_events", 0),
                "constraint_based": 0,
                "optimization": optimization_result.get("moved_events", 0),
            },
            "execution_time_seconds": {
                "greedy": greedy_result["execution_time_seconds"],
                "constraint_based": constraint_result["execution_time_seconds"],
                "optimization": optimization_result["execution_time_seconds"],
            },
            "best_approach": _determine_best_approach(greedy_result, constraint_result, optimization_result),
        },
    }
    
    return comparison


def _derive_meta(events: List[Dict]) -> Dict[str, Any]:
    """Derive scenario metadata from the event list when none is provided."""
    return {
        "number_of_events": len(events),
        "number_of_faculty": len({e["faculty_id"] for e in events}),
        "number_of_rooms": len({e["room_id"] for e in events if e.get("room_id")}),
        "number_of_batches_groups": len({e["batch_id"] for e in events}),
    }


def _estimate_syllabus_delay(events: List[Dict], capacities: Dict[int, float]) -> float:
    """Estimate syllabus delay based on workload and conflicts."""
    # Simple heuristic: more conflicts and overload = more delay
    conflicts = len(detect_conflicts(events))
    objective = evaluate_objective(events, capacities=capacities)
    workload_overload = objective["breakdown"].get("workload_overload", 0.0)
    return conflicts * 0.5 + workload_overload * 0.1


def _determine_best_approach(greedy, constraint, optimization) -> str:
    """Determine the best approach based on multiple criteria."""
    scores = {}
    
    for name, result in [("greedy", greedy), ("constraint_based", constraint), ("optimization", optimization)]:
        score = 0
        # Fewer final conflicts is better
        score -= result.get("final_conflicts", 999) * 10
        # Fewer moved events is better (less disruption)
        score -= result.get("moved_events", 0) * 2
        # Faster is better
        score -= result.get("execution_time_seconds", 999) * 100
        # Prefer approaches that actually resolve conflicts
        if result.get("conflicts_resolved", 0) > 0:
            score += 50
        
        scores[name] = score
    
    return max(scores, key=scores.get)


def run_rnd_evaluation_suite(
    sizes: tuple = (10, 50, 100),
    runs_per_size: int = 3,
) -> Dict[str, Any]:
    """
    Run R&D evaluation across multiple scenario sizes.
    
    This provides the comprehensive benchmark for R&D evaluation.
    """
    results = {}
    
    for size in sizes:
        scenario = _synthetic_scenario(size)
        size_results = []
        
        for _ in range(runs_per_size):
            result = run_rnd_evaluation(scenario)
            size_results.append(result)
        
        # Aggregate
        avg_times = {
            approach: sum(r["approaches"][approach]["execution_time_seconds"] for r in size_results) / len(size_results)
            for approach in ["greedy_baseline", "constraint_based", "optimization"]
        }
        
        avg_conflicts = {
            approach: sum(r["approaches"][approach]["final_conflicts"] for r in size_results) / len(size_results)
            for approach in ["greedy_baseline", "constraint_based", "optimization"]
        }
        
        avg_moved = {
            approach: sum(r["approaches"][approach].get("moved_events", 0) for r in size_results) / len(size_results)
            for approach in ["greedy_baseline", "constraint_based", "optimization"]
        }
        
        results[size] = {
            "input_size": size,
            "runs": runs_per_size,
            "avg_execution_time_seconds": avg_times,
            "avg_final_conflicts": avg_conflicts,
            "avg_moved_events": avg_moved,
            "detailed_runs": size_results,
        }
    
    return results
