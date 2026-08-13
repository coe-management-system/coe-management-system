from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.faculty import Faculty
from app.models.user import User


router = APIRouter(
    prefix="/faculty",
    tags=["Faculty"],
)

faculty_required = require_role("faculty")


@router.get("")
def get_faculty(
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    return db.scalars(
        select(Faculty)
    ).all()