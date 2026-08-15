import unittest

from app.scheduling.comparison import compare_schedules


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


class TestScheduleComparison(unittest.TestCase):

    def setUp(self):
        self.current = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 202, "102", "10:30", "11:30"),
            make_event(3, 11, 203, "103", "11:00", "12:00"),
        ]

    def test_identical_schedules_all_unchanged(self):
        comparison = compare_schedules(self.current, self.current)

        self.assertEqual(comparison["events"]["total"], 3)
        self.assertEqual(comparison["events"]["unchanged"], 3)
        self.assertEqual(comparison["events"]["moved"], 0)
        self.assertEqual(comparison["events"]["added"], 0)
        self.assertEqual(comparison["events"]["removed"], 0)

    def test_moved_events_detected(self):
        proposed = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 202, "102", "12:00", "13:00"),
            make_event(3, 11, 203, "103", "11:00", "12:00"),
        ]

        comparison = compare_schedules(self.current, proposed)

        self.assertEqual(comparison["events"]["unchanged"], 2)
        self.assertEqual(comparison["events"]["moved"], 1)
        self.assertEqual(comparison["events"]["added"], 0)
        self.assertEqual(comparison["events"]["removed"], 0)

    def test_added_and_removed_detected(self):
        proposed = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 202, "102", "10:30", "11:30"),
            make_event(9, 12, 204, "104", "13:00", "14:00"),
        ]

        comparison = compare_schedules(self.current, proposed)

        self.assertEqual(comparison["events"]["added"], 1)
        self.assertEqual(comparison["events"]["removed"], 1)

    def test_conflicts_before_after(self):
        proposed = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 202, "102", "12:00", "13:00"),
            make_event(3, 11, 203, "103", "11:00", "12:00"),
        ]

        comparison = compare_schedules(self.current, proposed)

        self.assertEqual(comparison["conflicts"]["before"], 1)
        self.assertEqual(comparison["conflicts"]["after"], 0)

    def test_workload_before_after(self):
        comparison = compare_schedules(self.current, self.current)

        self.assertIn("workload", comparison)
        self.assertIn("before", comparison["workload"])
        self.assertIn("after", comparison["workload"])
        self.assertIn("faculty", comparison["workload"]["before"])

    def test_objective_score_comparison(self):
        proposed = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 202, "102", "12:00", "13:00"),
            make_event(3, 11, 203, "103", "11:00", "12:00"),
        ]

        comparison = compare_schedules(self.current, proposed)

        self.assertGreater(comparison["objective"]["after"], comparison["objective"]["before"])


if __name__ == "__main__":
    unittest.main()
