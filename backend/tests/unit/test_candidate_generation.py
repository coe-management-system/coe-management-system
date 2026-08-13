import unittest

from app.scheduling.rescheduler import evaluate_candidate_slots


class TestCandidateGeneration(unittest.TestCase):

    def setUp(self):
        self.events = [
            {
                "id": 1,
                "subject_id": 101,
                "faculty_id": 10,
                "batch_id": 201,
                "room_id": "101",
                "date": "2026-08-15",
                "start_time": "10:00",
                "end_time": "11:00",
                "priority": 2,
            }
        ]

    def test_feasible_candidate(self):
        candidates = [
            {
                "date": "2026-08-15",
                "start_time": "11:00",
                "end_time": "12:00",
            }
        ]

        result = evaluate_candidate_slots(
            self.events,
            faculty_id=10,
            batch_id=202,
            room_id="102",
            candidate_slots=candidates,
        )

        self.assertEqual(result[0]["status"], "feasible")
        self.assertEqual(result[0]["reasons"], [])

    def test_faculty_conflict(self):
        candidates = [
            {
                "date": "2026-08-15",
                "start_time": "10:30",
                "end_time": "11:30",
            }
        ]

        result = evaluate_candidate_slots(
            self.events,
            faculty_id=10,
            batch_id=202,
            room_id="102",
            candidate_slots=candidates,
        )

        self.assertEqual(result[0]["status"], "rejected")
        self.assertTrue(
            any("Faculty 10" in reason for reason in result[0]["reasons"])
        )

    def test_batch_conflict(self):
        candidates = [
            {
                "date": "2026-08-15",
                "start_time": "10:30",
                "end_time": "11:30",
            }
        ]

        result = evaluate_candidate_slots(
            self.events,
            faculty_id=11,
            batch_id=201,
            room_id="102",
            candidate_slots=candidates,
        )

        self.assertEqual(result[0]["status"], "rejected")
        self.assertTrue(
            any("Batch 201" in reason for reason in result[0]["reasons"])
        )

    def test_room_conflict(self):
        candidates = [
            {
                "date": "2026-08-15",
                "start_time": "10:30",
                "end_time": "11:30",
            }
        ]

        result = evaluate_candidate_slots(
            self.events,
            faculty_id=11,
            batch_id=202,
            room_id="101",
            candidate_slots=candidates,
        )

        self.assertEqual(result[0]["status"], "rejected")
        self.assertTrue(
            any("Room 101" in reason for reason in result[0]["reasons"])
        )

    def test_invalid_time_range(self):
        candidates = [
            {
                "date": "2026-08-15",
                "start_time": "12:00",
                "end_time": "11:00",
            }
        ]

        result = evaluate_candidate_slots(
            self.events,
            faculty_id=11,
            batch_id=202,
            room_id="102",
            candidate_slots=candidates,
        )

        self.assertEqual(result[0]["status"], "rejected")
        self.assertTrue(
            any(
                "invalid time range" in reason.lower()
                for reason in result[0]["reasons"]
            )
        )


if __name__ == "__main__":
    unittest.main()