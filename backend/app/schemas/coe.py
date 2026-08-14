from pydantic import BaseModel, ConfigDict, Field


class CoEBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    status: str = Field(min_length=1, max_length=50)


class CoECreate(CoEBase):
    pass


class CoEUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    status: str | None = Field(default=None, min_length=1, max_length=50)


class CoEResponse(CoEBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class CoELabBase(BaseModel):
    coe_id: int
    name: str = Field(min_length=1, max_length=150)
    location: str | None = Field(default=None, max_length=255)
    capacity: int | None = Field(default=None, ge=0)


class CoELabCreate(CoELabBase):
    pass


class CoELabResponse(CoELabBase):
    model_config = ConfigDict(from_attributes=True)

    id: int