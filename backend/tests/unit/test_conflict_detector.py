import unittest

from backend.app.scheduling.conflict_detector import detect_conflicts


class TestConflictDetector(unittest.TestCase):

    def test_faculty_conflict(self):
        events = [
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
                "start_time": "10:30",
                "end_time": "11:30",
                "priority": "normal",
            },
        ]

        conflicts = detect_conflicts(events)

        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["type"], "faculty")

    def test_no_conflict_when_events_touch(self):
        events = [
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

        conflicts = detect_conflicts(events)

        self.assertEqual(conflicts, [])

    def test_batch_conflict(self):
        events = [
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
                "faculty_id": 11,
                "batch_id": 201,
                "room_id": 6,
                "date": "2026-08-15",
                "start_time": "10:30",
                "end_time": "11:30",
                "priority": "normal",
            },
        ]

        conflicts = detect_conflicts(events)

        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["type"], "batch")

    def test_room_conflict(self):
        events = [
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
                "faculty_id": 11,
                "batch_id": 202,
                "room_id": 5,
                "date": "2026-08-15",
                "start_time": "10:30",
                "end_time": "11:30",
                "priority": "normal",
            },
        ]

        conflicts = detect_conflicts(events)

        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["type"], "room")


if __name__ == "__main__":
    unittest.main()