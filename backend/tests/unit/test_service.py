import unittest
from datetime import date

from app.scheduling.domain import SchedulingEvent
from app.scheduling.service import SchedulingService


class TestSchedulingService(unittest.TestCase):

    def setUp(self):
        self.events = [
            SchedulingEvent(
                id=1,
                subject_id=101,
                faculty_id=10,
                batch_id=201,
                room_id="101",
                date=date(2026, 8, 15),
                start_time="10:00",
                end_time="11:00",
                priority=2,
            ),
            SchedulingEvent(
                id=2,
                subject_id=102,
                faculty_id=10,
                batch_id=202,
                room_id="102",
                date=date(2026, 8, 15),
                start_time="10:30",
                end_time="11:30",
                priority=2,
            ),
        ]

        self.service = SchedulingService(self.events)

    def test_analyze_conflicts(self):
        conflicts = self.service.analyze_conflicts()

        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["type"], "faculty")
        self.assertEqual(conflicts[0]["event_1"], 1)
        self.assertEqual(conflicts[0]["event_2"], 2)

    def test_get_faculty_workload(self):
        workload = self.service.get_faculty_workload(10)

        self.assertEqual(workload["faculty_id"], 10)
        self.assertEqual(workload["allocated_hours"], 2.0)

    def test_empty_timetable(self):
        service = SchedulingService()

        self.assertEqual(service.analyze_conflicts(), [])

        self.assertEqual(
            service.get_faculty_workload(10),
            {
                "faculty_id": 10,
                "allocated_hours": 0,
            },
        )


if __name__ == "__main__":
    unittest.main()