from datetime import date

from pydantic import BaseModel, ConfigDict


class SyllabusTopicBase(BaseModel):
    subject_id: int
    unit: str
    topic: str
    planned_classes: int = 0
    completed_classes: int = 0
    target_date: date | None = None
    actual_date: date | None = None


class SyllabusTopicCreate(SyllabusTopicBase):
    pass


class SyllabusTopicUpdate(BaseModel):
    subject_id: int | None = None
    unit: str | None = None
    topic: str | None = None
    planned_classes: int | None = None
    completed_classes: int | None = None
    target_date: date | None = None
    actual_date: date | None = None


class SyllabusTopicResponse(SyllabusTopicBase):
    id: int

    model_config = ConfigDict(from_attributes=True)