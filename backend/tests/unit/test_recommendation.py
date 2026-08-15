import unittest

from app.scheduling.recommendation import (
    NO_FEASIBLE_SLOT,
    recommend_reschedule,
)


def make_event(event_id, faculty_id, batch_id, room_id, start, end, priority=2):
    return {
        "id": event_id,
        "subject_id": 1,
        "faculty_id": faculty_id,
        "batch_id": batch_id,
        "room_id": room_id,
        "date": "2026-08-15",
        "start_time": start,
        "end_time": end,
        "priority": priority,
    }


class TestRecommendation(unittest.TestCase):

    def setUp(self):
        # Event 1 and event 2 conflict (same faculty at overlapping times).
        self.events = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 202, "102", "10:30", "11:30"),
        ]

    def test_recommendation_generated(self):
        candidates = [
            {"date": "2026-08-15", "start_time": "11:30", "end_time": "12:30"},
            {"date": "2026-08-15", "start_time": "14:00", "end_time": "15:00"},
        ]

        result = recommend_reschedule(
            self.events,
            event_id=1,
            candidates=candidates,
        )

        self.assertEqual(result["status"], "recommendation")
        self.assertEqual(result["event_id"], 1)
        self.assertIn("recommended", result)
        self.assertIn("reason", result)
        self.assertGreater(result["feasible_count"], 0)

    def test_recommendation_is_feasible(self):
        candidates = [
            {"date": "2026-08-15", "start_time": "11:30", "end_time": "12:30"},
            {"date": "2026-08-15", "start_time": "14:00", "end_time": "15:00"},
        ]

        result = recommend_reschedule(
            self.events,
            event_id=1,
            candidates=candidates,
        )

        recommended = result["recommended"]

        # The recommended slot must not overlap the conflicting event 2.
        self.assertFalse(
            _overlaps(
                recommended["start_time"],
                recommended["end_time"],
                "10:30",
                "11:30",
            )
        )
        self.assertGreater(result["score"], 0)

    def test_recommendation_is_deterministic(self):
        candidates = [
            {"date": "2026-08-15", "start_time": "14:00", "end_time": "15:00"},
            {"date": "2026-08-15", "start_time": "11:30", "end_time": "12:30"},
        ]

        first = recommend_reschedule(
            self.events,
            event_id=1,
            candidates=candidates,
        )
        second = recommend_reschedule(
            self.events,
            event_id=1,
            candidates=candidates,
        )

        self.assertEqual(first, second)

    def test_recommendation_explains_selection(self):
        candidates = [
            {"date": "2026-08-15", "start_time": "14:00", "end_time": "15:00"},
        ]

        result = recommend_reschedule(
            self.events,
            event_id=1,
            candidates=candidates,
        )

        reason = result["reason"]

        self.assertIn("no faculty conflict", reason)
        self.assertIn("no batch conflict", reason)
        self.assertIn("no room conflict", reason)

    def test_no_feasible_recommendation_handled(self):
        # The only candidate overlaps event 1 on the same faculty, batch,
        # and room, so event 2 has no feasible slot.
        events = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 201, "101", "11:00", "12:00"),
        ]

        candidates = [
            {"date": "2026-08-15", "start_time": "10:00", "end_time": "11:00"},
        ]

        result = recommend_reschedule(
            events,
            event_id=2,
            candidates=candidates,
        )

        self.assertEqual(result["status"], NO_FEASIBLE_SLOT)
        self.assertIn("reasons", result)
        self.assertTrue(result["reasons"])
        self.assertIn("No feasible time slot", result["message"])

    def test_no_feasible_when_all_rooms_occupied(self):
        events = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 201, "101", "11:00", "12:00"),
        ]

        # Only candidate collides with event 1 on room, faculty, and batch.
        candidates = [
            {"date": "2026-08-15", "start_time": "10:00", "end_time": "11:00"},
        ]

        result = recommend_reschedule(
            events,
            event_id=2,
            candidates=candidates,
        )

        self.assertEqual(result["status"], NO_FEASIBLE_SLOT)
        self.assertIn("reasons", result)

    def test_missing_event_raises(self):
        with self.assertRaises(ValueError):
            recommend_reschedule(
                self.events,
                event_id=999,
                candidates=[
                    {"date": "2026-08-15", "start_time": "14:00", "end_time": "15:00"}
                ],
            )

    def test_original_timetable_not_modified(self):
        before = [dict(event) for event in self.events]

        recommend_reschedule(
            self.events,
            event_id=1,
            candidates=[
                {"date": "2026-08-15", "start_time": "14:00", "end_time": "15:00"}
            ],
        )

        self.assertEqual(self.events, before)


def _overlaps(start_a, end_a, start_b, end_b):
    return start_a < end_b and start_b < end_a


if __name__ == "__main__":
    unittest.main()