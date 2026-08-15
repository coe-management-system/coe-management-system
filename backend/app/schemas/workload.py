from pydantic import BaseModel


class WorkloadEntry(BaseModel):
    faculty_id: int
    allocated_hours: float
    capacity: float | None = None
    overload: float | None = None
    status: str


class WorkloadReport(BaseModel):
    entries: list[WorkloadEntry]