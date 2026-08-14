from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    type: str | None = Field(default=None, max_length=50)


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    type: str | None = Field(
        default=None,
        max_length=50,
    )


class CompanyResponse(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int