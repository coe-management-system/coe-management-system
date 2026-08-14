from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.models.syllabus import SyllabusTopic
from app.services.syllabus_service import SyllabusService


class TestSyllabusService:

    def setup_method(self):
        self.db = MagicMock()
        self.service = SyllabusService(self.db)

    def test_calculate_pending_classes(self):
        result = self.service.calculate_pending_classes(
            planned_classes=10,
            completed_classes=6,
        )

        assert result == 4

    def test_calculate_pending_classes_when_complete(self):
        result = self.service.calculate_pending_classes(
            planned_classes=10,
            completed_classes=10,
        )

        assert result == 0

    def test_calculate_progress(self):
        result = self.service.calculate_progress(
            planned_classes=10,
            completed_classes=7,
        )

        assert result == 70.0

    def test_calculate_progress_with_zero_planned_classes(self):
        result = self.service.calculate_progress(
            planned_classes=0,
            completed_classes=0,
        )

        assert result == 0.0

    def test_calculate_progress_rounds_to_two_decimals(self):
        result = self.service.calculate_progress(
            planned_classes=3,
            completed_classes=1,
        )

        assert result == 33.33

    def test_calculate_delay_when_completed_late(self):
        result = self.service.calculate_delay(
            target_date=date(2026, 8, 10),
            actual_date=date(2026, 8, 12),
        )

        assert result is True

    def test_calculate_delay_when_completed_on_time(self):
        result = self.service.calculate_delay(
            target_date=date(2026, 8, 10),
            actual_date=date(2026, 8, 10),
        )

        assert result is False

    def test_calculate_delay_when_not_completed_and_target_passed(self):
        result = self.service.calculate_delay(
            target_date=date.today() - timedelta(days=1),
            actual_date=None,
        )

        assert result is True

    def test_calculate_delay_when_target_date_not_passed(self):
        result = self.service.calculate_delay(
            target_date=date.today() + timedelta(days=1),
            actual_date=None,
        )

        assert result is False

    def test_calculate_delay_without_target_date(self):
        result = self.service.calculate_delay(
            target_date=None,
            actual_date=None,
        )

        assert result is False

    def test_create_rejects_negative_planned_classes(self):
        with pytest.raises(
            ValueError,
            match="Planned classes cannot be negative",
        ):
            self.service.create_topic(
                subject_id=1,
                unit="Unit 1",
                topic="Introduction",
                planned_classes=-1,
                completed_classes=0,
                target_date=None,
                actual_date=None,
            )

    def test_create_rejects_negative_completed_classes(self):
        with pytest.raises(
            ValueError,
            match="Completed classes cannot be negative",
        ):
            self.service.create_topic(
                subject_id=1,
                unit="Unit 1",
                topic="Introduction",
                planned_classes=5,
                completed_classes=-1,
                target_date=None,
                actual_date=None,
            )

    def test_create_rejects_completed_classes_above_planned(self):
        with pytest.raises(
            ValueError,
            match="Completed classes cannot exceed planned classes",
        ):
            self.service.create_topic(
                subject_id=1,
                unit="Unit 1",
                topic="Introduction",
                planned_classes=5,
                completed_classes=6,
                target_date=None,
                actual_date=None,
            )

    def test_build_response_data(self):
        topic = SyllabusTopic(
            id=1,
            subject_id=10,
            unit="Unit 1",
            topic="Introduction",
            planned_classes=10,
            completed_classes=7,
            target_date=date(2026, 8, 20),
            actual_date=None,
        )

        data = self.service.build_response_data(topic)

        assert data["id"] == 1
        assert data["subject_id"] == 10
        assert data["unit"] == "Unit 1"
        assert data["topic"] == "Introduction"
        assert data["planned_classes"] == 10
        assert data["completed_classes"] == 7
        assert data["pending_classes"] == 3
        assert data["progress_percentage"] == 70.0
        assert data["is_delayed"] is False
