from pydantic import BaseModel, ConfigDict, Field


class TechnologyBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class TechnologyCreate(TechnologyBase):
    pass


class TechnologyUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )


class TechnologyResponse(TechnologyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int