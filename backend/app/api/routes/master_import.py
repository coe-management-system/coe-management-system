from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User

from app.excel.workbook_import.reader import read_workbook, WorkbookReadError
from app.excel.workbook_import.planner import build_workbook_plan, WorkbookPlanningError
from app.excel.workbook_import.master_resolver import resolve_master_workbook
from app.excel.workbook_import.attendance_resolver import resolve_attendance
from app.excel.workbook_import.commit import commit_workbook, WorkbookCommitError

router = APIRouter(
    prefix="/master-imports",
    tags=["Master Imports"],
)

faculty_required = require_role("faculty")

ALLOWED_EXTENSIONS = {".xlsx", ".xls"}
ALLOWED_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/octet-stream",
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def _save_upload_to_temp(file: UploadFile) -> str:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are supported",
        )

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported content type: {file.content_type}",
        )

    temporary_path = None
    total_size = 0
    with NamedTemporaryFile(suffix=extension, delete=False) as temporary_file:
        temporary_path = temporary_file.name
        while chunk := file.file.read(1024 * 1024):
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE_BYTES:
                Path(temporary_path).unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB",
                )
            temporary_file.write(chunk)

    if total_size == 0:
        Path(temporary_path).unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty")

    return temporary_path


def _build_resolution_plan(temporary_path: str, db: Session):
    try:
        workbook = read_workbook(temporary_path)
    except WorkbookReadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        workbook_plan = build_workbook_plan(workbook)
    except WorkbookPlanningError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    plan = resolve_master_workbook(db, workbook_plan)
    resolve_attendance(workbook_plan, plan)
    return plan


def _summarize_plan(plan) -> dict:
    return {
        "departments": {"existing": len(plan.departments) - len(plan.new_departments), "new": len(plan.new_departments)},
        "batches": {"existing": len(plan.batches) - len(plan.new_batches), "new": len(plan.new_batches)},
        "groups": {"existing": len(plan.groups) - len(plan.new_groups), "new": len(plan.new_groups)},
        "students": {"existing": len(plan.students) - len(plan.new_students), "new": len(plan.new_students)},
        "subjects": {"existing": len(plan.subjects) - len(plan.new_subjects), "new": len(plan.new_subjects)},
        "attendance": {"existing": len(plan.attendance) - len(plan.new_attendance), "new": len(plan.new_attendance)},
        "errors": plan.errors,
    }


@router.post("/preview")
def preview_master_workbook(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """
    Upload and resolve a master workbook (Departments/Batches/Groups/
    Students/Subjects) against the existing database WITHOUT writing
    anything. This is read-only, per resolve_master_workbook's contract.
    """
    temporary_path = _save_upload_to_temp(file)
    try:
        plan = _build_resolution_plan(temporary_path, db)
        return _summarize_plan(plan)
    finally:
        Path(temporary_path).unlink(missing_ok=True)


@router.post("/commit")
def commit_master_workbook(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    """
    Re-resolve the same workbook and commit it in one transaction.
    The caller must have already reviewed a /preview response for this
    same file and confirmed it is correct before calling this endpoint -
    there is no server-side preview state to "approve" against, so the
    client is responsible for only calling /commit after user confirmation.
    """
    temporary_path = _save_upload_to_temp(file)
    try:
        plan = _build_resolution_plan(temporary_path, db)
        if plan.errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Cannot commit: workbook has unresolved errors", "errors": plan.errors},
            )
        try:
            result = commit_workbook(db, plan)
        except WorkbookCommitError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return result
    finally:
        Path(temporary_path).unlink(missing_ok=True)
