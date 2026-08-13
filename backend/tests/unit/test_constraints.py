import unittest

from app.scheduling.constraints import (
    validate_event,
    is_slot_valid,
)


class TestConstraints(unittest.TestCase):

    def test_valid_event(self):
        event = {
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

        self.assertEqual(validate_event(event), [])

    def test_missing_required_field(self):
        event = {
            "id": 1,
            "subject_id": 101,
            "faculty_id": 10,
            "batch_id": 201,
            "room_id": 5,
            "date": "2026-08-15",
            "start_time": "10:00",
            "end_time": "11:00",
        }

        errors = validate_event(event)

        self.assertIn("Missing required field: priority", errors)

    def test_invalid_time_range(self):
        event = {
            "id": 1,
            "subject_id": 101,
            "faculty_id": 10,
            "batch_id": 201,
            "room_id": 5,
            "date": "2026-08-15",
            "start_time": "12:00",
            "end_time": "10:00",
            "priority": "normal",
        }

        errors = validate_event(event)

        self.assertIn(
            "start_time must be earlier than end_time",
            errors,
        )

    def test_invalid_priority(self):
        event = {
            "id": 1,
            "subject_id": 101,
            "faculty_id": 10,
            "batch_id": 201,
            "room_id": 5,
            "date": "2026-08-15",
            "start_time": "10:00",
            "end_time": "11:00",
            "priority": "critical",
        }

        errors = validate_event(event)

        self.assertIn(
            "Invalid priority: critical",
            errors,
        )

    def test_valid_slot(self):
        self.assertTrue(
            is_slot_valid("10:00", "11:00")
        )

    def test_invalid_slot(self):
        self.assertFalse(
            is_slot_valid("11:00", "10:00")
        )

    def test_equal_start_and_end_time(self):
        self.assertFalse(
            is_slot_valid("10:00", "10:00")
        )


if __name__ == "__main__":
    unittest.main()