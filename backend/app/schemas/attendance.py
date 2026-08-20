from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict


AttendanceStatus = Literal[
    "PRESENT",
    "ABSENT",
    "EXCUSED",
    "CANCELLED",
]


class AttendanceCreate(BaseModel):
    student_id: int
    subject_id: int
    session_date: date
    status: AttendanceStatus


class AttendanceRecordCreate(BaseModel):
    student_id: int
    status: AttendanceStatus


class AttendanceBulkCreate(BaseModel):
    subject_id: int
    session_date: date
    records: list[AttendanceRecordCreate]


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    subject_id: int
    session_date: date
    status: AttendanceStatus

    model_config = ConfigDict(
        from_attributes=True
    )


class AttendanceSummary(BaseModel):
    student_id: int
    subject_id: int
    attended_sessions: int
    eligible_sessions: int
    attendance_percentage: float


class AttendanceOverviewItem(BaseModel):
    student_id: int
    roll_no: str
    name: str
    department: str
    batch: str
    total_classes: int
    attended: int
    percentage: float