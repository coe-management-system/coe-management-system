from pydantic import BaseModel, ConfigDict, Field


class CertificationBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    issuing_organization: str | None = Field(default=None, max_length=150)


class CertificationCreate(CertificationBase):
    pass


class CertificationResponse(CertificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class CertificationAttemptBase(BaseModel):
    student_id: int
    certification_id: int
    status: str = Field(min_length=1, max_length=50)
    score: float | None = Field(default=None, ge=0, le=100)


class CertificationAttemptCreate(CertificationAttemptBase):
    pass


class CertificationAttemptUpdate(BaseModel):
    status: str | None = Field(default=None, min_length=1, max_length=50)
    score: float | None = Field(default=None, ge=0, le=100)


class CertificationAttemptResponse(CertificationAttemptBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_name: str | None = None
    certification_name: str | None = None


class CertificationSummary(BaseModel):
    total_certifications: int
    total_attempts: int
    completed: int
    in_progress: int
    pending: int
    recent_attempts: list[CertificationAttemptResponse] = []
