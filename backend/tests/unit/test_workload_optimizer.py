import unittest

from backend.app.scheduling.workload_optimizer import (
    calculate_event_duration,
    calculate_faculty_workload,
)


class TestWorkloadOptimizer(unittest.TestCase):

    def test_calculate_event_duration(self):
        event = {
            "id": 1,
            "start_time": "10:00",
            "end_time": "12:30",
        }

        duration = calculate_event_duration(event)

        self.assertEqual(duration, 2.5)

    def test_calculate_faculty_workload(self):
        events = [
            {
                "id": 1,
                "subject_id": 101,
                "faculty_id": 10,
                "batch_id": 201,
                "room_id": 5,
                "date": "2026-08-15",
                "start_time": "10:00",
                "end_time": "12:00",
                "priority": "normal",
            },
            {
                "id": 2,
                "subject_id": 102,
                "faculty_id": 10,
                "batch_id": 202,
                "room_id": 6,
                "date": "2026-08-15",
                "start_time": "13:00",
                "end_time": "16:00",
                "priority": "normal",
            },
            {
                "id": 3,
                "subject_id": 103,
                "faculty_id": 11,
                "batch_id": 203,
                "room_id": 7,
                "date": "2026-08-15",
                "start_time": "10:00",
                "end_time": "12:00",
                "priority": "normal",
            },
        ]

        result = calculate_faculty_workload(events, 10)

        self.assertEqual(result["faculty_id"], 10)
        self.assertEqual(result["allocated_hours"], 5.0)

    def test_faculty_with_no_events(self):
        result = calculate_faculty_workload([], 10)

        self.assertEqual(
            result,
            {
                "faculty_id": 10,
                "allocated_hours": 0,
            },
        )

    def test_invalid_time_range(self):
        event = {
            "id": 1,
            "start_time": "12:00",
            "end_time": "10:00",
        }

        with self.assertRaises(ValueError):
            calculate_event_duration(event)


if __name__ == "__main__":
    unittest.main()