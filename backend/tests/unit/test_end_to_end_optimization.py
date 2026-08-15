import unittest
from datetime import date

from app.scheduling.comparison import compare_schedules
from app.scheduling.optimizer import BaselineOptimizer, OptimizationConfig, OPTIMIZED


class TestEndToEndOptimizationScenario(unittest.TestCase):
    """
    End-to-end optimization scenario from the Day 4 task document:

    Faculty A, B
    Batch CSE-4A
    Rooms 101, 102
    Events E1, E2, E3 with overlapping time slots.

    Flow: current timetable -> conflict detection -> candidate generation
    -> constraint filtering -> optimization -> best feasible schedule.
    """

    def setUp(self):
        self.day = date(2026, 9, 21)

        self.faculty_a = 1
        self.faculty_b = 2
        self.batch_cse4a = 10

        self.events = [
            {
                "id": 1,
                "subject_id": 1,
                "faculty_id": self.faculty_a,
                "batch_id": self.batch_cse4a,
                "room_id": "101",
                "date": self.day.isoformat(),
                "start_time": "10:00",
                "end_time": "11:00",
                "priority": 2,
            },
            {
                "id": 2,
                "subject_id": 2,
                "faculty_id": self.faculty_a,
                "batch_id": self.batch_cse4a,
                "room_id": "102",
                "date": self.day.isoformat(),
                "start_time": "10:30",
                "end_time": "11:30",
                "priority": 2,
            },
            {
                "id": 3,
                "subject_id": 3,
                "faculty_id": self.faculty_b,
                "batch_id": self.batch_cse4a,
                "room_id": "101",
                "date": self.day.isoformat(),
                "start_time": "11:00",
                "end_time": "12:00",
                "priority": 2,
            },
        ]

    def test_conflicts_before_greater_than_zero(self):
        optimizer = BaselineOptimizer()
        result = optimizer.optimize(self.events)

        self.assertGreater(result.conflicts_before, 0)

    def test_conflicts_after_zero(self):
        optimizer = BaselineOptimizer()
        result = optimizer.optimize(self.events)

        self.assertEqual(result.conflicts_after, 0)

    def test_best_feasible_schedule_selected(self):
        optimizer = BaselineOptimizer()
        result = optimizer.optimize(self.events)

        self.assertEqual(result.status, OPTIMIZED)
        self.assertGreaterEqual(result.optimized_score, result.original_score)

    def test_proposed_schedule_is_conflict_free(self):
        optimizer = BaselineOptimizer()
        result = optimizer.optimize(self.events)

        comparison = compare_schedules(self.events, result.proposed_schedule)

        self.assertEqual(comparison["conflicts"]["after"], 0)

    def test_official_timetable_unchanged(self):
        snapshot = [dict(event) for event in self.events]

        optimizer = BaselineOptimizer()
        optimizer.optimize(self.events)

        self.assertEqual(snapshot, self.events)

    def test_candidate_search_boundaries_respected(self):
        config = OptimizationConfig(
            dates=[self.day],
            day_start="08:00",
            day_end="18:00",
            slot_minutes=60,
        )

        optimizer = BaselineOptimizer()
        result = optimizer.optimize(self.events, config=config)

        for change in result.recommended_changes:
            self.assertEqual(change["from"]["date"], self.day.isoformat())
            self.assertEqual(change["to"]["date"], self.day.isoformat())
            self.assertGreaterEqual(change["to"]["start_time"], "08:00")


if __name__ == "__main__":
    unittest.main()
