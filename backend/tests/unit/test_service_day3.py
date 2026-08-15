import unittest
from datetime import date

from app.scheduling.domain import SchedulingEvent
from app.scheduling.service import SchedulingService


def make_event(event_id, faculty_id, batch_id, room_id, start, end, priority=2):
    return SchedulingEvent(
        id=event_id,
        subject_id=101,
        faculty_id=faculty_id,
        batch_id=batch_id,
        room_id=room_id,
        date=date(2026, 8, 15),
        start_time=start,
        end_time=end,
        priority=priority,
    )


class TestSchedulingServiceDay3(unittest.TestCase):

    def setUp(self):
        self.events = [
            make_event(1, 10, 201, "101", "10:00", "11:00"),
            make_event(2, 10, 202, "102", "10:30", "11:30"),
        ]
        self.service = SchedulingService(self.events)

    def test_get_timetable_returns_event_dicts(self):
        timetable = self.service.get_timetable()

        self.assertEqual(len(timetable), 2)
        self.assertEqual(timetable[0]["id"], 1)
        self.assertIn("group_id", timetable[0])

    def test_structured_conflicts_are_explainable(self):
        conflicts = self.service.analyze_conflicts_structured()

        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["constraint_type"], "faculty")
        self.assertEqual(conflicts[0]["severity"], "hard")
        self.assertIn("message", conflicts[0])

    def test_workload_report_includes_capacity(self):
        report = self.service.get_workload_report(capacities={10: 6})

        entry = next(e for e in report if e["faculty_id"] == 10)

        self.assertEqual(entry["allocated_hours"], 2.0)
        self.assertEqual(entry["capacity"], 6)
        self.assertEqual(entry["status"], "optimal")

    def test_overloaded_faculty_in_report(self):
        report = self.service.get_workload_report(capacities={10: 1})

        entry = next(e for e in report if e["faculty_id"] == 10)

        self.assertEqual(entry["status"], "overloaded")
        self.assertGreater(entry["overload"], 0)

    def test_recommend_reschedule_returns_recommendation(self):
        result = self.service.recommend_reschedule(
            1,
            candidates=[
                {"date": "2026-08-15", "start_time": "11:30", "end_time": "12:30"},
            ],
        )

        self.assertEqual(result["status"], "recommendation")
        self.assertEqual(result["event_id"], 1)

    def test_run_what_if_scenario(self):
        result = self.service.run_what_if(
            {
                "type": "room_unavailable",
                "resource": "101",
                "date": "2026-08-15",
                "start_time": "10:00",
                "end_time": "11:00",
            }
        )

        self.assertTrue(result["timetable_unchanged"])
        affected_ids = [e["id"] for e in result["affected_events"]]
        self.assertIn(1, affected_ids)


if __name__ == "__main__":
    unittest.main()