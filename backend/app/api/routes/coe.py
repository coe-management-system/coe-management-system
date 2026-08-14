from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import faculty_required
from app.core.dependencies import require_role
from app.models.coe import CoE
from app.models.coe_lab import CoELab
from app.models.user import User
from app.schemas.coe import (
    CoECreate,
    CoEResponse,
    CoEUpdate,
    CoELabCreate,
    CoELabResponse,
)
from app.services.coe_service import CoEService


router = APIRouter(
    prefix="/coe",
    tags=["CoE"],
)

faculty_required = require_role("faculty")


@router.post(
    "",
    response_model=CoEResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_coe(
    coe_data: CoECreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    return service.create_coe(
        name=coe_data.name,
        status=coe_data.status,
    )


@router.get(
    "",
    response_model=list[CoEResponse],
)
def get_coes(
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    return service.get_coes()

@router.post(
    "/labs",
    response_model=CoELabResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_coe_lab(
    lab_data: CoELabCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    try:
        return service.create_lab(
            coe_id=lab_data.coe_id,
            name=lab_data.name,
            location=lab_data.location,
            capacity=lab_data.capacity,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )




@router.get(
    "/labs",
    response_model=list[CoELabResponse],
)
def get_coe_labs(
    coe_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    return service.get_labs(coe_id=coe_id)


@router.get(
    "/labs/{lab_id}",
    response_model=CoELabResponse,
)
def get_coe_lab(
    lab_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    lab = service.get_lab(lab_id)

    if lab is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CoE lab not found",
        )
    return lab


@router.get(
    "/{coe_id}",
    response_model=CoEResponse,
)
def get_coe(
    coe_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    coe = service.get_coe(coe_id)

    if coe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CoE not found",
        )

    return coe

@router.patch(
    "/{coe_id}",
    response_model=CoEResponse,
)
def update_coe(
    coe_id: int,
    coe_data: CoEUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    coe = service.get_coe(coe_id)

    if coe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CoE not found",
        )

    return service.update_coe(
        coe=coe,
        name=coe_data.name,
        status=coe_data.status,
    )
    