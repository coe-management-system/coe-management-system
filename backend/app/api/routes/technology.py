from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User
from app.schemas.technology import (
    TechnologyCreate,
    TechnologyResponse,
    TechnologyUpdate,
)
from app.services.coe_service import CoEService


router = APIRouter(
    prefix="/technologies",
    tags=["Technologies"],
)

faculty_required = require_role("faculty")


@router.post(
    "",
    response_model=TechnologyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_technology(
    technology_data: TechnologyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    return service.create_technology(
        name=technology_data.name,
    )


@router.get(
    "",
    response_model=list[TechnologyResponse],
)
def get_technologies(
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    return service.get_technologies()


@router.get(
    "/{technology_id}",
    response_model=TechnologyResponse,
)
def get_technology(
    technology_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    technology = service.get_technology(technology_id)

    if technology is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technology not found",
        )

    return technology


@router.patch(
    "/{technology_id}",
    response_model=TechnologyResponse,
)
def update_technology(
    technology_id: int,
    technology_data: TechnologyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    technology = service.get_technology(technology_id)

    if technology is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Technology not found",
        )

    return service.update_technology(
        technology=technology,
        name=technology_data.name,
    )