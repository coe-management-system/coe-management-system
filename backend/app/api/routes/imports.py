from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User
from app.schemas.import_schema import ImportResponse
from app.services.import_service import ImportService


router = APIRouter(
    prefix="/imports",
    tags=["Imports"],
)

faculty_required = require_role("faculty")


@router.post(
    "",
    response_model=ImportResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_student_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(faculty_required),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in {".xlsx", ".xls"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only Excel files (.xlsx, .xls) are supported",
        )

    temporary_path = None

    try:
        with NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name

            while chunk := file.file.read(1024 * 1024):
                temporary_file.write(chunk)

        return ImportService.process_student_file(
            db=db,
            file_path=temporary_path,
            filename=file.filename,
            created_by=current_user.id,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process uploaded Excel file",
        ) from exc

    finally:
        file.file.close()