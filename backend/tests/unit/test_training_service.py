import unittest
from datetime import date, datetime
from unittest.mock import MagicMock

from app.models.batch import Batch
from app.models.coe import CoE
from app.models.company import Company
from app.models.faculty import Faculty
from app.models.group import Group
from app.models.technology import Technology
from app.models.training import TrainingProgram, TrainingSession
from app.services.training_service import TrainingService


class TestTrainingService(unittest.TestCase):

    def setUp(self):
        self.db = MagicMock()
        self.service = TrainingService(self.db)

    def test_create_program(self):
        coe = CoE(
            id=1,
            name="Cloud CoE",
            status="active",
        )

        company = Company(
            id=1,
            name="AWS",
            type="Technology",
        )

        technology = Technology(
            id=1,
            name="AWS",
        )

        def get_side_effect(model, object_id):
            if model is CoE:
                return coe

            if model is Company:
                return company

            if model is Technology:
                return technology

            return None

        self.db.get.side_effect = get_side_effect

        result = self.service.create_program(
            name="AWS Fundamentals",
            description="Cloud training",
            coe_id=1,
            company_id=1,
            technology_id=1,
            start_date=date(2026, 8, 15),
            end_date=date(2026, 8, 30),
            planned_hours=40,
        )

        self.assertIsInstance(
            result,
            TrainingProgram,
        )

        self.assertEqual(
            result.name,
            "AWS Fundamentals",
        )

        self.assertEqual(
            result.coe_id,
            1,
        )

        self.assertEqual(
            result.company_id,
            1,
        )

        self.assertEqual(
            result.technology_id,
            1,
        )

        self.assertEqual(
            result.planned_hours,
            40,
        )

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(result)

    def test_create_program_rejects_missing_coe(self):
        self.db.get.return_value = None

        with self.assertRaisesRegex(
            ValueError,
            "CoE not found",
        ):
            self.service.create_program(
                name="AWS Fundamentals",
                description=None,
                coe_id=999,
                company_id=1,
                technology_id=1,
                start_date=date(2026, 8, 15),
                end_date=date(2026, 8, 30),
                planned_hours=40,
            )

        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_create_program_rejects_invalid_dates(self):
        coe = CoE(
            id=1,
            name="Cloud CoE",
            status="active",
        )

        company = Company(
            id=1,
            name="AWS",
            type="Technology",
        )

        technology = Technology(
            id=1,
            name="AWS",
        )

        def get_side_effect(model, object_id):
            if model is CoE:
                return coe

            if model is Company:
                return company

            if model is Technology:
                return technology

            return None

        self.db.get.side_effect = get_side_effect

        with self.assertRaisesRegex(
            ValueError,
            "end date cannot be earlier",
        ):
            self.service.create_program(
                name="Invalid",
                description=None,
                coe_id=1,
                company_id=1,
                technology_id=1,
                start_date=date(2026, 8, 30),
                end_date=date(2026, 8, 15),
                planned_hours=40,
            )

        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_schedule_session(self):
        program = TrainingProgram(
            id=1,
            name="AWS Fundamentals",
            coe_id=1,
            company_id=1,
            technology_id=1,
            start_date=date(2026, 8, 15),
            end_date=date(2026, 8, 30),
            planned_hours=40,
        )

        faculty = Faculty(
            id=1,
        )

        batch = Batch(
            id=1,
        )

        def get_side_effect(model, object_id):
            if model is TrainingProgram:
                return program

            if model is Faculty:
                return faculty

            if model is Batch:
                return batch

            return None

        self.db.get.side_effect = get_side_effect

        result = self.service.schedule_session(
            program_id=1,
            faculty_id=1,
            batch_id=1,
            group_id=None,
            title="AWS Introduction",
            start_at=datetime(2026, 8, 15, 10, 0),
            end_at=datetime(2026, 8, 15, 12, 0),
            hours=2,
        )

        self.assertIsInstance(
            result,
            TrainingSession,
        )

        self.assertEqual(
            result.program_id,
            1,
        )

        self.assertEqual(
            result.faculty_id,
            1,
        )

        self.assertEqual(
            result.batch_id,
            1,
        )

        self.assertEqual(
            result.hours,
            2,
        )

        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(result)

    def test_schedule_session_rejects_missing_program(self):
        self.db.get.return_value = None

        with self.assertRaisesRegex(
            ValueError,
            "Training program not found",
        ):
            self.service.schedule_session(
                program_id=999,
                faculty_id=1,
                batch_id=1,
                group_id=None,
                title="AWS Introduction",
                start_at=datetime(2026, 8, 15, 10, 0),
                end_at=datetime(2026, 8, 15, 12, 0),
                hours=2,
            )

        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_schedule_session_rejects_invalid_time(self):
        program = TrainingProgram(
            id=1,
            name="AWS Fundamentals",
            coe_id=1,
            company_id=1,
            technology_id=1,
            start_date=date(2026, 8, 15),
            end_date=date(2026, 8, 30),
            planned_hours=40,
        )

        faculty = Faculty(
            id=1,
        )

        batch = Batch(
            id=1,
        )

        def get_side_effect(model, object_id):
            if model is TrainingProgram:
                return program

            if model is Faculty:
                return faculty

            if model is Batch:
                return batch

            return None

        self.db.get.side_effect = get_side_effect

        with self.assertRaisesRegex(
            ValueError,
            "Session end time must be later",
        ):
            self.service.schedule_session(
                program_id=1,
                faculty_id=1,
                batch_id=1,
                group_id=None,
                title="Invalid Session",
                start_at=datetime(2026, 8, 15, 12, 0),
                end_at=datetime(2026, 8, 15, 10, 0),
                hours=2,
            )

        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_calculate_completion(self):
        program = TrainingProgram(
            id=1,
            name="AWS Fundamentals",
            coe_id=1,
            company_id=1,
            technology_id=1,
            start_date=date(2026, 8, 15),
            end_date=date(2026, 8, 30),
            planned_hours=40,
        )

        sessions = [
            TrainingSession(
                id=1,
                program_id=1,
                batch_id=1,
                group_id=None,
                title="Introduction",
                faculty_id=1,
                start_at=datetime(2026, 8, 15, 10, 0),
                end_at=datetime(2026, 8, 15, 12, 0),
                hours=2,
            ),
            TrainingSession(
                id=2,
                program_id=1,
                batch_id=1,
                group_id=None,
                title="EC2",
                faculty_id=1,
                start_at=datetime(2026, 8, 16, 10, 0),
                end_at=datetime(2026, 8, 16, 13, 0),
                hours=3,
            ),
        ]

        self.db.get.return_value = program
        self.db.scalars.return_value.all.return_value = sessions

        result = self.service.calculate_completion(
            program_id=1,
        )

        self.assertEqual(
            result["program_id"],
            1,
        )

        self.assertEqual(
            result["planned_hours"],
            40,
        )

        self.assertEqual(
            result["completed_hours"],
            5,
        )

        self.assertEqual(
            result["completion_percentage"],
            12.5,
        )

        self.assertEqual(
            result["session_count"],
            2,
        )

    def test_calculate_completion_rejects_missing_program(self):
        self.db.get.return_value = None

        with self.assertRaisesRegex(
            ValueError,
            "Training program not found",
        ):
            self.service.calculate_completion(
                program_id=999,
            )


if __name__ == "__main__":
    unittest.main()