from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User
from app.schemas.attendance import (
    AttendanceBulkCreate,
    AttendanceCreate,
    AttendanceOverviewItem,
    AttendanceResponse,
    AttendanceSummary,
)
from app.services.attendance_service import AttendanceService


router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
)

faculty_required = require_role("faculty")


@router.post(
    "",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def record_attendance(
    attendance_data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = AttendanceService(db)

    try:
        return service.record(
            student_id=attendance_data.student_id,
            subject_id=attendance_data.subject_id,
            session_date=attendance_data.session_date,
            status=attendance_data.status,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.post(
    "/bulk",
    response_model=list[AttendanceResponse],
    status_code=status.HTTP_201_CREATED,
)
def bulk_record_attendance(
    attendance_data: AttendanceBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = AttendanceService(db)

    try:
        records = [
            {
                "student_id": record.student_id,
                "status": record.status,
            }
            for record in attendance_data.records
        ]

        return service.bulk_record(
            subject_id=attendance_data.subject_id,
            session_date=attendance_data.session_date,
            records=records,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get(
    "/overview",
    response_model=list[AttendanceOverviewItem],
)
def get_attendance_overview(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = AttendanceService(db)

    return service.get_overview(limit=limit)


@router.get(
    "/summary",
    response_model=AttendanceSummary,
)
def get_attendance_summary(
    student_id: int,
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    service = AttendanceService(db)

    return service.get_summary(
        student_id=student_id,
        subject_id=subject_id,
    )