from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.scheduling.service import SchedulingService


router = APIRouter(
    prefix="/timetable",
    tags=["Timetable"],
)


@router.get("")
def get_timetable(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the official timetable.

    Read-only business operation. Does not modify any data.
    """
    service = SchedulingService.from_db(db)

    return service.get_timetable()