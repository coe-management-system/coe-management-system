from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.syllabus import SyllabusTopic


class SyllabusService:
    def __init__(self, db: Session):
        self.db = db

    def create_topic(
        self,
        subject_id: int,
        unit: str,
        topic: str,
        planned_classes: int,
        completed_classes: int,
        target_date: date | None,
        actual_date: date | None,
    ) -> SyllabusTopic:
        self._validate_class_counts(
            planned_classes,
            completed_classes,
        )

        syllabus_topic = SyllabusTopic(
            subject_id=subject_id,
            unit=unit,
            topic=topic,
            planned_classes=planned_classes,
            completed_classes=completed_classes,
            target_date=target_date,
            actual_date=actual_date,
        )

        self.db.add(syllabus_topic)
        self.db.commit()
        self.db.refresh(syllabus_topic)

        return syllabus_topic

    def get_topic(self, topic_id: int) -> SyllabusTopic | None:
        return self.db.get(SyllabusTopic, topic_id)

    def get_topics(
        self,
        subject_id: int | None = None,
    ) -> list[SyllabusTopic]:
        query = select(SyllabusTopic)

        if subject_id is not None:
            query = query.where(
                SyllabusTopic.subject_id == subject_id
            )

        return self.db.scalars(query).all()

    def update_topic(
        self,
        topic: SyllabusTopic,
        unit: str | None = None,
        topic_name: str | None = None,
        planned_classes: int | None = None,
        completed_classes: int | None = None,
        target_date: date | None = None,
        actual_date: date | None = None,
    ) -> SyllabusTopic:
        new_planned = (
            planned_classes
            if planned_classes is not None
            else topic.planned_classes
        )

        new_completed = (
            completed_classes
            if completed_classes is not None
            else topic.completed_classes
        )

        self._validate_class_counts(
            new_planned,
            new_completed,
        )

        if unit is not None:
            topic.unit = unit

        if topic_name is not None:
            topic.topic = topic_name

        if planned_classes is not None:
            topic.planned_classes = planned_classes

        if completed_classes is not None:
            topic.completed_classes = completed_classes

        if target_date is not None:
            topic.target_date = target_date

        if actual_date is not None:
            topic.actual_date = actual_date

        self.db.commit()
        self.db.refresh(topic)

        return topic

    @staticmethod
    def calculate_pending_classes(
        planned_classes: int,
        completed_classes: int,
    ) -> int:
        return max(
            planned_classes - completed_classes,
            0,
        )

    @staticmethod
    def calculate_progress(
        planned_classes: int,
        completed_classes: int,
    ) -> float:
        if planned_classes == 0:
            return 0.0

        return round(
            (completed_classes / planned_classes) * 100,
            2,
        )

    @staticmethod
    def calculate_delay(
        target_date: date | None,
        actual_date: date | None,
    ) -> bool:
        if target_date is None:
            return False

        if actual_date is not None:
            return actual_date > target_date

        return date.today() > target_date

    @staticmethod
    def build_response_data(
        topic: SyllabusTopic,
    ) -> dict:
        return {
            "id": topic.id,
            "subject_id": topic.subject_id,
            "unit": topic.unit,
            "topic": topic.topic,
            "planned_classes": topic.planned_classes,
            "completed_classes": topic.completed_classes,
            "target_date": topic.target_date,
            "actual_date": topic.actual_date,
            "pending_classes": SyllabusService.calculate_pending_classes(
                topic.planned_classes,
                topic.completed_classes,
            ),
            "progress_percentage": SyllabusService.calculate_progress(
                topic.planned_classes,
                topic.completed_classes,
            ),
            "is_delayed": SyllabusService.calculate_delay(
                topic.target_date,
                topic.actual_date,
            ),
        }

    @staticmethod
    def _validate_class_counts(
        planned_classes: int,
        completed_classes: int,
    ) -> None:
        if planned_classes < 0:
            raise ValueError(
                "Planned classes cannot be negative"
            )

        if completed_classes < 0:
            raise ValueError(
                "Completed classes cannot be negative"
            )

        if completed_classes > planned_classes:
            raise ValueError(
                "Completed classes cannot exceed planned classes"
            )
