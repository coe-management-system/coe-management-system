from datetime import datetime
from pydantic import BaseModel


class ImportCreateResponse(BaseModel):
    import_id: int
    filename: str
    status: str
    file_hash: str


class ImportSummary(BaseModel):
    total_rows: int
    valid: int
    invalid: int
    reference_errors: int
    existing: int
    duplicates: int
    ready_to_commit: int


class ImportDetailResponse(BaseModel):
    import_id: int
    filename: str
    status: str
    created_by: int | None
    created_at: datetime
    completed_at: datetime | None
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    error_message: str | None


class ValidateImportResponse(BaseModel):
    import_id: int
    status: str
    mapping: dict
    unmapped_columns: list[str]
    ambiguous_columns: list[dict] = []
    column_status: list[dict] = []
    summary: ImportSummary
    records: list[dict]
    # Attendance-specific fields (populated for import_type="attendance")
    format: str | None = None
    detected_type: str | None = None
    reason: str | None = None
    subject: str | None = None
    subject_source: str | None = None
    issues: list[dict] = []
    duplicates: list[dict] = []


class CommitImportResponse(BaseModel):
    import_id: int
    status: str
    imported_count: int = 0
    imported_students: list = []
    # Attendance-specific fields (populated for import_type="attendance")
    inserted: int = 0
    updated: int = 0
    overwritten: list[dict] = []
    valid_events: int = 0
    existing_events: int = 0
    excluded_events: int = 0
    below_threshold_count: int = 0
    below_threshold_threshold: float = 75.0
    below_threshold: list[dict] = []