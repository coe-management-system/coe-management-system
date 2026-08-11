from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.batch import Batch


router = APIRouter(
    prefix="/batches",
    tags=["Batches"],
)


@router.get("")
def get_batches(
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Batch)
    ).all()