import unittest

from app.scheduling.what_if_simulator import simulate_scenario


def make_event(event_id, faculty_id, batch_id, room_id, start, end, date="2026-08-15"):
    return {
        "id": event_id,
        "subject_id": 1,
        "faculty_id": faculty_id,
        "batch_id": batch_id,
        "room_id": room_id,
        "date": date,
        "start_time": start,
        "end_time": end,
        "priority": 2,
    }


class TestWhatIfScenarios(unittest.TestCase):

    def setUp(self):
        self.events = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 202, "102", "11:00", "12:00"),
        ]

    def test_scenario_creates_conflict(self):
        # Faculty 10 becomes unavailable during event 2's time.
        scenario = {
            "type": "faculty_unavailable",
            "resource": 10,
            "date": "2026-08-15",
            "start_time": "10:00",
            "end_time": "12:00",
        }

        result = simulate_scenario(self.events, scenario)

        self.assertTrue(result["has_conflict"])
        self.assertTrue(result["conflicts"])
        self.assertTrue(result["affected_events"])

    def test_scenario_removes_conflict(self):
        # Event 1 is moved away from event 2, removing the faculty conflict.
        scenario = {
            "type": "event_change",
            "event_id": 1,
            "changes": {
                "start_time": "14:00",
                "end_time": "15:00",
            },
        }

        result = simulate_scenario(self.events, scenario)

        self.assertFalse(result["has_conflict"])
        self.assertEqual(result["conflicts"], [])

    def test_workload_impact_calculated(self):
        scenario = {
            "type": "faculty_unavailable",
            "resource": 10,
            "date": "2026-08-15",
            "start_time": "10:00",
            "end_time": "12:00",
        }

        result = simulate_scenario(
            self.events,
            scenario,
            capacities={10: 6, 11: 6},
        )

        self.assertTrue(result["workload_impact"])
        for impact in result["workload_impact"]:
            self.assertIn("projected_hours", impact)
            self.assertIn("status", impact)

    def test_room_unavailable_identifies_affected(self):
        scenario = {
            "type": "room_unavailable",
            "resource": "101",
            "date": "2026-08-15",
            "start_time": "10:00",
            "end_time": "11:00",
        }

        result = simulate_scenario(self.events, scenario)

        affected_ids = [e["id"] for e in result["affected_events"]]
        self.assertIn(1, affected_ids)
        self.assertIn(1, result["candidate_replacements"])

    def test_original_timetable_unchanged(self):
        before = [dict(event) for event in self.events]

        simulate_scenario(
            self.events,
            {
                "type": "faculty_unavailable",
                "resource": 10,
                "date": "2026-08-15",
                "start_time": "10:00",
                "end_time": "12:00",
            },
        )

        self.assertEqual(self.events, before)

    def test_timetable_unchanged_flag_always_true(self):
        result = simulate_scenario(
            self.events,
            {
                "type": "room_unavailable",
                "resource": "101",
                "date": "2026-08-15",
                "start_time": "10:00",
                "end_time": "11:00",
            },
        )

        self.assertTrue(result["timetable_unchanged"])

    def test_unsupported_scenario_raises(self):
        with self.assertRaises(ValueError):
            simulate_scenario(
                self.events,
                {"type": "unsupported", "resource": 1},
            )


if __name__ == "__main__":
    unittest.main()