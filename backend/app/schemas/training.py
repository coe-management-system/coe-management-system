from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TrainingProgramBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None

    coe_id: int
    company_id: int
    technology_id: int

    start_date: date
    end_date: date

    planned_hours: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")
        return self


class TrainingProgramCreate(TrainingProgramBase):
    pass


class TrainingProgramResponse(TrainingProgramBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class TrainingSessionBase(BaseModel):
    program_id: int
    batch_id: int
    group_id: int | None = None
    title: str = Field(min_length=1, max_length=150)

    faculty_id: int

    start_at: datetime
    end_at: datetime

    hours: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_session_times(self):
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be later than start_at")
        return self


class TrainingSessionCreate(TrainingSessionBase):
    pass


class TrainingSessionResponse(TrainingSessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int