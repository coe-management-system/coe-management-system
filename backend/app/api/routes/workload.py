from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.scheduling.service import SchedulingService


router = APIRouter(
    prefix="/workload",
    tags=["Workload"],
)


@router.get("")
def get_faculty_workload(
    capacity: float | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the faculty workload report.

    An optional uniform capacity can be provided to evaluate overload
    status. Read-only business operation.
    """
    service = SchedulingService.from_db(db)

    capacities = None
    if capacity is not None:
        faculty_ids = {event["faculty_id"] for event in service.get_timetable()}
        capacities = {faculty_id: capacity for faculty_id in faculty_ids}

    return service.get_workload_report(capacities)