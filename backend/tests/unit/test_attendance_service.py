import unittest
from datetime import date
from unittest.mock import MagicMock

from app.models.attendance import Attendance
from app.services.attendance_service import AttendanceService


class TestAttendanceService(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.service = AttendanceService(self.db)

    def test_record_attendance(self):
        self.db.scalar.return_value = None

        result = self.service.record(
            student_id=1,
            subject_id=101,
            session_date=date(2026, 8, 13),
            status="PRESENT",
        )

        self.assertIsInstance(result, Attendance)
        self.assertEqual(result.student_id, 1)
        self.assertEqual(result.subject_id, 101)
        self.assertEqual(
            result.session_date,
            date(2026, 8, 13),
        )
        self.assertEqual(result.status, "PRESENT")

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(result)

    def test_record_duplicate_attendance(self):
        existing = Attendance(
            id=1,
            student_id=1,
            subject_id=101,
            session_date=date(2026, 8, 13),
            status="PRESENT",
        )

        self.db.scalar.return_value = existing

        with self.assertRaises(ValueError):
            self.service.record(
                student_id=1,
                subject_id=101,
                session_date=date(2026, 8, 13),
                status="ABSENT",
            )

        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_bulk_record(self):
        self.db.scalars.return_value.all.return_value = []

        records = [
            {
                "student_id": 1,
                "status": "PRESENT",
            },
            {
                "student_id": 2,
                "status": "ABSENT",
            },
        ]

        result = self.service.bulk_record(
            subject_id=101,
            session_date=date(2026, 8, 13),
            records=records,
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].student_id, 1)
        self.assertEqual(result[0].status, "PRESENT")
        self.assertEqual(result[1].student_id, 2)
        self.assertEqual(result[1].status, "ABSENT")

        self.db.add_all.assert_called_once()
        self.db.commit.assert_called_once()

    def test_bulk_record_rejects_duplicate_students(self):
        records = [
            {
                "student_id": 1,
                "status": "PRESENT",
            },
            {
                "student_id": 1,
                "status": "ABSENT",
            },
        ]

        with self.assertRaises(ValueError):
            self.service.bulk_record(
                subject_id=101,
                session_date=date(2026, 8, 13),
                records=records,
            )

        self.db.add_all.assert_not_called()
        self.db.commit.assert_not_called()

    def test_calculate_percentage(self):
        records = [
            Attendance(
                id=1,
                student_id=1,
                subject_id=101,
                session_date=date(2026, 8, 10),
                status="PRESENT",
            ),
            Attendance(
                id=2,
                student_id=1,
                subject_id=101,
                session_date=date(2026, 8, 11),
                status="PRESENT",
            ),
            Attendance(
                id=3,
                student_id=1,
                subject_id=101,
                session_date=date(2026, 8, 12),
                status="ABSENT",
            ),
            Attendance(
                id=4,
                student_id=1,
                subject_id=101,
                session_date=date(2026, 8, 13),
                status="EXCUSED",
            ),
            Attendance(
                id=5,
                student_id=1,
                subject_id=101,
                session_date=date(2026, 8, 14),
                status="CANCELLED",
            ),
        ]

        self.db.scalars.return_value.all.return_value = records

        percentage = self.service.calculate_percentage(
            student_id=1,
            subject_id=101,
        )

        self.assertEqual(percentage, 66.67)

    def test_calculate_percentage_with_no_eligible_sessions(self):
        records = [
            Attendance(
                id=1,
                student_id=1,
                subject_id=101,
                session_date=date(2026, 8, 13),
                status="EXCUSED",
            ),
            Attendance(
                id=2,
                student_id=1,
                subject_id=101,
                session_date=date(2026, 8, 14),
                status="CANCELLED",
            ),
        ]

        self.db.scalars.return_value.all.return_value = records

        percentage = self.service.calculate_percentage(
            student_id=1,
            subject_id=101,
        )

        self.assertEqual(percentage, 0.0)


if __name__ == "__main__":
    unittest.main()