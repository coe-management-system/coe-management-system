from datetime import date, time

from pydantic import BaseModel


class TimetableEventResponse(BaseModel):
    id: int
    subject_id: int
    faculty_id: int
    batch_id: int
    room_id: str | None
    date: date
    start_time: str
    end_time: str
    priority: int
    group_id: int | None = None