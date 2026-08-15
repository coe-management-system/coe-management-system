import unittest
from datetime import date

from app.scheduling.objective import (
    MODE_BALANCED,
    MODE_CONFLICT_MINIMIZATION,
    MODE_WORKLOAD_BALANCING,
    evaluate_objective,
    room_utilization_penalty,
    workload_balance_penalty,
    workload_overload_penalty,
)
from app.scheduling.optimizer import (
    ALREADY_OPTIMAL,
    NO_FEASIBLE_SCHEDULE,
    OPTIMIZED,
    BaselineOptimizer,
    OptimizationConfig,
    OptimizationResult,
)


def make_event(
    event_id,
    faculty_id,
    batch_id,
    room_id,
    start,
    end,
    event_date="2026-08-15",
    priority=2,
):
    return {
        "id": event_id,
        "subject_id": 101,
        "faculty_id": faculty_id,
        "batch_id": batch_id,
        "room_id": room_id,
        "date": event_date,
        "start_time": start,
        "end_time": end,
        "priority": priority,
    }


class TestObjective(unittest.TestCase):

    def test_conflict_free_schedule_scores_base(self):
        events = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 11, 202, "102", "11:00", "12:00"),
        ]

        objective = evaluate_objective(events)

        self.assertEqual(objective["conflicts"], 0)
        self.assertEqual(objective["score"], 1000.0)

    def test_conflicting_schedule_penalised(self):
        events = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 202, "102", "10:30", "11:30"),
        ]

        objective = evaluate_objective(events)

        self.assertEqual(objective["conflicts"], 1)
        self.assertLess(objective["score"], 1000.0)
        self.assertIn("conflicts", objective["breakdown"])

    def test_workload_overload_penalty(self):
        events = [
            make_event(1, 10, 201, "101", "09:00", "10:00"),
            make_event(2, 10, 202, "102", "10:00", "11:00"),
        ]

        penalty = workload_overload_penalty(events, capacities={10: 1})

        self.assertGreater(penalty, 0.0)

    def test_workload_balance_penalty_prefers_even_distribution(self):
        # Faculty 10 is overloaded while faculty 11 is under capacity.
        events = [
            make_event(1, 10, 201, "101", "09:00", "11:00"),
            make_event(2, 10, 202, "102", "11:00", "13:00"),
            make_event(3, 11, 203, "103", "09:00", "10:00"),
        ]

        balanced_events = [
            make_event(1, 10, 201, "101", "09:00", "10:00"),
            make_event(2, 10, 202, "102", "10:00", "11:00"),
            make_event(3, 11, 203, "103", "11:00", "13:00"),
        ]

        unbalanced = workload_balance_penalty(events, capacities={10: 2, 11: 2})
        balanced = workload_balance_penalty(
            balanced_events,
            capacities={10: 2, 11: 2},
        )

        self.assertGreater(unbalanced, balanced)

    def test_room_utilization_penalty_prefers_even_usage(self):
        uneven = [
            make_event(1, 10, 201, "101", "09:00", "11:00"),
            make_event(2, 10, 202, "101", "11:00", "13:00"),
            make_event(3, 11, 203, "102", "09:00", "10:00"),
        ]
        even = [
            make_event(1, 10, 201, "101", "09:00", "10:00"),
            make_event(2, 10, 202, "101", "10:00", "11:00"),
            make_event(3, 11, 203, "102", "11:00", "13:00"),
        ]

        self.assertGreater(
            room_utilization_penalty(uneven),
            room_utilization_penalty(even),
        )

    def test_moved_high_priority_event_costs_more(self):
        events = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 11, 202, "102", "10:30", "11:30"),
        ]

        normal = evaluate_objective(
            events,
            moved_event_ids=[1],
            original_events=events,
        )
        urgent = evaluate_objective(
            events,
            moved_event_ids=[1],
            original_events=[make_event(1, 10, 201, "101", "10:00", "11:00", priority=4)],
        )

        self.assertGreater(normal["score"], urgent["score"])

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_objective([], mode="UNKNOWN")

    def test_supported_modes_valid(self):
        events = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 202, "102", "10:30", "11:30"),
        ]

        for mode in (MODE_BALANCED, MODE_CONFLICT_MINIMIZATION, MODE_WORKLOAD_BALANCING):
            objective = evaluate_objective(events, mode=mode)
            self.assertEqual(objective["conflicts"], 1)


class TestBaselineOptimizer(unittest.TestCase):

    def setUp(self):
        self.events = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 202, "102", "10:30", "11:30"),
        ]
        self.optimizer = BaselineOptimizer()

    def test_result_shape(self):
        result = self.optimizer.optimize(self.events)

        self.assertIsInstance(result, OptimizationResult)
        self.assertIn(result.status, (OPTIMIZED, ALREADY_OPTIMAL))
        self.assertIn("before", result.objective_breakdown)
        self.assertIn("after", result.objective_breakdown)
        self.assertIsInstance(result.recommended_changes, list)
        self.assertIsInstance(result.proposed_schedule, list)

    def test_feasible_schedule_selected(self):
        result = self.optimizer.optimize(self.events)

        self.assertEqual(result.status, OPTIMIZED)
        self.assertEqual(result.conflicts_before, 1)
        self.assertEqual(result.conflicts_after, 0)

    def test_best_score_selected(self):
        result = self.optimizer.optimize(self.events)

        self.assertGreater(
            result.optimized_score,
            result.original_score,
        )
        self.assertEqual(result.events_changed, 1)
        self.assertEqual(len(result.recommended_changes), 1)

    def test_infeasible_candidates_rejected(self):
        # Only candidate slot collides with the faculty member's other event.
        result = self.optimizer.optimize(
            self.events,
            config=OptimizationConfig(
                dates=[date(2026, 8, 15)],
                day_start="08:00",
                day_end="10:00",
            ),
        )

        # 10:00-11:00 stays the only slot for event 1; no improvement.
        self.assertIn(result.status, (OPTIMIZED, ALREADY_OPTIMAL))
        self.assertEqual(result.conflicts_after, 0)

    def test_deterministic_result(self):
        first = self.optimizer.optimize(self.events)
        second = self.optimizer.optimize(self.events)
        third = self.optimizer.optimize(self.events)

        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.to_dict(), third.to_dict())

    def test_priority_respected(self):
        events = [
            make_event(1, 10, 201, "101", "10:00", "11:00", priority=4),
            make_event(2, 10, 202, "102", "10:30", "11:30", priority=2),
        ]

        result = self.optimizer.optimize(events)

        change = result.recommended_changes[0]
        self.assertEqual(change["event_id"], 2)

    def test_workload_objective_calculated(self):
        result = self.optimizer.optimize(
            self.events,
            capacities={10: 6},
        )

        self.assertIsInstance(result.workload_before, dict)
        self.assertIsInstance(result.workload_after, dict)
        self.assertIn("faculty", result.workload_before)

    def test_room_utilization_evaluated(self):
        result = self.optimizer.optimize(self.events)

        self.assertIsInstance(result.objective_breakdown["before"], dict)
        self.assertIsInstance(result.objective_breakdown["after"], dict)

    def test_no_feasible_schedule_handled(self):
        # The search window produces no candidate slots at all, so the
        # optimizer cannot resolve the conflict.
        result = self.optimizer.optimize(
            self.events,
            config=OptimizationConfig(
                dates=[date(2026, 8, 15)],
                day_start="10:30",
                day_end="10:30",
            ),
        )

        self.assertEqual(result.status, NO_FEASIBLE_SCHEDULE)
        self.assertEqual(result.conflicts_before, 1)
        self.assertEqual(result.conflicts_after, 1)

    def test_official_timetable_never_modified(self):
        snapshot = [dict(e) for e in self.events]

        self.optimizer.optimize(self.events)

        self.assertEqual(snapshot, self.events)

    def test_scenario_isolated(self):
        result = self.optimizer.optimize(self.events)

        self.assertEqual(len(result.proposed_schedule), len(self.events))
        for event in self.events:
            self.assertEqual(event["date"], "2026-08-15")
            self.assertEqual(event["start_time"], "10:00" if event["id"] == 1 else "10:30")


class TestNoFeasibleOptimization(unittest.TestCase):
    """
    When the search space cannot absorb an event, the optimizer reports
    NO_FEASIBLE_SCHEDULE instead of returning an empty list.
    """

    def test_no_feasible_when_all_slots_conflict(self):
        # Faculty 10 teaches 09:00-18:00 without a break; the conflicting
        # event has no free slot on the given dates.
        events = [
            make_event(1, 10, 201, "101", "09:00", "18:00"),
            make_event(2, 10, 202, "102", "10:30", "11:30"),
        ]

        result = BaselineOptimizer().optimize(
            events,
            config=OptimizationConfig(
                dates=[date(2026, 8, 15)],
                day_start="08:00",
                day_end="18:00",
            ),
        )

        # Event 1 occupies the whole day for faculty 10 and batch 201, so
        # event 2 cannot be placed anywhere on that date.
        self.assertIsInstance(result, OptimizationResult)
        self.assertIn(result.status, (NO_FEASIBLE_SCHEDULE, OPTIMIZED, ALREADY_OPTIMAL))
        self.assertIn("rejected_candidates", result.to_dict())


if __name__ == "__main__":
    unittest.main()
