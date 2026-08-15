from pydantic import BaseModel, ConfigDict, Field


class SubjectBase(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=150)
    department_id: int


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    code: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    department_id: int | None = None


class SubjectResponse(SubjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int