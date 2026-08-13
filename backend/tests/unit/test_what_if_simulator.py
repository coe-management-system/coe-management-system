import unittest

from backend.app.scheduling.what_if_simulator import simulate_event_change


class TestWhatIfSimulator(unittest.TestCase):

    def setUp(self):
        self.events = [
            {
                "id": 1,
                "subject_id": 101,
                "faculty_id": 10,
                "batch_id": 201,
                "room_id": 5,
                "date": "2026-08-15",
                "start_time": "10:00",
                "end_time": "11:00",
                "priority": "normal",
            },
            {
                "id": 2,
                "subject_id": 102,
                "faculty_id": 10,
                "batch_id": 202,
                "room_id": 6,
                "date": "2026-08-15",
                "start_time": "11:00",
                "end_time": "12:00",
                "priority": "normal",
            },
        ]

    def test_successful_simulation(self):
        result = simulate_event_change(
            self.events,
            event_id=1,
            changes={
                "start_time": "14:00",
                "end_time": "15:00",
            },
        )

        self.assertFalse(result["has_conflict"])
        self.assertEqual(result["conflicts"], [])
        self.assertEqual(
            result["simulated_event"]["start_time"],
            "14:00",
        )

    def test_conflicting_simulation(self):
        result = simulate_event_change(
            self.events,
            event_id=1,
            changes={
                "start_time": "11:00",
                "end_time": "12:00",
            },
        )

        self.assertTrue(result["has_conflict"])
        self.assertEqual(len(result["conflicts"]), 1)
        self.assertEqual(result["conflicts"][0]["type"], "faculty")

    def test_original_events_are_not_modified(self):
        simulate_event_change(
            self.events,
            event_id=1,
            changes={
                "start_time": "14:00",
                "end_time": "15:00",
            },
        )

        self.assertEqual(self.events[0]["start_time"], "10:00")
        self.assertEqual(self.events[0]["end_time"], "11:00")

    def test_nonexistent_event(self):
        with self.assertRaises(ValueError):
            simulate_event_change(
                self.events,
                event_id=999,
                changes={
                    "start_time": "14:00",
                    "end_time": "15:00",
                },
            )


if __name__ == "__main__":
    unittest.main()