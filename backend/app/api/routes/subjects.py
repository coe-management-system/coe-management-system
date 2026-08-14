from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User
from app.schemas.subject import (
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)
from app.services.subject_service import SubjectService


router = APIRouter(
    prefix="/subjects",
    tags=["Subjects"],
)

faculty_required = require_role("faculty")


@router.post(
    "",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subject(
    subject_data: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = SubjectService(db)

    try:
        return service.create_subject(
            code=subject_data.code,
            name=subject_data.name,
            department_id=subject_data.department_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[SubjectResponse],
)
def get_subjects(
    department_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = SubjectService(db)

    return service.get_subjects(
        department_id=department_id,
    )


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = SubjectService(db)

    subject = service.get_subject(subject_id)

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    return subject


@router.patch(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def update_subject(
    subject_id: int,
    subject_data: SubjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = SubjectService(db)

    subject = service.get_subject(subject_id)

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    try:
        return service.update_subject(
            subject=subject,
            code=subject_data.code,
            name=subject_data.name,
            department_id=subject_data.department_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )