from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User
from app.schemas.training import (
    TrainingProgramCreate,
    TrainingProgramResponse,
    TrainingSessionCreate,
    TrainingSessionResponse,
)
from app.services.training_service import TrainingService


router = APIRouter(
    prefix="/training",
    tags=["Training"],
)

faculty_required = require_role("faculty")


@router.post(
    "/programs",
    response_model=TrainingProgramResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_training_program(
    program_data: TrainingProgramCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = TrainingService(db)

    try:
        return service.create_program(
            name=program_data.name,
            description=program_data.description,
            coe_id=program_data.coe_id,
            company_id=program_data.company_id,
            technology_id=program_data.technology_id,
            start_date=program_data.start_date,
            end_date=program_data.end_date,
            planned_hours=program_data.planned_hours,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/programs",
    response_model=list[TrainingProgramResponse],
)
def get_training_programs(
    coe_id: int | None = None,
    company_id: int | None = None,
    technology_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = TrainingService(db)

    return service.get_programs(
        coe_id=coe_id,
        company_id=company_id,
        technology_id=technology_id,
    )


@router.get(
    "/programs/{program_id}",
    response_model=TrainingProgramResponse,
)
def get_training_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = TrainingService(db)

    program = service.get_program(program_id)

    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training program not found",
        )

    return program


@router.post(
    "/sessions",
    response_model=TrainingSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def schedule_training_session(
    session_data: TrainingSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = TrainingService(db)

    try:
        return service.schedule_session(
            program_id=session_data.program_id,
            faculty_id=session_data.faculty_id,
            batch_id=session_data.batch_id,
            group_id=session_data.group_id,
            title=session_data.title,
            start_at=session_data.start_at,
            end_at=session_data.end_at,
            hours=session_data.hours,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/sessions",
    response_model=list[TrainingSessionResponse],
)
def get_training_sessions(
    program_id: int | None = None,
    batch_id: int | None = None,
    group_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = TrainingService(db)

    return service.get_sessions(
        program_id=program_id,
        batch_id=batch_id,
        group_id=group_id,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=TrainingSessionResponse,
)
def get_training_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = TrainingService(db)

    session = service.get_session(session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training session not found",
        )

    return session


@router.get(
    "/programs/{program_id}/completion",
)
def get_training_completion(
    program_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = TrainingService(db)

    try:
        return service.calculate_completion(program_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )