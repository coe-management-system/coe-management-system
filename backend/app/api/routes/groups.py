from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.group import Group


router = APIRouter(
    prefix="/groups",
    tags=["Groups"],
)


@router.get("")
def get_groups(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Group)
    ).all()