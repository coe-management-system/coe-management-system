import unittest
from datetime import date, time

from app.scheduling.domain import SchedulingEvent


class TestSchedulingEvent(unittest.TestCase):

    def test_from_timetable_data(self):
        event = SchedulingEvent.from_timetable_data(
            id=1,
            subject_id=101,
            faculty_id=10,
            batch_id=201,
            room_id="101",
            event_date=date(2026, 8, 15),
            start_time=time(10, 0),
            end_time=time(11, 0),
            priority=2,
        )

        self.assertEqual(event.id, 1)
        self.assertEqual(event.subject_id, 101)
        self.assertEqual(event.faculty_id, 10)
        self.assertEqual(event.batch_id, 201)
        self.assertEqual(event.room_id, "101")
        self.assertEqual(event.date, date(2026, 8, 15))
        self.assertEqual(event.start_time, "10:00")
        self.assertEqual(event.end_time, "11:00")
        self.assertEqual(event.priority, 2)

    def test_to_dict(self):
        event = SchedulingEvent(
            id=1,
            subject_id=101,
            faculty_id=10,
            batch_id=201,
            room_id="101",
            date=date(2026, 8, 15),
            start_time="10:00",
            end_time="11:00",
            priority=2,
        )

        result = event.to_dict()

        self.assertEqual(result["id"], 1)
        self.assertEqual(result["faculty_id"], 10)
        self.assertEqual(result["batch_id"], 201)
        self.assertEqual(result["room_id"], "101")
        self.assertEqual(result["date"], date(2026, 8, 15))
        self.assertEqual(result["start_time"], "10:00")
        self.assertEqual(result["end_time"], "11:00")
        self.assertEqual(result["priority"], 2)


if __name__ == "__main__":
    unittest.main()