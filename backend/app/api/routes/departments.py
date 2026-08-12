from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.department import Department


router = APIRouter(
    prefix="/departments",
    tags=["Departments"],
)


@router.get("")
def get_departments(
    db: Session = Depends(get_db),
):
    departments = db.scalars(
        select(Department)
    ).all()

    return departments