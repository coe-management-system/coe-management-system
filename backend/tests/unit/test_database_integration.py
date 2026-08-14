import unittest
from datetime import date, time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.timetable import TimetableEvent
from app.scheduling.service import SchedulingService


class TestDatabaseIntegration(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

        self.db.add_all(
            [
                TimetableEvent(
                    id=1,
                    subject_id=101,
                    faculty_id=10,
                    batch_id=201,
                    room_id="101",
                    event_date=date(2026, 8, 15),
                    start_time=time(10, 0),
                    end_time=time(11, 0),
                    priority=2,
                ),
                TimetableEvent(
                    id=2,
                    subject_id=102,
                    faculty_id=10,
                    batch_id=202,
                    room_id="102",
                    event_date=date(2026, 8, 15),
                    start_time=time(10, 30),
                    end_time=time(11, 30),
                    priority=2,
                ),
            ]
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_from_db_loads_real_entities(self):
        service = SchedulingService.from_db(self.db)

        timetable = service.get_timetable()

        self.assertEqual(len(timetable), 2)
        self.assertEqual(timetable[0]["id"], 1)
        self.assertEqual(timetable[0]["faculty_id"], 10)
        self.assertEqual(timetable[0]["start_time"], "10:00")

    def test_from_db_detects_conflicts(self):
        service = SchedulingService.from_db(self.db)

        conflicts = service.analyze_conflicts()

        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["type"], "faculty")

    def test_from_db_structured_conflicts(self):
        service = SchedulingService.from_db(self.db)

        violations = service.analyze_conflicts_structured()

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["constraint_type"], "faculty")

    def test_what_if_does_not_modify_database(self):
        service = SchedulingService.from_db(self.db)

        service.run_what_if(
            {
                "type": "room_unavailable",
                "resource": "101",
                "date": "2026-08-15",
                "start_time": "10:00",
                "end_time": "11:00",
            }
        )

        rows = self.db.query(TimetableEvent).all()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].room_id, "101")
        self.assertEqual(rows[0].start_time, time(10, 0))


if __name__ == "__main__":
    unittest.main()