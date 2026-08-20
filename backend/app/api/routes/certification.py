from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.certification import CertificationAttempt
from app.models.user import User
from app.schemas.certification import (
    CertificationAttemptCreate,
    CertificationAttemptResponse,
    CertificationAttemptUpdate,
    CertificationCreate,
    CertificationResponse,
    CertificationSummary,
)
from app.services.certification_service import CertificationService


router = APIRouter(
    prefix="/certifications",
    tags=["Certification"],
)

faculty_required = require_role("faculty")


@router.post(
    "",
    response_model=CertificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_certification(
    certification_data: CertificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CertificationService(db)

    return service.create_certification(
        name=certification_data.name,
        issuing_organization=certification_data.issuing_organization,
    )


@router.get(
    "",
    response_model=list[CertificationResponse],
)
def get_certifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CertificationService(db)

    return service.get_certifications()


@router.get(
    "/summary",
    response_model=CertificationSummary,
)
def get_certification_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CertificationService(db)

    return service.get_summary()


@router.post(
    "/attempts",
    response_model=CertificationAttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_certification_attempt(
    attempt_data: CertificationAttemptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CertificationService(db)

    try:
        return service.record_attempt(
            student_id=attempt_data.student_id,
            certification_id=attempt_data.certification_id,
            status=attempt_data.status,
            score=attempt_data.score,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "/attempts",
    response_model=list[CertificationAttemptResponse],
)
def get_certification_attempts(
    student_id: int | None = None,
    certification_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CertificationService(db)

    return service.get_attempts(
        student_id=student_id,
        certification_id=certification_id,
    )


@router.get(
    "/{certification_id}",
    response_model=CertificationResponse,
)
def get_certification(
    certification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CertificationService(db)

    certification = service.get_certification(certification_id)

    if certification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification not found",
        )

    return certification


@router.patch(
    "/attempts/{attempt_id}",
    response_model=CertificationAttemptResponse,
)
def update_certification_attempt(
    attempt_id: int,
    attempt_data: CertificationAttemptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = CertificationService(db)

    attempt = db.get(CertificationAttempt, attempt_id)

    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certification attempt not found",
        )

    return service.update_attempt(
        attempt=attempt,
        status=attempt_data.status,
        score=attempt_data.score,
    )
