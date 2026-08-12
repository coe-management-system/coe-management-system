from datetime import datetime
from sqlalchemy import DateTime, func
from pydantic import BaseModel, ConfigDict, EmailStr


class StudentCreate(BaseModel):
    roll_no: str
    name: str
    email: EmailStr
    department_id: int
    batch_id: int
    group_id: int


class StudentResponse(BaseModel):
    id: int
    roll_no: str
    name: str
    email: EmailStr
    department_id: int
    batch_id: int
    group_id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True
    )