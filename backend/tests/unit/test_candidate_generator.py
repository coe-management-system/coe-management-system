import unittest

from app.scheduling.candidate_generator import (
    build_candidate,
    evaluate_candidates,
    generate_candidates,
    generate_slots,
)


def make_event(event_id=1, faculty_id=10, batch_id=201, room_id="101", priority=2):
    return {
        "id": event_id,
        "subject_id": 101,
        "faculty_id": faculty_id,
        "batch_id": batch_id,
        "room_id": room_id,
        "date": "2026-08-15",
        "start_time": "10:00",
        "end_time": "11:00",
        "priority": priority,
    }


class TestCandidateGenerator(unittest.TestCase):

    def setUp(self):
        # Event 3 is the event being rescheduled; events 1 and 2 occupy
        # 10:00-11:00 on the same date.
        self.events = [
            make_event(event_id=1, faculty_id=10, batch_id=201, room_id="101"),
            make_event(event_id=2, faculty_id=11, batch_id=202, room_id="102"),
        ]
        self.event = make_event(
            event_id=3,
            faculty_id=10,
            batch_id=203,
            room_id="103",
        )

    def test_feasible_candidate(self):
        candidates = [
            {"date": "2026-08-15", "start_time": "11:00", "end_time": "12:00"}
        ]

        result = evaluate_candidates(self.events, self.event, candidates)

        self.assertEqual(result[0]["status"], "FEASIBLE")
        self.assertEqual(result[0]["reasons"], [])

    def test_candidate_rejected_by_faculty(self):
        candidates = [
            {"date": "2026-08-15", "start_time": "10:30", "end_time": "11:30"}
        ]

        result = evaluate_candidates(self.events, self.event, candidates)

        self.assertEqual(result[0]["status"], "REJECTED")
        self.assertTrue(any("Faculty 10" in r for r in result[0]["reasons"]))

    def test_candidate_rejected_by_batch(self):
        candidate_event = {
            **self.event,
            "faculty_id": 11,
            "room_id": "102",
            "batch_id": 201,
        }

        candidates = [
            {"date": "2026-08-15", "start_time": "10:30", "end_time": "11:30"}
        ]

        result = evaluate_candidates(self.events, candidate_event, candidates)

        self.assertEqual(result[0]["status"], "REJECTED")
        self.assertTrue(any("Batch 201" in r for r in result[0]["reasons"]))

    def test_candidate_rejected_by_room(self):
        candidate_event = {
            **self.event,
            "faculty_id": 12,
            "batch_id": 204,
            "room_id": "101",
        }

        candidates = [
            {"date": "2026-08-15", "start_time": "10:30", "end_time": "11:30"}
        ]

        result = evaluate_candidates(self.events, candidate_event, candidates)

        self.assertEqual(result[0]["status"], "REJECTED")
        self.assertTrue(any("Room 101" in r for r in result[0]["reasons"]))

    def test_candidate_rejected_by_workload(self):
        candidate_event = {
            **self.event,
            "faculty_id": 12,
            "batch_id": 204,
            "room_id": "104",
        }

        candidates = [
            {"date": "2026-08-15", "start_time": "11:00", "end_time": "14:00"}
        ]

        result = evaluate_candidates(
            self.events,
            candidate_event,
            candidates,
            capacities={12: 2},
            hard_capacities={12: 2},
        )

        self.assertEqual(result[0]["status"], "REJECTED")
        self.assertTrue(any("workload" in r.lower() for r in result[0]["reasons"]))

    def test_invalid_time_rejected(self):
        candidates = [
            {"date": "2026-08-15", "start_time": "12:00", "end_time": "11:00"}
        ]

        result = evaluate_candidates(
            self.events,
            {**self.event, "faculty_id": 12, "batch_id": 204, "room_id": "104"},
            candidates,
        )

        self.assertEqual(result[0]["status"], "REJECTED")
        self.assertTrue(
            any("invalid time range" in r.lower() for r in result[0]["reasons"])
        )

    def test_all_candidates_rejected(self):
        candidates = [
            {"date": "2026-08-15", "start_time": "10:30", "end_time": "11:30"}
        ]

        result = evaluate_candidates(self.events, self.event, candidates)

        self.assertEqual(result[0]["status"], "REJECTED")
        self.assertTrue(result[0]["reasons"])

    def test_generate_slots_is_deterministic(self):
        slots_1 = generate_slots(["2026-08-15"])
        slots_2 = generate_slots(["2026-08-15"])

        self.assertEqual(slots_1, slots_2)
        self.assertGreater(len(slots_1), 0)

    def test_generate_candidates_returns_evaluations(self):
        result = generate_candidates(
            self.events,
            self.event,
            dates=["2026-08-16"],
        )

        self.assertGreater(len(result), 0)
        self.assertTrue(all("status" in c for c in result))
        self.assertTrue(any(c["status"] == "FEASIBLE" for c in result))

    def test_build_candidate_combines_event_and_slot(self):
        candidate = build_candidate(
            self.event,
            {"date": "2026-08-16", "start_time": "09:00", "end_time": "10:00"},
        )

        self.assertEqual(candidate["event_id"], 3)
        self.assertEqual(candidate["faculty_id"], 10)
        self.assertEqual(candidate["room_id"], "103")
        self.assertEqual(candidate["date"], "2026-08-16")
        self.assertEqual(candidate["start_time"], "09:00")


if __name__ == "__main__":
    unittest.main()