import unittest

from app.scheduling.rescheduler import find_available_slots


class TestRescheduler(unittest.TestCase):

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
            }
        ]

    def test_available_slot(self):
        candidate_slots = [
            {
                "date": "2026-08-15",
                "start_time": "11:00",
                "end_time": "12:00",
            }
        ]

        result = find_available_slots(
            self.events,
            faculty_id=10,
            batch_id=201,
            room_id=5,
            candidate_slots=candidate_slots,
        )

        self.assertEqual(result, candidate_slots)

    def test_faculty_conflict_rejects_slot(self):
        candidate_slots = [
            {
                "date": "2026-08-15",
                "start_time": "10:30",
                "end_time": "11:30",
            }
        ]

        result = find_available_slots(
            self.events,
            faculty_id=10,
            batch_id=202,
            room_id=6,
            candidate_slots=candidate_slots,
        )

        self.assertEqual(result, [])

    def test_batch_conflict_rejects_slot(self):
        candidate_slots = [
            {
                "date": "2026-08-15",
                "start_time": "10:30",
                "end_time": "11:30",
            }
        ]

        result = find_available_slots(
            self.events,
            faculty_id=11,
            batch_id=201,
            room_id=6,
            candidate_slots=candidate_slots,
        )

        self.assertEqual(result, [])

    def test_room_conflict_rejects_slot(self):
        candidate_slots = [
            {
                "date": "2026-08-15",
                "start_time": "10:30",
                "end_time": "11:30",
            }
        ]

        result = find_available_slots(
            self.events,
            faculty_id=11,
            batch_id=202,
            room_id=5,
            candidate_slots=candidate_slots,
        )

        self.assertEqual(result, [])

    def test_different_date_is_available(self):
        candidate_slots = [
            {
                "date": "2026-08-16",
                "start_time": "10:00",
                "end_time": "11:00",
            }
        ]

        result = find_available_slots(
            self.events,
            faculty_id=10,
            batch_id=201,
            room_id=5,
            candidate_slots=candidate_slots,
        )

        self.assertEqual(result, candidate_slots)


if __name__ == "__main__":
    unittest.main()