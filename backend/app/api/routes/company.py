from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User
from app.schemas.company import (
    CompanyCreate,
    CompanyResponse,
    CompanyUpdate,
)
from app.services.coe_service import CoEService


router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)

faculty_required = require_role("faculty")


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    return service.create_company(
        name=company_data.name,
        company_type=company_data.type,
    )


@router.get(
    "",
    response_model=list[CompanyResponse],
)
def get_companies(
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    return service.get_companies()


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    company = service.get_company(company_id)

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return company


@router.patch(
    "/{company_id}",
    response_model=CompanyResponse,
)
def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CoEService(db)

    company = service.get_company(company_id)

    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    return service.update_company(
        company=company,
        name=company_data.name,
        company_type=company_data.type,
    )