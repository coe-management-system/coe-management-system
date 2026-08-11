from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.faculty import Faculty


router = APIRouter(
    prefix="/faculty",
    tags=["Faculty"],
)


@router.get("")
def get_faculty(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Faculty)
    ).all()